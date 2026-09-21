"""
Repositories — the query layer the application talks to.

`Store` is the only database surface the pages and the future API use. It owns a
connection from `connection.connect()` and serialises access behind a lock,
because Streamlit serves reruns from a thread pool and SQLite connections are
not safe to share across threads without one.

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
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import asdict

from .connection import DEFAULT_PATH, connect, now as _now
from .models import (
    SCHEMA_VERSION, TRADE_COLUMNS, Portfolio, Snapshot, TradingAccount, _jsonable,
    _to_account, _to_portfolio, _to_snapshot, row_to_trade, trade_to_row,
)


def _email(value: str) -> str:
    """
    Normalise an address into the form every row is keyed by.

    One function rather than `.strip().lower()` at each call site: a single
    method that forgot the `.lower()` would file a person's trades under a second
    identity and show them an empty journal, which reads as data loss.
    """
    return (value or "").strip().lower()


class Store:
    """
    Repository over SQLite.

    One connection, guarded by a lock: Streamlit serves reruns from a thread pool,
    and SQLite connections are not safe to share across threads without it.
    """

    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        self._lock = threading.Lock()
        self._conn = connect(path)

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
        email = _email(email)
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
        rows = self._read("SELECT * FROM users WHERE email = ?", (_email(email),))
        return dict(rows[0]) if rows else None

    def list_users(self) -> list[dict]:
        """Everyone with a row. The deployment decides who may ask."""
        return [dict(r) for r in
                self._read("SELECT * FROM users ORDER BY email")]

    def _ensure_user(self, conn, email: str) -> None:
        """
        Create the user row a write is about to reference.

        Every user-owned table has a foreign key to `users`, so a portfolio or a
        trade written for someone with no row would be rejected. Calling this on
        the write paths means a caller never has to remember to register a user
        first — and it is what makes the cascade in `delete_user` complete,
        because a row that was never registered could not be cascaded from.
        """
        stamp = _now()
        conn.execute(
            """INSERT INTO users (email, tier, created_at, updated_at)
               VALUES (?, 'free', ?, ?) ON CONFLICT(email) DO NOTHING""",
            (email, stamp, stamp),
        )

    def delete_user(self, email: str) -> dict:
        """
        Remove a person and everything filed under them.

        Counted before deleting and reported back, because "your data has been
        deleted" is a claim that should be able to say how much. The children go
        through the foreign keys' cascade; they are also deleted explicitly, so
        the guarantee does not depend on a pragma being set on this connection.
        """
        email = _email(email)
        if not email:
            return {"portfolios": 0, "snapshots": 0, "accounts": 0, "trades": 0}

        counts = {
            "portfolios": self._count(
                "SELECT COUNT(*) AS n FROM portfolios WHERE user_email = ?", email),
            "snapshots": self._count(
                "SELECT COUNT(*) AS n FROM snapshots WHERE portfolio_id IN "
                "(SELECT id FROM portfolios WHERE user_email = ?)", email),
            "accounts": self._count(
                "SELECT COUNT(*) AS n FROM trading_accounts WHERE user_email = ?", email),
            "trades": self._count(
                "SELECT COUNT(*) AS n FROM trades WHERE user_email = ?", email),
        }

        with self._write() as conn:
            conn.execute(
                "DELETE FROM snapshots WHERE portfolio_id IN "
                "(SELECT id FROM portfolios WHERE user_email = ?)", (email,))
            conn.execute("DELETE FROM trades WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM trading_accounts WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM portfolios WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM users WHERE email = ?", (email,))
        return counts

    def export_user(self, email: str) -> dict:
        """
        Everything stored for one person, as plain JSON-able data.

        Portability, and the shape the API will serve. Reads through the same
        user-scoped methods as everything else, so an export cannot reach
        further than the app can.
        """
        email = _email(email)
        return {
            "user": self.get_user(email),
            "portfolios": [
                {
                    "portfolio": asdict(portfolio),
                    "snapshots": [asdict(s) for s in self.list_snapshots(
                        email, portfolio.id, limit=10_000)],
                }
                for portfolio in self.list_portfolios(email)
            ],
            "accounts": [asdict(a) for a in self.list_accounts(email)],
            "trades": [t.to_dict() for t in self.list_trades(email)],
            "schema_version": SCHEMA_VERSION,
        }

    def _count(self, sql: str, *params) -> int:
        rows = self._read(sql, tuple(params))
        return int(rows[0]["n"]) if rows else 0

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
        user_email = _email(user_email)
        name = name.strip()
        if not user_email or not name or not holdings:
            raise ValueError("user_email, name and holdings are all required")

        now = _now()
        payload = json.dumps(holdings)
        with self._write() as conn:
            self._ensure_user(conn, user_email)
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
        return [_to_portfolio(r) for r in self._read(sql, (_email(user_email),))]

    def get_portfolio(self, user_email: str, portfolio_id: int) -> Portfolio | None:
        """
        One portfolio, and only if it belongs to this user.

        Every method from here down takes the owner. An integer primary key is
        guessable, so a lookup by id alone returns whatever row holds that id —
        which on a shared database means one person's holdings answering another
        person's request. The user is not an optional extra argument for that
        reason: a parameter with a default is exactly how this comes back.
        """
        rows = self._read(
            "SELECT * FROM portfolios WHERE id = ? AND user_email = ?",
            (int(portfolio_id), _email(user_email)),
        )
        return _to_portfolio(rows[0]) if rows else None

    def rename_portfolio(self, user_email: str, portfolio_id: int,
                         new_name: str) -> bool:
        """True when a row was renamed — False when it was not this user's."""
        with self._write() as conn:
            cursor = conn.execute(
                "UPDATE portfolios SET name = ?, updated_at = ? "
                "WHERE id = ? AND user_email = ?",
                (new_name.strip(), _now(), int(portfolio_id), _email(user_email)),
            )
            return cursor.rowcount > 0

    def delete_portfolio(self, user_email: str, portfolio_id: int) -> bool:
        """
        Delete a portfolio and its snapshots. False when it was not this user's.

        The snapshots go through the foreign key's cascade on a version 2
        database. The explicit delete stays for one written down reason: a
        connection that lost `PRAGMA foreign_keys = ON` would otherwise leave
        orphaned snapshots behind, and an orphan carrying holdings is the kind
        of residue a deletion is supposed to remove.
        """
        email = _email(user_email)
        with self._write() as conn:
            conn.execute(
                "DELETE FROM snapshots WHERE portfolio_id IN "
                "(SELECT id FROM portfolios WHERE id = ? AND user_email = ?)",
                (int(portfolio_id), email),
            )
            cursor = conn.execute(
                "DELETE FROM portfolios WHERE id = ? AND user_email = ?",
                (int(portfolio_id), email),
            )
            return cursor.rowcount > 0

    # ── Snapshots ────────────────────────────────────────────────────────────
    #
    # Snapshots carry no user column; they reach their owner through the
    # portfolio. Every query below joins through it rather than trusting the
    # caller's id, so a snapshot cannot be read, written or deleted across the
    # boundary even when its own id is known.

    def add_snapshot(self, user_email: str, portfolio_id: int, *,
                     total_value: float | None, weights: dict,
                     metrics: dict) -> int:
        """
        Record the portfolio's state at a point in time.

        Snapshots are what make the history view possible: the app can recompute
        metrics from prices at any time, but it cannot recover what the allocation
        *was* last month unless that was written down.

        Returns -1 when the portfolio is not this user's, rather than writing a
        snapshot onto someone else's history.
        """
        if self.get_portfolio(user_email, portfolio_id) is None:
            return -1
        with self._write() as conn:
            cursor = conn.execute(
                """INSERT INTO snapshots (portfolio_id, taken_at, total_value, weights, metrics)
                   VALUES (?, ?, ?, ?, ?)""",
                (int(portfolio_id), _now(),
                 float(total_value) if total_value is not None else None,
                 json.dumps(weights), json.dumps(_jsonable(metrics))),
            )
            return int(cursor.lastrowid)

    def list_snapshots(self, user_email: str, portfolio_id: int,
                       limit: int = 100) -> list[Snapshot]:
        rows = self._read(
            """SELECT s.* FROM snapshots s
               JOIN portfolios p ON p.id = s.portfolio_id
               WHERE s.portfolio_id = ? AND p.user_email = ?
               ORDER BY s.taken_at DESC LIMIT ?""",
            (int(portfolio_id), _email(user_email), int(limit)),
        )
        return [_to_snapshot(r) for r in rows]

    def latest_snapshot(self, user_email: str, portfolio_id: int) -> Snapshot | None:
        snapshots = self.list_snapshots(user_email, portfolio_id, limit=1)
        return snapshots[0] if snapshots else None

    def delete_snapshot(self, user_email: str, snapshot_id: int) -> bool:
        with self._write() as conn:
            cursor = conn.execute(
                """DELETE FROM snapshots WHERE id = ? AND portfolio_id IN
                   (SELECT id FROM portfolios WHERE user_email = ?)""",
                (int(snapshot_id), _email(user_email)),
            )
            return cursor.rowcount > 0

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
            snapshot = self.latest_snapshot(user_email, portfolio.id)
            out.append({
                "portfolio": portfolio,
                "snapshot": snapshot,
                "metrics": snapshot.metrics if snapshot else {},
                "total_value": snapshot.total_value if snapshot else None,
                "n_snapshots": len(
                    self.list_snapshots(user_email, portfolio.id, limit=500)),
            })
        return out

    # ── Trading accounts ─────────────────────────────────────────────────────

    def upsert_account(self, user_email: str, account_id: str, name: str, *,
                       broker: str | None = None, currency: str = "USD") -> None:
        user_email = _email(user_email)
        now = _now()
        with self._write() as conn:
            self._ensure_user(conn, user_email)
            conn.execute(
                """INSERT INTO trading_accounts
                     (id, user_email, name, broker, currency, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(user_email, id) DO UPDATE SET
                     name = excluded.name,
                     broker = excluded.broker,
                     currency = excluded.currency,
                     updated_at = excluded.updated_at""",
                (str(account_id), user_email, name, broker, currency, now, now),
            )

    def list_accounts(self, user_email: str) -> list[TradingAccount]:
        rows = self._read(
            "SELECT * FROM trading_accounts WHERE user_email = ? ORDER BY name",
            (_email(user_email),),
        )
        return [_to_account(r) for r in rows]

    def delete_account(self, user_email: str, account_id: str) -> None:
        """Removes the account and every trade filed under it."""
        user_email = _email(user_email)
        with self._write() as conn:
            conn.execute("DELETE FROM trades WHERE user_email = ? AND account_id = ?",
                         (user_email, str(account_id)))
            conn.execute("DELETE FROM trading_accounts WHERE user_email = ? AND id = ?",
                         (user_email, str(account_id)))

    def record_sync(self, user_email: str, account_id: str, *,
                    trades: int = 0, at: str | None = None) -> None:
        """
        Mark when an account was last pulled from, and how much came back.

        Stored rather than inferred. The obvious proxy — the newest close in the
        journal — is wrong in the one case that matters: a sync that found
        nothing leaves it unchanged, so the next window reaches further back
        every time nothing happens, and a quiet fortnight turns every sync into
        a full re-download.
        """
        with self._write() as conn:
            conn.execute(
                """UPDATE trading_accounts
                   SET last_synced_at = ?, last_sync_trades = ?, updated_at = ?
                   WHERE user_email = ? AND id = ?""",
                (at or _now(), int(trades), _now(),
                 _email(user_email), str(account_id)),
            )

    def last_synced_at(self, user_email: str, account_id: str) -> str | None:
        rows = self._read(
            "SELECT last_synced_at FROM trading_accounts "
            "WHERE user_email = ? AND id = ?",
            (_email(user_email), str(account_id)),
        )
        return rows[0]["last_synced_at"] if rows else None

    # ── Trades ───────────────────────────────────────────────────────────────

    def save_trade(self, user_email: str, trade) -> None:
        self.save_trades(user_email, [trade])

    def save_trades(self, user_email: str, trades) -> int:
        """
        Upsert a batch of trades, returning how many were written.

        One statement per batch rather than per trade: a broker sync arrives with
        thousands at once, and a commit per row turns a two-second import into a
        two-minute one.

        `created_at` is preserved on conflict so a re-sync does not rewrite when a
        trade was first seen — that timestamp is the only record of it.
        """
        user_email = _email(user_email)
        if not user_email:
            raise ValueError("user_email is required")

        now = _now()
        rows = [trade_to_row(t, user_email, now) for t in trades]
        if not rows:
            return 0

        columns = ", ".join(TRADE_COLUMNS)
        placeholders = ", ".join("?" for _ in TRADE_COLUMNS)
        updates = ", ".join(
            f"{c} = excluded.{c}" for c in TRADE_COLUMNS
            if c not in ("id", "user_email", "created_at")
        )
        sql = (f"INSERT INTO trades ({columns}) VALUES ({placeholders}) "
               f"ON CONFLICT(user_email, id) DO UPDATE SET {updates}")

        with self._write() as conn:
            self._ensure_user(conn, user_email)
            conn.executemany(sql, [[row[c] for c in TRADE_COLUMNS] for row in rows])
        return len(rows)

    def list_trades(self, user_email: str, *, account_id: str | None = None,
                    symbol: str | None = None, limit: int | None = None) -> list:
        """
        Trades for a user, newest close first.

        Open trades have a null `closed_at` and sort last under `DESC`; that is
        deliberate — a list of results should lead with results.
        """
        sql = "SELECT * FROM trades WHERE user_email = ?"
        params: list = [_email(user_email)]
        if account_id:
            sql += " AND account_id = ?"
            params.append(str(account_id))
        if symbol:
            sql += " AND symbol = ?"
            params.append(symbol)
        sql += " ORDER BY closed_at DESC, opened_at DESC"
        if limit:
            sql += " LIMIT ?"
            params.append(int(limit))
        return [row_to_trade(r) for r in self._read(sql, tuple(params))]

    def get_trade(self, user_email: str, trade_id: str):
        rows = self._read(
            "SELECT * FROM trades WHERE user_email = ? AND id = ?",
            (_email(user_email), str(trade_id)),
        )
        return row_to_trade(rows[0]) if rows else None

    def delete_trade(self, user_email: str, trade_id: str) -> None:
        with self._write() as conn:
            conn.execute("DELETE FROM trades WHERE user_email = ? AND id = ?",
                         (_email(user_email), str(trade_id)))

    def delete_all_trades(self, user_email: str, account_id: str | None = None) -> int:
        user_email = _email(user_email)
        with self._write() as conn:
            if account_id:
                cursor = conn.execute(
                    "DELETE FROM trades WHERE user_email = ? AND account_id = ?",
                    (user_email, str(account_id)))
            else:
                cursor = conn.execute("DELETE FROM trades WHERE user_email = ?",
                                      (user_email,))
            return cursor.rowcount

    def count_trades(self, user_email: str, account_id: str | None = None) -> int:
        sql = "SELECT COUNT(*) AS n FROM trades WHERE user_email = ?"
        params: list = [_email(user_email)]
        if account_id:
            sql += " AND account_id = ?"
            params.append(str(account_id))
        rows = self._read(sql, tuple(params))
        return int(rows[0]["n"]) if rows else 0

    def trade_symbols(self, user_email: str) -> list[str]:
        rows = self._read(
            "SELECT DISTINCT symbol FROM trades WHERE user_email = ? ORDER BY symbol",
            (_email(user_email),),
        )
        return [r["symbol"] for r in rows]
