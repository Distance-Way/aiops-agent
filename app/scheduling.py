from datetime import datetime, timezone

from app import db
from app.config import settings


def worker_is_fresh(worker) -> bool:
    if worker is None or worker["status"] != "active":
        return False
    try:
        last_heartbeat = datetime.fromisoformat(worker["last_heartbeat_at"])
    except ValueError:
        return False
    if last_heartbeat.tzinfo is None:
        last_heartbeat = last_heartbeat.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - last_heartbeat).total_seconds()
    return age <= settings.worker_ttl_seconds


def claim_next_job(worker_id: str):
    worker = db.get_worker(worker_id)
    if not worker_is_fresh(worker):
        return None

    used_cpu, used_memory_mb = db.worker_used_capacity(worker_id)
    available_cpu = worker["cpu_capacity"] - used_cpu
    available_memory_mb = worker["memory_capacity_mb"] - used_memory_mb

    for job in db.list_queued_jobs():
        if (
            job["cpu_request"] <= available_cpu
            and job["memory_request_mb"] <= available_memory_mb
        ):
            if db.claim_job(job["id"], worker_id, db.utc_now()):
                return db.get_job(job["id"])
    return None
