import asyncio

from app.agent import MockLLM


def test_mock_llm_returns_system_tool_call():
    llm = MockLLM()
    result = asyncio.run(llm.chat(
        messages=[
            {"role": "system", "content": "system"},
            {"role": "user", "content": "查看服务器状态"},
        ],
        tools=[
            {
                "type": "function",
                "function": {"name": "get_system_status", "parameters": {}},
            }
        ],
    ))
    assert result.tool_calls
    assert result.tool_calls[0].name == "get_system_status"


def test_mock_llm_summarizes_tool_result():
    llm = MockLLM()
    result = asyncio.run(llm.chat(
        messages=[
            {"role": "user", "content": "查看服务器状态"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "get_system_status", "arguments": "{}"},
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "CPU 23%"},
        ],
        tools=[],
    ))
    assert result.content
    assert "CPU 23%" in result.content
