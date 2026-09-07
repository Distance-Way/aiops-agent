from typing import Any, Literal

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: str = Field(default="新会话", max_length=80)


class SessionOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=64)
    use_rag: bool = True
    top_k: int = Field(default=3, ge=1, le=10)


class ToolCallResult(BaseModel):
    name: str
    arguments: dict[str, Any]
    output: str
    status: str
    duration_ms: float


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tools_executed: list[ToolCallResult]
    sources: list[str]
    provider: str
    model: str
    latency_ms: float


class DocumentOut(BaseModel):
    id: str
    name: str
    size: int
    chunk_count: int
    created_at: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)


class SearchHit(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    position: int
    content: str
    score: float


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]


class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class WorkerRegister(BaseModel):
    name: str = Field(default="worker", max_length=80)
    cpu_capacity: float = Field(gt=0, le=1024)
    memory_capacity_mb: int = Field(gt=0, le=1024 * 1024)


class WorkerOut(BaseModel):
    id: str
    name: str
    status: str
    cpu_capacity: float
    memory_capacity_mb: int
    last_heartbeat_at: str
    created_at: str


class JobCreate(BaseModel):
    type: Literal["system_status", "service_check", "query_logs", "log_inference"]
    priority: Literal["high", "normal", "low"] = "normal"
    cpu_request: float = Field(default=1.0, gt=0, le=1024)
    memory_request_mb: int = Field(default=128, gt=0, le=1024 * 1024)
    payload: dict[str, Any] = Field(default_factory=dict)


class JobOut(BaseModel):
    id: str
    type: str
    status: str
    priority: str
    cpu_request: float
    memory_request_mb: int
    payload: dict[str, Any]
    worker_id: str | None = None
    result: str | None = None
    error: str | None = None
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
