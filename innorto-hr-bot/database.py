import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

DB_PATH = "innorto_hr.db"
log = logging.getLogger(__name__)


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                mode        TEXT DEFAULT 'unknown',
                step        INTEGER DEFAULT 0,
                completed   INTEGER DEFAULT 0,
                created_at  TEXT,
                updated_at  TEXT
            )
        """)


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_user(user_id: int) -> Optional[dict]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def upsert_user(user_id: int, **kwargs):
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    with _conn() as conn:
        existing = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if existing:
            sets = ", ".join(f"{k} = ?" for k in kwargs)
            conn.execute(f"UPDATE users SET {sets} WHERE user_id = ?", (*kwargs.values(), user_id))
        else:
            kwargs["user_id"] = user_id
            kwargs["created_at"] = kwargs["updated_at"]
            cols = ", ".join(kwargs.keys())
            placeholders = ", ".join("?" * len(kwargs))
            conn.execute(f"INSERT INTO users ({cols}) VALUES ({placeholders})", tuple(kwargs.values()))


def set_mode(user_id: int, mode: str):
    upsert_user(user_id, mode=mode, step=0, completed=0)


def set_step(user_id: int, step: int):
    upsert_user(user_id, step=step)


def set_completed(user_id: int):
    upsert_user(user_id, completed=1, mode="employee")
