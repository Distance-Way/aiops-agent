import os
import tempfile
from pathlib import Path

import pytest


TEST_DIR = tempfile.mkdtemp(prefix="aiops-agent-tests-")
os.environ["APP_API_KEY"] = "test-api-key"
os.environ["DATABASE_PATH"] = str(Path(TEST_DIR) / "test.db")
os.environ["LOG_FILE_PATH"] = str(Path(TEST_DIR) / "agent.log")
os.environ["LLM_PROVIDER"] = "mock"
os.environ["LLM_API_KEY"] = ""

from app import db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    db.reset_db()
    log_file = Path(os.environ["LOG_FILE_PATH"])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("", encoding="utf-8")
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def headers():
    return {"X-API-Key": "test-api-key"}


@pytest.fixture
def sample_runbook() -> str:
    return """# 磁盘满排障手册

当磁盘使用率达到 90% 时应立即检查。
第一步执行 df -h 确认分区使用率。
第二步执行 du -sh /var/log/* 定位大文件目录。
第三步清理历史日志并设置日志轮转。
若无法清理，需要评估扩容或归档。
"""
