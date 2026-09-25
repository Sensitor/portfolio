"""
Database connection and migrations.

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

Migrations
----------
`CREATE TABLE IF NOT EXISTS` never touches a table that already exists, so a
schema change reaches nobody who has already saved anything — which is every
real user. Two mechanisms cover that:

* **Added columns** are applied in place with `ALTER TABLE`, which SQLite does
  cheaply and without rewriting the file.
* **Changed constraints** — a new foreign key, a new CHECK — cannot be added in
  place at all. Those need the table rebuilt, and the rebuild is versioned by
  `PRAGMA user_version` so it runs exactly once.

A rebuild is the one operation here that can lose data if it goes wrong, so it
runs inside a transaction, copies only columns present in both shapes, and is
tested against a database built from the previous schema and populated.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from .models import SCHEMA, SCHEMA_VERSION, TABLES, USER_OWNED

DEFAULT_PATH = os.getenv("SENSITOR_DB_PATH", "sensitor_data.db")


def now() -> str:
    """UTC timestamp, second precision — the format every table stores."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str = DEFAULT_PATH) -> sqlite3.Connection:
    """
    Open the database, apply the schema, and bring it up to the current version.

    `check_same_thread=False` because Streamlit serves reruns from a thread pool;
    the caller is responsible for serialising access, which `Store` does with a
    lock.
    """
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)

    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # Foreign keys stay off while the schema is applied and migrated. A rebuild
    # drops and recreates tables that others reference, and with enforcement on,
    # SQLite would cascade those drops into the very rows being migrated.
    conn.execute("PRAGMA foreign_keys = OFF")

    had_tables = _table_names(conn) != set()
    conn.executescript(SCHEMA)
    _migrate(conn, fresh=not had_tables)

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    return conn


# =============================================================================
# MIGRATIONS
# =============================================================================

# Columns added to a table after it first shipped. Applied whenever absent, so
# this is safe to run on every open and cheap enough to.
_ADDED_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "trades": [("raw", "TEXT")],
    "trading_accounts": [("last_synced_at", "TEXT"),
                         ("last_sync_trades", "INTEGER")],
    "users": [("password_hash", "TEXT"), ("last_login_at", "TEXT"),
              ("failed_logins", "INTEGER NOT NULL DEFAULT 0"),
              ("locked_until", "TEXT")],
}


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {r["name"] for r in
            conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]


def _migrate(conn: sqlite3.Connection, *, fresh: bool) -> None:
    """Bring an existing database up to `SCHEMA_VERSION`."""
    if fresh:
        # Nothing existed before this open, so `executescript` just created the
        # current shape. Stamping it here is what keeps a new database from
        # being run through migrations written for old ones.
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        return

    _add_missing_columns(conn)

    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version < 2:
        _to_v2(conn)
    # Version 3 adds credentials and sessions. Both arrive as new columns and a
    # new table, which `_add_missing_columns` and `executescript` have already
    # applied — no rebuild, so there is nothing further to do here.
    #
    # Version 4 adds `workspace`, the portfolio being worked on right now. It is
    # a new table and nothing else, so `executescript` has already created it and
    # no existing row is touched. An older database simply gains an empty
    # workspace, which restores to "nothing saved yet" — the correct answer for
    # someone who has never had one.
    #
    # The version is still stamped, so a database that has been through this is
    # distinguishable from one that has not.
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def _add_missing_columns(conn: sqlite3.Connection) -> None:
    existing_tables = _table_names(conn)
    for table, columns in _ADDED_COLUMNS.items():
        if table not in existing_tables:
            continue
        present = set(_columns(conn, table))
        for name, declaration in columns:
            if name not in present:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")


def _to_v2(conn: sqlite3.Connection) -> None:
    """
    Version 2: every user-owned table cascades from `users`, and `trades`
    constrains its direction.

    SQLite cannot add a foreign key or a CHECK to an existing table, so each one
    is rebuilt: rename aside, create at the current definition, copy the columns
    the two shapes share, drop the old. Copying by shared column rather than by
    `SELECT *` is what lets this run on a database that did or did not receive
    the `raw` column earlier.
    """
    tables = _table_names(conn)

    # A foreign key to `users` is unenforceable until every referenced email is
    # there. Older databases wrote portfolios and trades without ever creating
    # the user row, so backfill before the constraint exists to reject them.
    _backfill_users(conn, tables)

    # `ALTER TABLE ... RENAME TO` rewrites the foreign keys of *other* tables to
    # follow the new name. That is helpful everywhere except here: renaming
    # `portfolios` aside repointed `snapshots` at the scratch table, and
    # dropping the scratch table then left `snapshots` referencing something
    # that no longer exists — a database that opens fine and fails on the first
    # cascade. `legacy_alter_table` turns that rewriting off, which is exactly
    # what a rebuild wants: referencing tables should keep pointing at the name,
    # because the name is about to hold the new table.
    conn.execute("PRAGMA legacy_alter_table = ON")
    try:
        for table in USER_OWNED:
            if table not in tables:
                continue
            _rebuild(conn, table)
    finally:
        conn.execute("PRAGMA legacy_alter_table = OFF")

    conn.executescript(SCHEMA)          # recreate the indexes the drops removed
    _verify(conn)


def _backfill_users(conn: sqlite3.Connection, tables: set[str]) -> None:
    emails: set[str] = set()
    for table in USER_OWNED:
        if table in tables and "user_email" in _columns(conn, table):
            emails.update(
                r["user_email"] for r in
                conn.execute(f"SELECT DISTINCT user_email FROM {table}")
                if r["user_email"]
            )
    if not emails:
        return

    stamp = now()
    conn.executemany(
        """INSERT INTO users (email, tier, created_at, updated_at)
           VALUES (?, 'free', ?, ?)
           ON CONFLICT(email) DO NOTHING""",
        [(email, stamp, stamp) for email in sorted(emails)],
    )


def _verify(conn: sqlite3.Connection) -> None:
    """
    Refuse to finish a migration that left the database inconsistent.

    `foreign_key_check` reports every row whose reference does not resolve, and
    `integrity_check` every structural fault. Raising here means a broken
    migration is a failed open on a file that is still on disk and still holds
    its rows — rather than an app that starts, looks fine, and fails on the
    first delete.
    """
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        tables = sorted({row[0] for row in violations})
        raise sqlite3.IntegrityError(
            f"migration left {len(violations)} unresolved references "
            f"in {', '.join(tables)}; the database was not modified further"
        )

    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise sqlite3.IntegrityError(f"migration left the database inconsistent: {result}")


def _rebuild(conn: sqlite3.Connection, table: str) -> None:
    """Recreate one table at its current definition, carrying its rows across."""
    old_columns = _columns(conn, table)
    if not old_columns:
        return

    conn.execute(f"ALTER TABLE {table} RENAME TO _migrating_{table}")
    conn.execute(TABLES[table])

    shared = [c for c in _columns(conn, table) if c in old_columns]
    if shared:
        names = ", ".join(shared)
        conn.execute(
            f"INSERT OR IGNORE INTO {table} ({names}) "
            f"SELECT {names} FROM _migrating_{table}"
        )
    conn.execute(f"DROP TABLE _migrating_{table}")
