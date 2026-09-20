"""
Database connection.

Isolated from the repository so the backend can change in one place. Everything
above this module works through `Store`, which takes whatever `connect()`
returns; swapping SQLite for Postgres means rewriting this file and nothing else.

Where the data lives, and the catch
-----------------------------------
The default is a local SQLite file. That is correct on your own machine and for
a single-user deployment. It is **not** durable on Streamlit Cloud: that
filesystem is ephemeral, so the database is wiped whenever the app restarts,
redeploys or sleeps. Point `SENSITOR_DB_PATH` at a persistent volume, or replace
this module, before treating saved data as safe.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from .models import SCHEMA

DEFAULT_PATH = os.getenv("SENSITOR_DB_PATH", "sensitor_data.db")


def now() -> str:
    """UTC timestamp, second precision — the format every table stores."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str = DEFAULT_PATH) -> sqlite3.Connection:
    """
    Open the database and apply the schema.

    `check_same_thread=False` because Streamlit serves reruns from a thread pool;
    the caller is responsible for serialising access, which `Store` does with a
    lock. Foreign keys are enabled explicitly since SQLite leaves them off.
    """
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()
    return conn


# Columns added after a table first shipped. `CREATE TABLE IF NOT EXISTS` leaves
# an existing database untouched, so a new column never reaches anyone who
# already has the file — which is every user who has saved anything. Each entry
# is applied only when the column is absent, so this is safe to run on every
# open and cheap enough to.
_ADDED_COLUMNS = {
    "trades": [("raw", "TEXT")],
}


def _migrate(conn: sqlite3.Connection) -> None:
    for table, columns in _ADDED_COLUMNS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        if not existing:                      # table not created yet
            continue
        for name, declaration in columns:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")
