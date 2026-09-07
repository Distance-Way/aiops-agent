import json

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app import db, scheduling
from app.metrics import AIOPS_DIAGNOSTIC_JOB_COMPLETIONS_TOTAL
from app.rag import RagService
from app.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentOut,
    JobComplete,
    JobCreate,
    JobOut,
    MessageOut,
    SearchRequest,
    SearchResponse,
    SessionCreate,
    SessionOut,
    ToolInfo,
    WorkerOut,
    WorkerRegister,
)
from app.security import require_api_key


router = APIRouter(prefix="/api", dependencies=[Depends(require_api_key)])


def _job_out(row) -> dict:
    data = dict(row)
    data["payload"] = json.loads(data["payload"])
    return data


@router.post("/workers", response_model=WorkerOut, status_code=status.HTTP_201_CREATED)
def register_worker(payload: WorkerRegister):
    row = db.register_worker(
        name=payload.name,
        cpu_capacity=payload.cpu_capacity,
        memory_capacity_mb=payload.memory_capacity_mb,
    )
    return dict(row)


@router.post("/workers/{worker_id}/heartbeat", response_model=WorkerOut)
def worker_heartbeat(worker_id: str):
    if not db.get_worker(worker_id):
        raise HTTPException(status_code=404, detail="Worker 不存在")
    db.touch_worker_heartbeat(worker_id)
    return dict(db.get_worker(worker_id))


@router.post("/workers/{worker_id}/claim", response_model=JobOut | None)
def worker_claim(worker_id: str):
    if not db.get_worker(worker_id):
        raise HTTPException(status_code=404, detail="Worker 不存在")
    job = scheduling.claim_next_job(worker_id)
    return _job_out(job) if job else None


@router.post("/workers/{worker_id}/complete", response_model=JobOut)
def worker_complete(worker_id: str, payload: JobComplete):
    job = db.get_job(payload.job_id)
    if not job or job["worker_id"] != worker_id:
        raise HTTPException(status_code=404, detail="Diagnostic Job 不存在")
    if not db.complete_job(
        job_id=payload.job_id,
        worker_id=worker_id,
        status=payload.status,
        result=payload.result,
        error=payload.error,
    ):
        raise HTTPException(status_code=409, detail="Diagnostic Job 当前不可完成")
    AIOPS_DIAGNOSTIC_JOB_COMPLETIONS_TOTAL.labels(payload.status).inc()
    return _job_out(db.get_job(payload.job_id))


@router.get("/workers", response_model=list[WorkerOut])
def workers():
    return [dict(row) for row in db.list_workers()]


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate):
    row = db.create_job(
        job_type=payload.type,
        priority=payload.priority,
        cpu_request=payload.cpu_request,
        memory_request_mb=payload.memory_request_mb,
        payload=payload.payload,
    )
    return _job_out(row)


@router.get("/jobs", response_model=list[JobOut])
def jobs():
    return [_job_out(row) for row in db.list_jobs()]


@router.get("/jobs/{job_id}", response_model=JobOut)
def job_detail(job_id: str):
    row = db.get_job(job_id)
    if not row:
        raise HTTPException(status_code=404, detail="Diagnostic Job 不存在")
    return _job_out(row)


@router.get("/healthz", include_in_schema=False)
async def healthz(request: Request):
    return {"status": "ok", "service": request.app.state.settings.app_name}


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate):
    row = db.create_session(payload.title)
    return {
        "id": row["id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "message_count": 0,
    }


@router.get("/sessions", response_model=list[SessionOut])
def sessions():
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "message_count": row["message_count"],
        }
        for row in db.list_sessions()
    ]


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
def session_messages(session_id: str):
    if not db.get_session(session_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    return [dict(row) for row in db.get_messages(session_id)]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str):
    if not db.delete_session(session_id):
        raise HTTPException(status_code=404, detail="会话不存在")


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request):
    agent = request.app.state.agent
    return await agent.run(
        session_id=payload.session_id,
        message=payload.message,
        use_rag=payload.use_rag,
        top_k=payload.top_k,
    )


@router.get("/tools", response_model=list[ToolInfo])
def tools(request: Request):
    return request.app.state.agent.tools.tool_list()


@router.get("/status")
def system_status():
    from app.monitoring import get_system_status

    return get_system_status()


@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(request: Request, file: UploadFile = File(...)):
    name = file.filename or "runbook.md"
    suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if suffix not in {"md", "txt", "markdown"}:
        raise HTTPException(
            status_code=415, detail="仅支持 Markdown/TXT 排障手册"
        )
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件过大，最大支持 2MB")
    text = content.decode("utf-8", errors="replace")
    if not text.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")
    rag: RagService = request.app.state.rag
    document = rag.ingest_document(name=name, content=text)
    return {
        "id": document.id,
        "name": document.name,
        "size": document.size,
        "chunk_count": document.chunk_count,
        "created_at": document.created_at,
    }


@router.get("/documents", response_model=list[DocumentOut])
def documents():
    return [dict(row) for row in db.list_documents()]


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(document_id: str):
    if not db.delete_document(document_id):
        raise HTTPException(status_code=404, detail="文档不存在")


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, request: Request):
    rag: RagService = request.app.state.rag
    return SearchResponse(query=payload.query, hits=rag.search(payload.query, payload.top_k))
