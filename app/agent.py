import json
import re
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

import httpx

from app import db
from app.config import settings
from app.rag import RagService
from app.schemas import ChatResponse, ToolCallResult
from app.tools import ToolRegistry


SYSTEM_PROMPT = (
    "你是 AIOps Agent，一个面向服务器与日志排障场景的智能运维助手。"
    "当用户询问系统状态、日志、服务端口或排障手册时，优先调用可用工具获取事实，"
    "再根据工具结果给出简洁、可执行的中文回答。若工具结果不足，请如实说明，不要编造。"
)


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMResult:
    content: str | None
    tool_calls: list[ToolCall]
    model: str
    provider: str


class MockLLM:
    """Deterministic local LLM used to run the full flow without an API key."""

    model = "mock-llm"
    provider = "mock"

    async def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMResult:
        if messages and messages[-1].get("role") == "tool":
            output = messages[-1].get("content", "")
            return LLMResult(
                content=f"好的，工具执行结果如下：\n{output}",
                tool_calls=[],
                model=self.model,
                provider=self.provider,
            )

        user_text = self._last_user_text(messages)
        available = {
            tool["function"]["name"] for tool in tools if tool.get("function")
        }

        if "日志" in user_text and "query_logs" in available:
            return self._tool_result(
                "query_logs", {"keyword": "ERROR", "max_lines": 20}
            )

        runbook_hints = ("手册", "知识库", "排障", "怎么处理", "如何处理", "处置")
        if any(hint in user_text for hint in runbook_hints) and "search_runbook" in available:
            return self._tool_result(
                "search_runbook", {"query": user_text, "top_k": 3}
            )

        system_hints = ("系统状态", "服务器状态", "cpu", "内存", "磁盘", "负载", "运行状态")
        if any(hint in user_text.lower() for hint in system_hints) and "get_system_status" in available:
            return self._tool_result("get_system_status", {})

        if ("服务" in user_text or "端口" in user_text) and "check_service" in available:
            match = re.search(r"(\d{2,5})", user_text)
            return self._tool_result("check_service", {"port": int(match.group(1)) if match else 8000})

        if any(keyword in user_text for keyword in ("几点", "当前时间", "现在时间")) and "get_current_time" in available:
            return self._tool_result("get_current_time", {})

        return LLMResult(
            content=(
                "你好，我是 AIOps Agent。你可以让我查看服务器状态、检索错误日志、"
                "检查服务端口，或根据排障手册回答故障处理问题。"
            ),
            tool_calls=[],
            model=self.model,
            provider=self.provider,
        )

    def _tool_result(self, name: str, arguments: dict[str, Any]) -> LLMResult:
        return LLMResult(
            content=None,
            tool_calls=[ToolCall(name=name, arguments=arguments)],
            model=self.model,
            provider=self.provider,
        )

    @staticmethod
    def _last_user_text(messages: list[dict[str, Any]]) -> str:
        for message in reversed(messages):
            if message.get("role") == "user":
                return str(message.get("content", ""))
        return ""


class OpenAICompatibleLLM:
    """OpenAI-compatible chat completions client."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.provider = "openai"

    async def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        message = data["choices"][0]["message"]
        content = message.get("content")
        tool_calls: list[ToolCall] = []
        for item in message.get("tool_calls") or []:
            function = item.get("function") or {}
            raw_arguments = function.get("arguments") or "{}"
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                arguments = {}
            tool_calls.append(
                ToolCall(
                    name=function.get("name", ""),
                    arguments=arguments,
                )
            )
        return LLMResult(
            content=content,
            tool_calls=tool_calls,
            model=self.model,
            provider=self.provider,
        )


def build_llm() -> MockLLM | OpenAICompatibleLLM:
    if settings.llm_provider == "openai" and settings.llm_api_key:
        return OpenAICompatibleLLM(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    return MockLLM()


class AgentEngine:
    def __init__(self, rag: RagService | None = None):
        self.rag = rag or RagService()
        self.llm = build_llm()
        self.tools = ToolRegistry(rag=self.rag)

    async def run(
        self,
        session_id: str | None,
        message: str,
        use_rag: bool = True,
        top_k: int = 3,
    ) -> ChatResponse:
        started = perf_counter()
        session = db.get_or_create_session(session_id)
        sid = session["id"]
        history_rows = db.get_messages(sid)
        history = [
            {"role": row["role"], "content": row["content"]}
            for row in history_rows[-settings.history_limit * 2 :]
        ]
        db.add_message(sid, "user", message)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": message},
        ]
        schemas = self.tools.schemas(include_rag=use_rag)
        events: list[ToolCallResult] = []
        sources: list[str] = []
        final_reply: str | None = None

        for step in range(settings.max_tool_steps):
            try:
                result = await self.llm.chat(messages, schemas)
            except Exception as exc:
                final_reply = f"模型调用失败：{exc}"
                break

            if not result.tool_calls:
                final_reply = result.content or "未生成回答，请换一种方式描述问题。"
                break

            assistant_message: dict[str, Any] = {
                "role": "assistant",
                "content": None,
                "tool_calls": [],
            }
            prepared: list[tuple[str, ToolCall]] = []
            for index, call in enumerate(result.tool_calls):
                call_id = f"call_{step}_{index}_{call.name}"
                arguments = dict(call.arguments)
                if call.name == "search_runbook" and "top_k" not in arguments:
                    arguments["top_k"] = top_k
                assistant_message["tool_calls"].append(
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(arguments, ensure_ascii=False),
                        },
                    }
                )
                prepared.append((call_id, ToolCall(call.name, arguments)))
            messages.append(assistant_message)

            for call_id, call in prepared:
                tool_started = perf_counter()
                execution = await self.tools.execute(call.name, call.arguments)
                duration_ms = round((perf_counter() - tool_started) * 1000, 2)
                status = "success" if not execution.output.startswith("工具执行失败") else "error"
                db.add_tool_run(
                    session_id=sid,
                    name=call.name,
                    arguments=call.arguments,
                    output=execution.output,
                    status=status,
                    duration_ms=duration_ms,
                )
                events.append(
                    ToolCallResult(
                        name=call.name,
                        arguments=call.arguments,
                        output=execution.output,
                        status=status,
                        duration_ms=duration_ms,
                    )
                )
                sources.extend(execution.sources)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": execution.output,
                    }
                )

        if final_reply is None:
            final_reply = (
                f"已执行 {len(events)} 次工具调用但仍未得到结论，"
                "请缩小问题范围或补充更具体的错误信息。"
            )
        db.add_message(sid, "assistant", final_reply)
        return ChatResponse(
            session_id=sid,
            reply=final_reply,
            tools_executed=events,
            sources=list(dict.fromkeys(sources)),
            provider=getattr(self.llm, "provider", "mock"),
            model=getattr(self.llm, "model", "mock"),
            latency_ms=round((perf_counter() - started) * 1000, 2),
        )
