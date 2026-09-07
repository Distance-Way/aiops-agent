from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app import api, db
from app.agent import AgentEngine
from app.config import settings
from app.logging_config import get_logger, setup_logging
from app.metrics import (
    AIOPS_DIAGNOSTIC_JOBS_QUEUED,
    AIOPS_DIAGNOSTIC_JOBS_RUNNING,
    AIOPS_WORKERS_ACTIVE,
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_TOTAL,
)
from app.rag import RagService


db.init_db()
setup_logging(settings.log_file_path)
logger = get_logger()


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("service started", extra={"provider": settings.llm_provider})
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AIOps Agent：智能运维诊断与监控服务",
        lifespan=lifespan,
    )
    application.state.settings = settings
    rag = RagService()
    application.state.rag = rag
    application.state.agent = AgentEngine(rag=rag)
    application.include_router(api.router)

    @application.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            status_code = 500
            duration_ms = round((perf_counter() - started) * 1000, 2)
            HTTP_REQUESTS_TOTAL.labels(request.method, request.url.path, str(status_code)).inc()
            logger.error(
                "http request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": duration_ms,
                },
            )
            raise
        duration = max(perf_counter() - started, 0)
        duration_ms = round(duration * 1000, 2)
        HTTP_REQUESTS_TOTAL.labels(
            request.method, request.url.path, str(response.status_code)
        ).inc()
        HTTP_REQUEST_DURATION.labels(request.method, request.url.path).observe(duration)
        logger.info(
            "http request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @application.get("/healthz", tags=["system"])
    def healthz():
        return {"status": "ok", "service": settings.app_name}

    @application.get("/metrics", tags=["system"])
    def metrics():
        AIOPS_WORKERS_ACTIVE.set(db.count_active_workers())
        AIOPS_DIAGNOSTIC_JOBS_QUEUED.set(db.count_diagnostic_jobs("queued"))
        AIOPS_DIAGNOSTIC_JOBS_RUNNING.set(db.count_diagnostic_jobs("running"))
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    web_dir = Path(__file__).resolve().parent.parent / "web"
    if web_dir.exists():
        application.mount("/ui", StaticFiles(directory=web_dir, html=True), name="ui")

    @application.get("/", include_in_schema=False)
    def index():
        index_file = web_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return RedirectResponse("/docs")

    return application


app = create_app()
