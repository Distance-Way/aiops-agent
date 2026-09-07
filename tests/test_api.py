import os
from pathlib import Path


def test_health_and_metrics(client):
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "http_requests_total" in metrics.text


def test_api_key_required(client):
    response = client.get("/api/sessions")
    assert response.status_code == 401


def test_create_list_and_delete_session(client, headers):
    created = client.post("/api/sessions", json={"title": "排障会话"}, headers=headers)
    assert created.status_code == 201
    session_id = created.json()["id"]

    listed = client.get("/api/sessions", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == session_id for item in listed.json())

    deleted = client.delete(f"/api/sessions/{session_id}", headers=headers)
    assert deleted.status_code == 204


def test_chat_time_tool(client, headers):
    response = client.post(
        "/api/chat",
        json={"message": "现在几点", "use_rag": False},
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert "当前时间" in payload["reply"]
    names = [tool["name"] for tool in payload["tools_executed"]]
    assert "get_current_time" in names


def test_agent_metrics_exposed_after_chat(client, headers):
    response = client.post(
        "/api/chat",
        json={"message": "现在几点", "use_rag": False},
        headers=headers,
    )
    assert response.status_code == 200

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "ai_chat_requests_total" in metrics.text
    assert "agent_loop_steps_total" in metrics.text
    assert "agent_tool_calls_total{" in metrics.text
    assert 'tool="get_current_time"' in metrics.text
    assert 'status="success"' in metrics.text


def test_chat_system_status_tool(client, headers):
    response = client.post(
        "/api/chat",
        json={"message": "查看服务器状态", "use_rag": False},
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    names = [tool["name"] for tool in payload["tools_executed"]]
    assert "get_system_status" in names
    assert "系统状态诊断" in payload["reply"]


def test_chat_log_tool(client, headers):
    log_path = Path(os.environ["LOG_FILE_PATH"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        '{"level": "INFO", "message": "started"}\n'
        '{"level": "ERROR", "message": "database timeout"}\n'
        '{"level": "ERROR", "message": "connection reset"}\n',
        encoding="utf-8",
    )
    response = client.post(
        "/api/chat",
        json={"message": "查询日志中的 ERROR", "use_rag": False},
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    names = [tool["name"] for tool in payload["tools_executed"]]
    assert "query_logs" in names
    assert "database timeout" in payload["reply"]


def test_chat_rag_runbook(client, headers, sample_runbook):
    upload = client.post(
        "/api/documents",
        files={"file": ("disk-manual.md", sample_runbook.encode("utf-8"), "text/markdown")},
        headers=headers,
    )
    assert upload.status_code == 201

    response = client.post(
        "/api/chat",
        json={"message": "磁盘满了怎么处理，请根据排障手册回答", "top_k": 3},
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    names = [tool["name"] for tool in payload["tools_executed"]]
    assert "search_runbook" in names
    assert payload["sources"] == ["disk-manual.md"]
    assert "df -h" in payload["reply"]


def test_document_upload_search_delete(client, headers, sample_runbook):
    upload = client.post(
        "/api/documents",
        files={"file": ("ops.md", sample_runbook.encode("utf-8"), "text/markdown")},
        headers=headers,
    )
    assert upload.status_code == 201
    document = upload.json()
    assert document["chunk_count"] >= 1

    listed = client.get("/api/documents", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    search = client.post(
        "/api/search",
        json={"query": "磁盘使用率达到 90", "top_k": 3},
        headers=headers,
    )
    assert search.status_code == 200
    hits = search.json()["hits"]
    assert hits and "df -h" in hits[0]["content"]

    deleted = client.delete(f"/api/documents/{document['id']}", headers=headers)
    assert deleted.status_code == 204
    search_after = client.post(
        "/api/search",
        json={"query": "磁盘使用率达到 90", "top_k": 3},
        headers=headers,
    )
    assert search_after.json()["hits"] == []


def test_status_endpoint(client, headers):
    response = client.get("/api/status", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    for key in ("cpu_percent", "memory", "disk", "process"):
        assert key in payload


def test_ui_page_served(client):
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "AIOps Agent" in response.text
