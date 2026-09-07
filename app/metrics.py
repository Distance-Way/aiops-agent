from prometheus_client import Counter, Gauge, Histogram


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

AIOPS_WORKERS_ACTIVE = Gauge(
    "aiops_workers_active",
    "Workers currently registered as active",
)
AIOPS_DIAGNOSTIC_JOBS_QUEUED = Gauge(
    "aiops_diagnostic_jobs_queued",
    "Diagnostic jobs currently queued",
)
AIOPS_DIAGNOSTIC_JOBS_RUNNING = Gauge(
    "aiops_diagnostic_jobs_running",
    "Diagnostic jobs currently running",
)
AIOPS_DIAGNOSTIC_JOB_COMPLETIONS_TOTAL = Counter(
    "aiops_diagnostic_job_completions_total",
    "Diagnostic jobs completed",
    ["status"],
)
