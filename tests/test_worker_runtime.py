import json

from app.worker import WorkerRuntime, execute_diagnostic_job


class FakeClient:
    def __init__(self, claimed_job=None):
        self.claimed_job = claimed_job
        self.completed = None

    def claim(self, worker_id):
        return self.claimed_job

    def complete(self, worker_id, job_id, status, result=None, error=None):
        self.completed = {
            "worker_id": worker_id,
            "job_id": job_id,
            "status": status,
            "result": result,
            "error": error,
        }


def test_log_inference_job_classifies_known_log():
    result = execute_diagnostic_job(
        {"id": "j_1", "type": "log_inference", "payload": {"text": "disk full"}}
    )
    payload = json.loads(result)
    assert payload["label"] == "disk"
    assert payload["confidence"] > 0.8


def test_worker_runtime_completes_succeeded_job():
    client = FakeClient(
        claimed_job={
            "id": "j_2",
            "type": "log_inference",
            "payload": {"text": "connection timeout"},
        }
    )
    WorkerRuntime(client=client, worker_id="w_1").work_once()

    assert client.completed["job_id"] == "j_2"
    assert client.completed["status"] == "succeeded"
    assert "network" in client.completed["result"]


def test_worker_runtime_reports_failed_job():
    client = FakeClient(claimed_job={"id": "j_3", "type": "unknown", "payload": {}})
    WorkerRuntime(client=client, worker_id="w_1").work_once()

    assert client.completed["status"] == "failed"
    assert "不支持" in client.completed["error"]
