from app import db


def _register_worker(client, headers, cpu=4.0, memory=4096):
    response = client.post(
        "/api/workers",
        json={
            "name": "worker-a",
            "cpu_capacity": cpu,
            "memory_capacity_mb": memory,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _submit_job(client, headers, priority="normal", cpu=1.0, memory=256):
    response = client.post(
        "/api/jobs",
        json={
            "type": "system_status",
            "priority": priority,
            "cpu_request": cpu,
            "memory_request_mb": memory,
            "payload": {},
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_claim_orders_by_priority_and_complete_releases_capacity(client, headers):
    worker_id = _register_worker(client, headers)
    low = _submit_job(client, headers, priority="low")
    high = _submit_job(client, headers, priority="high")

    claimed = client.post(f"/api/workers/{worker_id}/claim", headers=headers)
    assert claimed.status_code == 200
    assert claimed.json()["id"] == high["id"]
    assert claimed.json()["status"] == "running"
    assert claimed.json()["worker_id"] == worker_id

    detail = client.get(f"/api/jobs/{high['id']}", headers=headers)
    assert detail.json()["status"] == "running"
    assert detail.json()["started_at"] is not None

    completed = client.post(
        f"/api/workers/{worker_id}/complete",
        json={
            "job_id": high["id"],
            "status": "succeeded",
            "result": "system ok",
        },
        headers=headers,
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "succeeded"
    assert completed.json()["finished_at"] is not None

    next_claimed = client.post(f"/api/workers/{worker_id}/claim", headers=headers)
    assert next_claimed.json()["id"] == low["id"]


def test_job_stays_queued_until_capacity_is_released(client, headers):
    worker_id = _register_worker(client, headers, cpu=1.0, memory=512)
    first = _submit_job(client, headers, cpu=1.0, memory=256)
    second = _submit_job(client, headers, cpu=1.0, memory=256)

    first_claim = client.post(f"/api/workers/{worker_id}/claim", headers=headers)
    assert first_claim.json()["id"] == first["id"]

    blocked = client.post(f"/api/workers/{worker_id}/claim", headers=headers)
    assert blocked.status_code == 200
    assert blocked.json() is None
    assert client.get(f"/api/jobs/{second['id']}", headers=headers).json()["status"] == "queued"

    client.post(
        f"/api/workers/{worker_id}/complete",
        json={"job_id": first["id"], "status": "failed", "error": "timeout"},
        headers=headers,
    )

    second_claim = client.post(f"/api/workers/{worker_id}/claim", headers=headers)
    assert second_claim.json()["id"] == second["id"]


def test_stale_worker_is_not_selected(client, headers):
    worker_id = _register_worker(client, headers)
    _submit_job(client, headers)
    db.set_worker_heartbeat(worker_id, "2020-01-01T00:00:00+00:00")

    claimed = client.post(f"/api/workers/{worker_id}/claim", headers=headers)
    assert claimed.status_code == 200
    assert claimed.json() is None


def test_claim_requires_existing_worker(client, headers):
    _submit_job(client, headers)
    response = client.post("/api/workers/w_missing/claim", headers=headers)
    assert response.status_code == 404
