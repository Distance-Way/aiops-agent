def test_register_worker_and_submit_list_get_job(client, headers):
    worker = client.post(
        "/api/workers",
        json={
            "name": "worker-a",
            "cpu_capacity": 2.0,
            "memory_capacity_mb": 1024,
        },
        headers=headers,
    )
    assert worker.status_code == 201
    worker_id = worker.json()["id"]
    assert worker.json()["status"] == "active"

    job = client.post(
        "/api/jobs",
        json={
            "type": "system_status",
            "priority": "high",
            "cpu_request": 1.0,
            "memory_request_mb": 128,
            "payload": {},
        },
        headers=headers,
    )
    assert job.status_code == 201
    payload = job.json()
    assert payload["type"] == "system_status"
    assert payload["priority"] == "high"
    assert payload["status"] == "queued"
    assert payload["worker_id"] is None

    listed = client.get("/api/jobs", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == payload["id"] for item in listed.json())

    detail = client.get(f"/api/jobs/{payload['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == payload["id"]

    workers = client.get("/api/workers", headers=headers)
    assert workers.status_code == 200
    assert any(item["id"] == worker_id for item in workers.json())


def test_job_api_requires_auth(client):
    response = client.post(
        "/api/jobs",
        json={
            "type": "system_status",
            "priority": "normal",
            "cpu_request": 1.0,
            "memory_request_mb": 128,
            "payload": {},
        },
    )
    assert response.status_code == 401
