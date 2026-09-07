import asyncio

from app.schemas import SearchHit
from app.tools import ToolRegistry


def _run(coro):
    return asyncio.run(coro)


def test_execute_rejects_unregistered_tool():
    registry = ToolRegistry()
    result = _run(registry.execute("rm_rf", {}))

    assert result.status == "error"
    assert "未注册工具" in result.output


def test_execute_rejects_unknown_arguments():
    registry = ToolRegistry()
    result = _run(registry.execute("get_system_status", {"command": "reboot"}))

    assert result.status == "error"
    assert "参数校验失败" in result.output
    assert "command" in result.output


def test_execute_rejects_invalid_argument_types():
    registry = ToolRegistry()
    result = _run(
        registry.execute("query_logs", {"keyword": 123, "max_lines": "oops"})
    )

    assert result.status == "error"
    assert "keyword 必须是 string" in result.output


def test_handler_error_is_reported_as_error():
    registry = ToolRegistry()

    def broken_handler():
        raise ValueError("disk check failed")

    registry.register(
        "broken_tool",
        "always fails",
        {"type": "object", "properties": {}, "required": []},
        broken_handler,
    )

    result = _run(registry.execute("broken_tool", {}))

    assert result.status == "error"
    assert result.output.startswith("工具执行失败")


def test_execute_truncates_long_output():
    registry = ToolRegistry()

    def long_output():
        return "x" * 3000

    registry.register(
        "long_output",
        "returns a long string",
        {"type": "object", "properties": {}, "required": []},
        long_output,
    )

    result = _run(registry.execute("long_output", {}))

    assert result.status == "success"
    assert len(result.output) < 3000
    assert "输出过长" in result.output


def test_search_runbook_searches_once_and_reports_sources():
    class FakeRag:
        def __init__(self):
            self.calls = 0

        def search(self, query, top_k=3):
            self.calls += 1
            return [
                SearchHit(
                    chunk_id="chunk-1",
                    document_id="doc-1",
                    document_name="disk-manual.md",
                    position=0,
                    content="执行 df -h 确认分区使用率",
                    score=0.91,
                )
            ]

    rag = FakeRag()
    registry = ToolRegistry(rag=rag)
    result = _run(
        registry.execute(
            "search_runbook", {"query": "磁盘满了怎么处理", "top_k": 2}
        )
    )

    assert rag.calls == 1
    assert result.status == "success"
    assert result.sources == ["disk-manual.md"]
    assert "df -h" in result.output
