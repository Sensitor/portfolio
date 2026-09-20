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

CREATE TABLE IF NOT EXISTS trading_accounts (
    id          TEXT NOT NULL,
    user_email  TEXT NOT NULL,
    name        TEXT NOT NULL,
    broker      TEXT,
    currency    TEXT NOT NULL DEFAULT 'USD',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (user_email, id)
);

-- Trades are keyed by (user_email, id), not by id alone. A broker deal id is
-- only unique within one broker account, so two users importing from the same
-- platform can genuinely collide. Scoping the key by user makes that impossible
-- rather than unlikely, and it is the same shape multi-user needs later.
CREATE TABLE IF NOT EXISTS trades (
    id               TEXT NOT NULL,
    user_email       TEXT NOT NULL,
    account_id       TEXT,

    symbol           TEXT NOT NULL,
    direction        TEXT NOT NULL,
    entry_price      REAL NOT NULL,
    exit_price       REAL,
    size             REAL NOT NULL,
    stop_loss        REAL,
    take_profit      REAL,
    opened_at        TEXT NOT NULL,
    closed_at        TEXT,

    gross_pnl        REAL,
    commission       REAL NOT NULL DEFAULT 0,
    swap             REAL NOT NULL DEFAULT 0,
    account_currency TEXT NOT NULL DEFAULT 'USD',

    setups           TEXT NOT NULL DEFAULT '[]',   -- JSON array
    mistakes         TEXT NOT NULL DEFAULT '[]',   -- JSON array
    timeframe        TEXT,
    market_regime    TEXT,
    setup_quality    INTEGER,
    confidence       INTEGER,
    entry_reason     TEXT,
    exit_reason      TEXT,

    emotion_before   TEXT,
    emotion_during   TEXT,
    emotion_after    TEXT,
    discipline       INTEGER,
    notes            TEXT,

    image_pre        TEXT,
    image_post       TEXT,
    image_annotated  TEXT,

    source           TEXT NOT NULL DEFAULT 'manual',

    -- The connector's original payload, as JSON. Derived values are never
    -- stored, but the *source* record is: when the normaliser is corrected, the
    -- trades can be rebuilt from what the broker actually said instead of
    -- re-downloading a history that may no longer be reachable.
    raw              TEXT,

    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    PRIMARY KEY (user_email, id)
);

CREATE INDEX IF NOT EXISTS idx_portfolios_user ON portfolios(user_email);
CREATE INDEX IF NOT EXISTS idx_snapshots_portfolio ON snapshots(portfolio_id, taken_at);
CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_email, closed_at);
CREATE INDEX IF NOT EXISTS idx_trades_account ON trades(user_email, account_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(user_email, symbol);
"""

# Columns written by the trade upsert, in order. Kept as a list so the INSERT,
# the placeholder count and the UPDATE clause can never drift apart.
TRADE_COLUMNS = [
    "id", "user_email", "account_id",
    "symbol", "direction", "entry_price", "exit_price", "size",
    "stop_loss", "take_profit", "opened_at", "closed_at",
    "gross_pnl", "commission", "swap", "account_currency",
    "setups", "mistakes", "timeframe", "market_regime",
    "setup_quality", "confidence", "entry_reason", "exit_reason",
    "emotion_before", "emotion_during", "emotion_after", "discipline", "notes",
    "image_pre", "image_post", "image_annotated",
    "source", "raw", "created_at", "updated_at",
]


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


# =============================================================================
# TRADING ACCOUNT
# =============================================================================

@dataclass
class TradingAccount:
    id: str
    user_email: str
    name: str
    broker: str | None
    currency: str
    created_at: str
    updated_at: str


def _to_account(row: sqlite3.Row) -> TradingAccount:
    return TradingAccount(
        id=row["id"], user_email=row["user_email"], name=row["name"],
        broker=row["broker"], currency=row["currency"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


# =============================================================================
# TRADE ROW MAPPING
# =============================================================================

def trade_to_row(trade, user_email: str, now: str) -> dict:
    """
    A `trading.Trade` flattened to database columns.

    Derived values (P&L, R multiple, duration) are deliberately not stored: they
    are functions of the stored fields, and persisting them means a schema where
    two columns can disagree. The engine recomputes them on load, which is cheap.
    """
    return {
        "id": trade.id,
        "user_email": user_email,
        "account_id": trade.account_id,
        "symbol": trade.symbol,
        "direction": trade.direction.value,
        "entry_price": float(trade.entry_price),
        "exit_price": trade.exit_price,
        "size": float(trade.size),
        "stop_loss": trade.stop_loss,
        "take_profit": trade.take_profit,
        "opened_at": trade.opened_at.isoformat() if trade.opened_at else None,
        "closed_at": trade.closed_at.isoformat() if trade.closed_at else None,
        "gross_pnl": trade.gross_pnl,
        "commission": float(trade.commission or 0.0),
        "swap": float(trade.swap or 0.0),
        "account_currency": trade.account_currency or "USD",
        "setups": json.dumps(list(trade.setups or [])),
        "mistakes": json.dumps(list(trade.mistakes or [])),
        "timeframe": trade.timeframe,
        "market_regime": trade.market_regime,
        "setup_quality": trade.setup_quality,
        "confidence": trade.confidence,
        "entry_reason": trade.entry_reason,
        "exit_reason": trade.exit_reason,
        "emotion_before": trade.emotion_before,
        "emotion_during": trade.emotion_during,
        "emotion_after": trade.emotion_after,
        "discipline": trade.discipline,
        "notes": trade.notes,
        "image_pre": trade.image_pre,
        "image_post": trade.image_post,
        "image_annotated": trade.image_annotated,
        "source": trade.source or "manual",
        "raw": json.dumps(trade.raw) if trade.raw else None,
        "created_at": now,
        "updated_at": now,
    }


def row_to_trade(row: sqlite3.Row):
    """
    Rebuild a `trading.Trade` from a database row.

    Imported here rather than at module scope so `database.models` stays
    importable without pulling the trading engine in — the schema is useful on
    its own, for a migration tool or an inspection script.
    """
    from ..trading.models import Trade

    return Trade.from_dict({
        "id": row["id"],
        "symbol": row["symbol"],
        "direction": row["direction"],
        "entry_price": row["entry_price"],
        "exit_price": row["exit_price"],
        "size": row["size"],
        "stop_loss": row["stop_loss"],
        "take_profit": row["take_profit"],
        "opened_at": row["opened_at"],
        "closed_at": row["closed_at"],
        "gross_pnl": row["gross_pnl"],
        "commission": row["commission"],
        "swap": row["swap"],
        "account_id": row["account_id"],
        "account_currency": row["account_currency"],
        "setups": json.loads(row["setups"] or "[]"),
        "mistakes": json.loads(row["mistakes"] or "[]"),
        "timeframe": row["timeframe"],
        "market_regime": row["market_regime"],
        "setup_quality": row["setup_quality"],
        "confidence": row["confidence"],
        "entry_reason": row["entry_reason"],
        "exit_reason": row["exit_reason"],
        "emotion_before": row["emotion_before"],
        "emotion_during": row["emotion_during"],
        "emotion_after": row["emotion_after"],
        "discipline": row["discipline"],
        "notes": row["notes"],
        "image_pre": row["image_pre"],
        "image_post": row["image_post"],
        "image_annotated": row["image_annotated"],
        "source": row["source"],
        "raw": json.loads(row["raw"]) if _has(row, "raw") and row["raw"] else {},
    })


def _has(row: sqlite3.Row, column: str) -> bool:
    """Whether a row carries a column — true after the migration, false before."""
    return column in row.keys()
