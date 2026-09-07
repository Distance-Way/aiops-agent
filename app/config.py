import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "aiops-agent")
    api_key: str = os.getenv("APP_API_KEY", "dev-key-change-me")
    database_path: str = os.getenv(
        "DATABASE_PATH", str(BASE_DIR / "data" / "agent.db")
    )
    log_file_path: str = os.getenv(
        "LOG_FILE_PATH", str(BASE_DIR / "logs" / "agent.log")
    )
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock").lower()
    llm_base_url: str = os.getenv(
        "LLM_BASE_URL", "https://api.openai.com/v1"
    )
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    max_tool_steps: int = _env_int("MAX_TOOL_STEPS", 3)
    history_limit: int = _env_int("HISTORY_LIMIT", 10)
    rate_limit: int = _env_int("RATE_LIMIT", 120)
    rate_window_seconds: int = _env_int("RATE_WINDOW_SECONDS", 60)
    tool_output_limit: int = _env_int("TOOL_OUTPUT_LIMIT", 2000)
    tool_timeout_seconds: float = float(os.getenv("TOOL_TIMEOUT_SECONDS", "5"))
    worker_ttl_seconds: float = float(os.getenv("WORKER_TTL_SECONDS", "60"))
    chunk_size: int = _env_int("CHUNK_SIZE", 400)
    chunk_overlap: int = _env_int("CHUNK_OVERLAP", 60)


settings = Settings()
