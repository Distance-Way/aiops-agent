import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence

from app.config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    size INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    content TEXT NOT NULL,
    vector TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    arguments TEXT NOT NULL,
    output TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_tool_runs_session ON tool_runs(session_id, created_at);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.database_path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        conn.executescript(SCHEMA)


def reset_db() -> None:
    """Drop the database file. Used by the test suite."""
    path = Path(settings.database_path)
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(path) + suffix)
        if candidate.exists():
            candidate.unlink()
    init_db()


def _new_session_id() -> str:
    return "s_" + uuid.uuid4().hex[:12]


def create_session(title: str = "新会话", session_id: str | None = None) -> sqlite3.Row:
    sid = session_id or _new_session_id()
    now = utc_now()
    with connection() as conn:
        conn.execute(
            "INSERT INTO sessions(id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (sid, title, now, now),
        )
    return get_session(sid)


def get_session(session_id: str) -> sqlite3.Row | None:
    with connection() as conn:
        return conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()


def list_sessions(limit: int = 20) -> list[sqlite3.Row]:
    with connection() as conn:
        return conn.execute(
            """
            SELECT s.id, s.title, s.created_at, s.updated_at,
                   (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS message_count
            FROM sessions s
            ORDER BY s.updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def get_or_create_session(session_id: str | None, title: str = "新会话") -> sqlite3.Row:
    if session_id:
        row = get_session(session_id)
        if row:
            return row
    return create_session(title, session_id)


def add_message(session_id: str, role: str, content: str) -> None:
    now = utc_now()
    with connection() as conn:
        conn.execute(
            "INSERT INTO messages(session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now),
        )
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id)
        )


def get_messages(session_id: str) -> list[sqlite3.Row]:
    with connection() as conn:
        return conn.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()


def delete_session(session_id: str) -> bool:
    with connection() as conn:
        cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cursor.rowcount > 0


def add_document(doc_id: str, name: str, size: int) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO documents(id, name, size, created_at) VALUES (?, ?, ?, ?)",
            (doc_id, name, size, utc_now()),
        )


def list_documents() -> list[sqlite3.Row]:
    with connection() as conn:
        return conn.execute(
            """
            SELECT d.id, d.name, d.size, d.created_at,
                   COUNT(c.id) AS chunk_count
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            GROUP BY d.id
            ORDER BY d.created_at DESC
            """
        ).fetchall()


def delete_document(doc_id: str) -> bool:
    with connection() as conn:
        cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        return cursor.rowcount > 0


def add_chunks(chunks: Sequence[tuple[str, str, int, str, str]]) -> None:
    with connection() as conn:
        conn.executemany(
            """
            INSERT INTO chunks(id, document_id, position, content, vector)
            VALUES (?, ?, ?, ?, ?)
            """,
            chunks,
        )


def list_chunks() -> list[sqlite3.Row]:
    with connection() as conn:
        return conn.execute(
            """
            SELECT c.id AS chunk_id, c.document_id, c.position, c.content, c.vector,
                   d.name AS document_name
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            """
        ).fetchall()


def add_tool_run(
    session_id: str,
    name: str,
    arguments: dict,
    output: str,
    status: str,
    duration_ms: float,
) -> None:
    import json

    with connection() as conn:
        conn.execute(
            """
            INSERT INTO tool_runs(session_id, name, arguments, output, status, duration_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, name, json.dumps(arguments, ensure_ascii=False), output, status, duration_ms, utc_now()),
        )
