"""
Database schema and row models.

Pure declarations: the table definitions, the dataclasses the rest of the app
passes around, and the mapping between a sqlite row and those dataclasses. No
connection handling and no queries, so the schema can be read — or applied to a
different database — without pulling in the driver plumbing.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

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
