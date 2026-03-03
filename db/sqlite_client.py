"""
db/sqlite_client.py
====================
Nyaya Mitra — SQLite Session and Query Logging (MVP)
------------------------------------------------------
Provides a lightweight local database for storing:
  • Anonymous sessions (UUID only — no PII)
  • Query logs (text + response + latency)
  • Draft logs (document type + output)

This will be replaced by PostgreSQL via Alembic migrations in Phase 2.
All methods use SQLAlchemy Core (not ORM) for simplicity.
"""

import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import SQLITE_DB_PATH

logger = logging.getLogger(__name__)


def _get_connection() -> sqlite3.Connection:
    """Opens a SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db() -> None:
    """
    Creates tables if they do not already exist.
    Called once during FastAPI lifespan startup.
    """
    Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    ddl = """
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        tier TEXT DEFAULT 'free',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        query_text TEXT NOT NULL,
        response_json TEXT NOT NULL,
        latency_ms INTEGER,
        feedback INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        document_type TEXT NOT NULL,
        accused_name TEXT,
        input_facts TEXT NOT NULL,
        output_draft TEXT NOT NULL,
        latency_ms INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """

    with _get_connection() as conn:
        conn.executescript(ddl)
    logger.info("SQLite database initialized at: %s", SQLITE_DB_PATH)


def create_session(session_id: Optional[str] = None) -> str:
    """
    Creates a new anonymous session record.
    Returns the session_id (UUID string).
    """
    sid = session_id or str(uuid.uuid4())
    with _get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (id) VALUES (?)",
            (sid,),
        )
    return sid


def log_query(
    session_id: str,
    query_text: str,
    response_json: str,
    latency_ms: int,
) -> None:
    """Persists a completed query + response for analytics."""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO queries (session_id, query_text, response_json, latency_ms)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, query_text, response_json, latency_ms),
            )
    except Exception as exc:
        # Non-fatal — never let logging failures break the main request
        logger.warning("Failed to log query: %s", exc)


def log_draft(
    session_id: str,
    document_type: str,
    accused_name: Optional[str],
    input_facts: str,
    output_draft: str,
    latency_ms: int,
) -> None:
    """Persists a completed draft for analytics."""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO drafts 
                    (session_id, document_type, accused_name, input_facts, output_draft, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, document_type, accused_name, input_facts, output_draft, latency_ms),
            )
    except Exception as exc:
        logger.warning("Failed to log draft: %s", exc)
