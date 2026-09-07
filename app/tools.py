import asyncio
import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.config import settings
from app.monitoring import get_system_status
from app.rag import RagService


@dataclass
class ToolExecution:
    output: str
    sources: list[str]


ToolHandler = Callable[..., str]


def _truncate(text: str, limit: int | None = None) -> str:
    max_length = limit or settings.tool_output_limit
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n...[输出过长，已截断，共 {len(text)} 字符]"


def _get_current_time() -> str:
    now = datetime.now(timezone.utc).astimezone()
    return f"当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}（{now.tzname()}）"


def _get_system_status() -> str:
    status = get_system_status()
    return json.dumps(status, ensure_ascii=False)


def _check_service(port: int | None = None) -> str:
    target_port = port or 8000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        result = sock.connect_ex(("127.0.0.1", target_port))
        if result == 0:
            return f"端口 {target_port} 正在监听，服务健康检查通过"
        return f"端口 {target_port} 未监听，服务可能未启动或端口不通"
    except OSError as exc:
        return f"端口检查失败：{exc}"
    finally:
        sock.close()


def _query_logs(
    keyword: str = "ERROR", max_lines: int = 20, since_minutes: int = 60
) -> str:
    path = Path(settings.log_file_path)
    if not path.exists():
        return f"日志文件不存在：{path}"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = lines[-max(1000, max_lines * 50) :]
    matches = [line for line in lines if keyword.lower() in line.lower()]
    matches = matches[-max_lines:]
    if not matches:
        return f"最近 {since_minutes} 分钟内未找到包含 {keyword!r} 的日志"
    body = "\n".join(matches)
    return f"共找到 {len(matches)} 条匹配日志：\n{body}"


def _search_runbook(query: str, rag: RagService, top_k: int = 3) -> str:
    hits = rag.search(query, top_k=top_k)
    if not hits:
        return "知识库中暂无排障手册，请先上传 Markdown/TXT 文档"
    parts = [
        f"[{index}] 来源：{hit.document_name}（相似度 {hit.score}）\n{hit.content}"
        for index, hit in enumerate(hits, start=1)
    ]
    return "\n\n".join(parts)


class ToolRegistry:
    def __init__(self, rag: RagService | None = None):
        self._rag = rag
        self._tools: dict[str, dict[str, Any]] = {}
        self.register(
            name="get_current_time",
            description="获取服务器当前日期与时间",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            handler=_get_current_time,
        )
        self.register(
            name="get_system_status",
            description="查看服务器 CPU、内存、磁盘、进程与 GPU 状态",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            handler=_get_system_status,
        )
        self.register(
            name="check_service",
            description="检查本地服务端口是否监听",
            parameters={
                "type": "object",
                "properties": {"port": {"type": "integer", "description": "端口号"}},
                "required": [],
            },
            handler=_check_service,
        )
        self.register(
            name="query_logs",
            description="检索服务日志，按关键字返回最近匹配片段",
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "检索关键字，如 ERROR"},
                    "max_lines": {"type": "integer", "description": "最多返回行数"},
                    "since_minutes": {"type": "integer", "description": "最近多少分钟"},
                },
                "required": ["keyword"],
            },
            handler=_query_logs,
        )
        if rag is not None:
            self.register(
                name="search_runbook",
                description="检索排障手册知识库，返回处置步骤与来源",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "故障描述或检索问题"},
                        "top_k": {"type": "integer", "description": "返回片段数量"},
                    },
                    "required": ["query"],
                },
                handler=lambda **kwargs: _search_runbook(
                    query=kwargs.get("query", ""),
                    rag=self._rag,
                    top_k=int(kwargs.get("top_k") or 3),
                ),
            )

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        self._tools[name] = {
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }

    def schemas(self, include_rag: bool = True) -> list[dict[str, Any]]:
        result = []
        for name, spec in self._tools.items():
            if name == "search_runbook" and not include_rag:
                continue
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": spec["description"],
                        "parameters": spec["parameters"],
                    },
                }
            )
        return result

    def tool_list(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "description": spec["description"],
                "parameters": spec["parameters"],
            }
            for name, spec in self._tools.items()
        ]

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolExecution:
        spec = self._tools.get(name)
        if not spec:
            return ToolExecution(output=f"未注册工具：{name}", sources=[])
        handler: ToolHandler = spec["handler"]
        try:
            output = await asyncio.wait_for(
                asyncio.to_thread(handler, **arguments),
                timeout=settings.tool_timeout_seconds,
            )
            sources: list[str] = []
            if name == "search_runbook" and self._rag is not None:
                query = str(arguments.get("query") or "")
                sources = [
                    hit.document_name
                    for hit in self._rag.search(query, top_k=int(arguments.get("top_k") or 3))
                ]
            return ToolExecution(output=_truncate(output), sources=list(dict.fromkeys(sources)))
        except asyncio.TimeoutError:
            return ToolExecution(
                output=f"工具执行超时（超过 {settings.tool_timeout_seconds:.1f} 秒）",
                sources=[],
            )
        except Exception as exc:  # pragma: no cover - defensive boundary
            return ToolExecution(output=f"工具执行失败：{exc}", sources=[])
