import json
import time

import httpx

from app.config import settings
from app.local_model import classify_log
from app.monitoring import get_system_status
from app.tools import _check_service, _query_logs


def execute_diagnostic_job(job: dict) -> str:
    job_type = job.get("type")
    payload = job.get("payload") or {}
    if job_type == "system_status":
        return json.dumps(get_system_status(), ensure_ascii=False)
    if job_type == "service_check":
        return _check_service(port=payload.get("port"))
    if job_type == "query_logs":
        return _query_logs(
            keyword=payload.get("keyword", "ERROR"),
            max_lines=int(payload.get("max_lines") or 20),
            since_minutes=int(payload.get("since_minutes") or 60),
        )
    if job_type == "log_inference":
        return json.dumps(classify_log(payload.get("text", "")), ensure_ascii=False)
    raise ValueError(f"不支持的任务类型：{job_type}")


class ControlPlaneClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 10.0,
    ):
        self.base_url = (base_url or settings.control_plane_url).rstrip("/")
        self.api_key = api_key or settings.api_key
        self._client = httpx.Client(timeout=timeout)

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key}

    def register(
        self, name: str, cpu_capacity: float, memory_capacity_mb: int
    ) -> str:
        response = self._client.post(
            f"{self.base_url}/api/workers",
            headers=self._headers(),
            json={
                "name": name,
                "cpu_capacity": cpu_capacity,
                "memory_capacity_mb": memory_capacity_mb,
            },
        )
        response.raise_for_status()
        return response.json()["id"]

    def heartbeat(self, worker_id: str) -> None:
        response = self._client.post(
            f"{self.base_url}/api/workers/{worker_id}/heartbeat",
            headers=self._headers(),
        )
        response.raise_for_status()

    def claim(self, worker_id: str) -> dict | None:
        response = self._client.post(
            f"{self.base_url}/api/workers/{worker_id}/claim",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def complete(
        self,
        worker_id: str,
        job_id: str,
        status: str,
        result: str | None = None,
        error: str | None = None,
    ) -> None:
        response = self._client.post(
            f"{self.base_url}/api/workers/{worker_id}/complete",
            headers=self._headers(),
            json={
                "job_id": job_id,
                "status": status,
                "result": result,
                "error": error,
            },
        )
        response.raise_for_status()


class WorkerRuntime:
    def __init__(
        self,
        client: ControlPlaneClient,
        worker_id: str,
        executor=execute_diagnostic_job,
    ):
        self.client = client
        self.worker_id = worker_id
        self.executor = executor

    def work_once(self) -> bool:
        job = self.client.claim(self.worker_id)
        if not job:
            return False
        try:
            result = self.executor(job)
        except Exception as exc:
            self.client.complete(
                self.worker_id,
                job["id"],
                "failed",
                error=str(exc),
            )
            return True
        self.client.complete(self.worker_id, job["id"], "succeeded", result=result)
        return True


def main() -> None:
    client = ControlPlaneClient()
    worker_id = client.register(
        name=settings.worker_name,
        cpu_capacity=settings.worker_cpu_capacity,
        memory_capacity_mb=settings.worker_memory_mb,
    )
    runtime = WorkerRuntime(client=client, worker_id=worker_id)
    last_heartbeat = 0.0
    while True:
        if time.monotonic() - last_heartbeat >= settings.worker_heartbeat_interval_seconds:
            client.heartbeat(worker_id)
            last_heartbeat = time.monotonic()
        runtime.work_once()
        time.sleep(settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    main()
