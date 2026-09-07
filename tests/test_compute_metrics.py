def _register_worker(client, headers):
    response = client.post(
        "/api/workers",
        json={
            "name": "worker-metrics",
            "cpu_capacity": 2.0,
            "memory_capacity_mb": 2048,
        },
        headers=headers,
    )
    return response.json()["id"]


def test_metrics_expose_workers_and_queued_jobs(client, headers):
    worker_id = _register_worker(client, headers)
    client.post(
        "/api/jobs",
        json={
            "type": "system_status",
            "priority": "normal",
            "cpu_request": 1.0,
            "memory_request_mb": 256,
            "payload": {},
        },
        headers=headers,
    )

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "aiops_workers_active 1.0" in metrics.text
    assert "aiops_diagnostic_jobs_queued 1.0" in metrics.text


def test_metrics_expose_completed_job_count(client, headers):
    worker_id = _register_worker(client, headers)
    job = client.post(
        "/api/jobs",
        json={
            "type": "system_status",
            "priority": "normal",
            "cpu_request": 1.0,
            "memory_request_mb": 256,
            "payload": {},
        },
        headers=headers,
    ).json()
    claimed = client.post(f"/api/workers/{worker_id}/claim", headers=headers)
    assert claimed.json()["id"] == job["id"]
    client.post(
        f"/api/workers/{worker_id}/complete",
        json={"job_id": job["id"], "status": "succeeded", "result": "ok"},
        headers=headers,
    )

    metrics = client.get("/metrics").text
    assert 'aiops_diagnostic_job_completions_total{status="succeeded"} 1.0' in metrics
    assert "aiops_diagnostic_jobs_running 0.0" in metrics
