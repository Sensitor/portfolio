"""
Persistence layer — saved portfolios, snapshots and users.

Everything in the app up to now lived in session state and vanished on reload.
This module gives it somewhere to go.

Where the data actually lives, and the catch
--------------------------------------------
The default backend is a local SQLite file. That is correct for running on your
own machine and correct for a single-user deployment. It is **not** durable on
Streamlit Cloud: that filesystem is ephemeral, so the database is wiped whenever
the app restarts, redeploys or sleeps. Anything saved there should be treated as
a convenience cache, not as storage.

For a real multi-user deployment, point `SENSITOR_DB_PATH` at a persistent volume
or replace `_connect()` with a Postgres connection — every query below is plain
SQL through the DB-API, and the repository interface is what the pages depend on,
so swapping the driver does not touch the UI. The schema is deliberately boring
for the same reason.

Privacy
-------
Rows carry an email address and the holdings behind it. That is personal
financial data: it stays on whatever machine runs the app, it is never sent
anywhere by this module, and a deployment that shares a database between people
needs authentication in front of it — the email field here identifies a row, it
does not authenticate anyone.

No Streamlit import: this module is testable and reusable on its own.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone

DEFAULT_PATH = os.getenv("SENSITOR_DB_PATH", "sensitor_data.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email       TEXT PRIMARY KEY,
    tier        TEXT NOT NULL DEFAULT 'free',
    display_name TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email  TEXT NOT NULL,
    name        TEXT NOT NULL,
    holdings    TEXT NOT NULL,           -- JSON {ticker: weight or quantity}
    mode        TEXT NOT NULL DEFAULT 'simulation',
    currency    TEXT NOT NULL DEFAULT '$',
    notes       TEXT,
    client_name TEXT,                    -- set when the book belongs to a client
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    UNIQUE(user_email, name)
);

CREATE TABLE IF NOT EXISTS snapshots (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    taken_at     TEXT NOT NULL,
    total_value  REAL,
    weights      TEXT NOT NULL,          -- JSON {ticker: weight}
    metrics      TEXT NOT NULL,          -- JSON of the headline figures
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_portfolios_user ON portfolios(user_email);
CREATE INDEX IF NOT EXISTS idx_snapshots_portfolio ON snapshots(portfolio_id, taken_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Portfolio:
    id: int
    user_email: str
    name: str
    holdings: dict
    mode: str
    currency: str
    notes: str | None
    client_name: str | None
    created_at: str
    updated_at: str

    @property
    def is_client(self) -> bool:
        return bool(self.client_name)


@dataclass
class Snapshot:
    id: int
    portfolio_id: int
    taken_at: str
    total_value: float | None
    weights: dict
    metrics: dict


class Store:
    """
    Repository over SQLite.

    One connection, guarded by a lock: Streamlit serves reruns from a thread pool,
    and SQLite connections are not safe to share across threads without it.
    """

    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        self._lock = threading.Lock()
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    # ── Plumbing ─────────────────────────────────────────────────────────────

    @contextmanager
    def _write(self):
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def _read(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ── Users ────────────────────────────────────────────────────────────────

    def upsert_user(self, email: str, tier: str = "free",
                    display_name: str | None = None) -> None:
        """Record or refresh a user. Tier is mirrored here for the advisor view."""
        email = email.strip().lower()
        if not email:
            return
        now = _now()
        with self._write() as conn:
            conn.execute(
                """INSERT INTO users (email, tier, display_name, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(email) DO UPDATE SET
                     tier = excluded.tier,
                     display_name = COALESCE(excluded.display_name, users.display_name),
                     updated_at = excluded.updated_at""",
                (email, tier, display_name, now, now),
            )

    def get_user(self, email: str) -> dict | None:
        rows = self._read("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
        return dict(rows[0]) if rows else None

    # ── Portfolios ───────────────────────────────────────────────────────────

    def save_portfolio(self, user_email: str, name: str, holdings: dict, *,
                       mode: str = "simulation", currency: str = "$",
                       notes: str | None = None,
                       client_name: str | None = None) -> int:
        """
        Create or overwrite a portfolio by (user, name).

        Overwriting rather than erroring on a duplicate name is deliberate: the
        save button is how people iterate, and a name is how they mean to identify
        one book across those iterations.
        """
        user_email = user_email.strip().lower()
        name = name.strip()
        if not user_email or not name or not holdings:
            raise ValueError("user_email, name and holdings are all required")

        now = _now()
        payload = json.dumps(holdings)
        with self._write() as conn:
            cursor = conn.execute(
                """INSERT INTO portfolios
                     (user_email, name, holdings, mode, currency, notes, client_name,
                      created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(user_email, name) DO UPDATE SET
                     holdings = excluded.holdings,
                     mode = excluded.mode,
                     currency = excluded.currency,
                     notes = excluded.notes,
                     client_name = excluded.client_name,
                     updated_at = excluded.updated_at""",
                (user_email, name, payload, mode, currency, notes, client_name, now, now),
            )
            if cursor.lastrowid:
                return int(cursor.lastrowid)
        row = self._read(
            "SELECT id FROM portfolios WHERE user_email = ? AND name = ?",
            (user_email, name),
        )
        return int(row[0]["id"]) if row else -1

    def list_portfolios(self, user_email: str, *,
                        clients_only: bool = False) -> list[Portfolio]:
        sql = "SELECT * FROM portfolios WHERE user_email = ?"
        if clients_only:
            sql += " AND client_name IS NOT NULL AND client_name != ''"
        sql += " ORDER BY updated_at DESC"
        return [_to_portfolio(r) for r in self._read(sql, (user_email.strip().lower(),))]

    def get_portfolio(self, portfolio_id: int) -> Portfolio | None:
        rows = self._read("SELECT * FROM portfolios WHERE id = ?", (int(portfolio_id),))
        return _to_portfolio(rows[0]) if rows else None

    def rename_portfolio(self, portfolio_id: int, new_name: str) -> None:
        with self._write() as conn:
            conn.execute(
                "UPDATE portfolios SET name = ?, updated_at = ? WHERE id = ?",
                (new_name.strip(), _now(), int(portfolio_id)),
            )

    def delete_portfolio(self, portfolio_id: int) -> None:
        with self._write() as conn:
            conn.execute("DELETE FROM snapshots WHERE portfolio_id = ?", (int(portfolio_id),))
            conn.execute("DELETE FROM portfolios WHERE id = ?", (int(portfolio_id),))

    # ── Snapshots ────────────────────────────────────────────────────────────

    def add_snapshot(self, portfolio_id: int, *, total_value: float | None,
                     weights: dict, metrics: dict) -> int:
        """
        Record the portfolio's state at a point in time.

        Snapshots are what make the history view possible: the app can recompute
        metrics from prices at any time, but it cannot recover what the allocation
        *was* last month unless that was written down.
        """
        with self._write() as conn:
            cursor = conn.execute(
                """INSERT INTO snapshots (portfolio_id, taken_at, total_value, weights, metrics)
                   VALUES (?, ?, ?, ?, ?)""",
                (int(portfolio_id), _now(),
                 float(total_value) if total_value is not None else None,
                 json.dumps(weights), json.dumps(_jsonable(metrics))),
            )
            return int(cursor.lastrowid)

    def list_snapshots(self, portfolio_id: int, limit: int = 100) -> list[Snapshot]:
        rows = self._read(
            """SELECT * FROM snapshots WHERE portfolio_id = ?
               ORDER BY taken_at DESC LIMIT ?""",
            (int(portfolio_id), int(limit)),
        )
        return [_to_snapshot(r) for r in rows]

    def latest_snapshot(self, portfolio_id: int) -> Snapshot | None:
        snapshots = self.list_snapshots(portfolio_id, limit=1)
        return snapshots[0] if snapshots else None

    def delete_snapshot(self, snapshot_id: int) -> None:
        with self._write() as conn:
            conn.execute("DELETE FROM snapshots WHERE id = ?", (int(snapshot_id),))

    # ── Aggregates ───────────────────────────────────────────────────────────

    def portfolio_summaries(self, user_email: str, *,
                            clients_only: bool = False) -> list[dict]:
        """
        Every portfolio with its most recent snapshot attached.

        This is what the advisor view renders from, so it is one query plus one
        lookup per portfolio rather than a join — the row counts here are small,
        and keeping it simple keeps it portable to another database.
        """
        out = []
        for portfolio in self.list_portfolios(user_email, clients_only=clients_only):
            snapshot = self.latest_snapshot(portfolio.id)
            out.append({
                "portfolio": portfolio,
                "snapshot": snapshot,
                "metrics": snapshot.metrics if snapshot else {},
                "total_value": snapshot.total_value if snapshot else None,
                "n_snapshots": len(self.list_snapshots(portfolio.id, limit=500)),
            })
        return out


# =============================================================================
# ROW MAPPING
# =============================================================================

def _to_portfolio(row: sqlite3.Row) -> Portfolio:
    return Portfolio(
        id=int(row["id"]),
        user_email=row["user_email"],
        name=row["name"],
        holdings=json.loads(row["holdings"]),
        mode=row["mode"],
        currency=row["currency"],
        notes=row["notes"],
        client_name=row["client_name"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_snapshot(row: sqlite3.Row) -> Snapshot:
    return Snapshot(
        id=int(row["id"]),
        portfolio_id=int(row["portfolio_id"]),
        taken_at=row["taken_at"],
        total_value=row["total_value"],
        weights=json.loads(row["weights"]),
        metrics=json.loads(row["metrics"]),
    )


def _jsonable(value):
    """
    Coerce numpy scalars and pandas objects to plain JSON types.

    Metrics dicts come straight from the analytics layer and are full of
    numpy.float64, which json.dumps refuses. Anything it cannot place becomes a
    string rather than failing the write — a snapshot with one odd field is worth
    more than no snapshot.
    """
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, "item"):          # numpy scalar
        try:
            return value.item()
        except Exception:
            pass
    return str(value)
