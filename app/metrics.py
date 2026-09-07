from prometheus_client import Counter, Histogram


HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "HTTP requests processed",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)
AGENT_TOOL_CALLS_TOTAL = Counter(
    "agent_tool_calls_total",
    "Agent tool calls executed",
    ["tool", "status"],
)
AGENT_LOOP_STEPS_TOTAL = Counter(
    "agent_loop_steps_total",
    "Agent reasoning loop steps",
)
AI_CHAT_REQUESTS_TOTAL = Counter(
    "ai_chat_requests_total",
    "Chat requests handled by the agent",
)
