import json
import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "memory.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_memory() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT,
                user_role TEXT,
                last_intent TEXT,
                last_agent TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_session_memory(session_id: str) -> dict[str, Any]:
    initialize_memory()
    with get_connection() as conn:
        session_row = conn.execute(
            """
            SELECT session_id, username, user_role, last_intent, last_agent
            FROM sessions
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()

        messages = conn.execute(
            """
            SELECT role, content, metadata
            FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 6
            """,
            (session_id,),
        ).fetchall()

    history = []
    for message in reversed(messages):
        history.append(
            {
                "role": message["role"],
                "content": message["content"],
                "metadata": json.loads(message["metadata"]) if message["metadata"] else {},
            }
        )

    return {
        "session": dict(session_row) if session_row else {},
        "history": history,
    }


def upsert_session_memory(
    session_id: str,
    username: str | None,
    user_role: str | None,
    last_intent: str | None,
    last_agent: str | None,
) -> None:
    initialize_memory()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_id, username, user_role, last_intent, last_agent)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                username = COALESCE(excluded.username, sessions.username),
                user_role = COALESCE(excluded.user_role, sessions.user_role),
                last_intent = COALESCE(excluded.last_intent, sessions.last_intent),
                last_agent = COALESCE(excluded.last_agent, sessions.last_agent),
                updated_at = CURRENT_TIMESTAMP
            """,
            (session_id, username, user_role, last_intent, last_agent),
        )


def save_message(
    session_id: str,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    initialize_memory()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO messages (session_id, role, content, metadata)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, json.dumps(metadata or {})),
        )
