"""
The database layer: isolation between users, and migrations that keep data.

Two things are asserted here, and they are the two the rest of the product
assumes without being able to check:

**No method reaches across users.** Every read, write and delete that touches
user data is called as one user against another user's row, and must come back
empty, False or zero. The list of methods is derived from the `Store` class
itself, so a method added later without a user parameter fails this suite rather
than shipping — which is how the hole this phase closed got in.

**A migration keeps what was there.** The schema gained foreign keys and a CHECK
in version 2, and SQLite cannot add either in place: the tables are rebuilt. A
rebuild is the one operation in this codebase that can lose data, so it is run
against a database built from the previous schema and populated, and every row
is counted back.

Run with:  python tests/test_database.py
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules["streamlit"] = None

WORK = tempfile.mkdtemp(prefix="sensitor-db-test-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(WORK, "main.db")

from sensitor.database import Store                                  # noqa: E402
from sensitor.database.connection import connect, now as _now        # noqa: E402
from sensitor.database.models import SCHEMA_VERSION                  # noqa: E402
from sensitor.trading.models import Direction, Trade                 # noqa: E402

ALICE = "alice@example.com"
BOB = "bob@example.com"

CHECKS = []


def check(name, condition, detail=""):
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}"
          + (f"   {detail}" if detail and not condition else ""))


def a_trade(trade_id="t1", symbol="EURUSD", pnl=100.0) -> Trade:
    return Trade(
        id=trade_id, symbol=symbol, direction=Direction.LONG,
        entry_price=1.1000, size=100_000.0,
        opened_at=datetime(2025, 3, 10, 9, 0),
        exit_price=1.1050, closed_at=datetime(2025, 3, 10, 11, 0),
        stop_loss=1.0950, gross_pnl=pnl, commission=-7.0,
        account_id="acct-1", setups=["bos"], notes="private note",
    )


def fresh_store(name="iso.db") -> Store:
    path = os.path.join(WORK, name)
    if os.path.exists(path):
        os.remove(path)
    return Store(path)


# =============================================================================
# 1. CROSS-USER ISOLATION
# =============================================================================

def test_isolation():
    print("\nCross-user isolation")
    store = fresh_store()

    alice_pf = store.save_portfolio(ALICE, "Core", {"SPY": 0.6, "AGG": 0.4},
                                    notes="alice's plan")
    bob_pf = store.save_portfolio(BOB, "Core", {"QQQ": 1.0})
    alice_snap = store.add_snapshot(ALICE, alice_pf, total_value=100_000.0,
                                    weights={"SPY": 0.6, "AGG": 0.4},
                                    metrics={"sharpe": 1.2})
    store.save_trades(ALICE, [a_trade()])
    store.upsert_account(ALICE, "acct-1", "Alice Live", broker="Broker")

    check("two users can hold the same portfolio name",
          alice_pf != bob_pf and alice_pf > 0 and bob_pf > 0)

    # ── Reads ────────────────────────────────────────────────────────────────
    check("a portfolio cannot be read by another user",
          store.get_portfolio(BOB, alice_pf) is None)
    check("but its owner can", store.get_portfolio(ALICE, alice_pf) is not None)

    check("snapshots cannot be listed by another user",
          store.list_snapshots(BOB, alice_pf) == [])
    check("but its owner can see them",
          len(store.list_snapshots(ALICE, alice_pf)) == 1)
    check("the latest snapshot is scoped too",
          store.latest_snapshot(BOB, alice_pf) is None)

    check("portfolio listings are scoped",
          [p.name for p in store.list_portfolios(BOB)] == ["Core"]
          and store.list_portfolios(BOB)[0].holdings == {"QQQ": 1.0})
    check("summaries are scoped", len(store.portfolio_summaries(BOB)) == 1)

    check("a trade cannot be read by another user",
          store.get_trade(BOB, "t1") is None)
    check("but its owner can", store.get_trade(ALICE, "t1") is not None)
    check("trade listings are scoped", store.list_trades(BOB) == [])
    check("trade counts are scoped", store.count_trades(BOB) == 0)
    check("trade symbols are scoped", store.trade_symbols(BOB) == [])
    check("accounts are scoped", store.list_accounts(BOB) == [])
    check("last_synced_at is scoped",
          store.last_synced_at(BOB, "acct-1") is None)

    # ── Writes ───────────────────────────────────────────────────────────────
    check("a portfolio cannot be renamed by another user",
          store.rename_portfolio(BOB, alice_pf, "Hijacked") is False)
    check("and the name is unchanged",
          store.get_portfolio(ALICE, alice_pf).name == "Core")

    check("a snapshot cannot be written onto another user's portfolio",
          store.add_snapshot(BOB, alice_pf, total_value=1.0, weights={},
                             metrics={}) == -1)
    check("and the history is unchanged",
          len(store.list_snapshots(ALICE, alice_pf)) == 1)

    store.record_sync(BOB, "acct-1", trades=99)
    check("a sync cannot be recorded against another user's account",
          store.last_synced_at(ALICE, "acct-1") is None)

    # ── Deletes ──────────────────────────────────────────────────────────────
    check("a portfolio cannot be deleted by another user",
          store.delete_portfolio(BOB, alice_pf) is False)
    check("and it is still there", store.get_portfolio(ALICE, alice_pf) is not None)

    check("a snapshot cannot be deleted by another user",
          store.delete_snapshot(BOB, alice_snap) is False)
    check("and it is still there",
          len(store.list_snapshots(ALICE, alice_pf)) == 1)

    store.delete_trade(BOB, "t1")
    check("a trade cannot be deleted by another user",
          store.get_trade(ALICE, "t1") is not None)

    removed = store.delete_all_trades(BOB)
    check("delete_all_trades does not reach another user",
          removed == 0 and store.count_trades(ALICE) == 1, f"removed {removed}")

    store.delete_account(BOB, "acct-1")
    check("deleting an account does not reach another user's",
          len(store.list_accounts(ALICE)) == 1)
    check("nor their trades on it", store.count_trades(ALICE) == 1)

    # ── The owner can still do all of it ─────────────────────────────────────
    check("the owner can rename", store.rename_portfolio(ALICE, alice_pf, "Renamed"))
    check("the owner can delete a snapshot",
          store.delete_snapshot(ALICE, alice_snap))
    check("the owner can delete the portfolio",
          store.delete_portfolio(ALICE, alice_pf))
    store.delete_trade(ALICE, "t1")
    check("the owner can delete a trade", store.count_trades(ALICE) == 0)


def test_every_user_method_is_scoped():
    """
    The list of methods is derived from the class, not written down here.

    A method added later that touches user data without taking a user would
    otherwise pass this file unnoticed — which is precisely how the seven
    unscoped portfolio and snapshot methods this phase fixed survived four
    phases of review.
    """
    print("\nEvery user-facing method takes a user")

    import inspect

    exempt = {
        # Plumbing and schema-level operations, not user data access.
        "close", "list_users",
    }
    offenders = []
    for name, method in inspect.getmembers(Store, inspect.isfunction):
        if name.startswith("_") or name in exempt:
            continue
        params = list(inspect.signature(method).parameters)[1:]  # drop self
        if not params:
            continue
        first = params[0]
        if first not in ("user_email", "email"):
            offenders.append(f"{name}({', '.join(params)})")

    check("every public Store method leads with the user",
          not offenders, f"unscoped: {offenders}")

    # And none of them makes the user optional — a default is how a caller
    # forgets to pass one and gets everybody's rows.
    optional = []
    for name, method in inspect.getmembers(Store, inspect.isfunction):
        if name.startswith("_") or name in exempt:
            continue
        signature = inspect.signature(method)
        for param in ("user_email", "email"):
            if (param in signature.parameters
                    and signature.parameters[param].default is not inspect.Parameter.empty):
                optional.append(name)
    check("and none of them defaults it", not optional, f"optional: {optional}")


# =============================================================================
# 2. USER LIFECYCLE
# =============================================================================

def test_user_lifecycle():
    print("\nUser lifecycle")
    store = fresh_store("lifecycle.db")

    pf = store.save_portfolio(ALICE, "Core", {"SPY": 1.0})
    store.add_snapshot(ALICE, pf, total_value=1.0, weights={}, metrics={})
    store.upsert_account(ALICE, "acct-1", "Live")
    store.save_trades(ALICE, [a_trade(), a_trade("t2", "XAUUSD", -50.0)])
    store.save_portfolio(BOB, "Bob's", {"QQQ": 1.0})
    store.save_trades(BOB, [a_trade("b1")])

    check("a write registers the user without being asked",
          store.get_user(ALICE) is not None)
    check("list_users sees both", {u["email"] for u in store.list_users()}
          == {ALICE, BOB})

    export = store.export_user(ALICE)
    check("an export carries the portfolios", len(export["portfolios"]) == 1)
    check("with their snapshots",
          len(export["portfolios"][0]["snapshots"]) == 1)
    check("and the accounts", len(export["accounts"]) == 1)
    check("and the trades", len(export["trades"]) == 2)
    check("and says which schema it came from",
          export["schema_version"] == SCHEMA_VERSION)
    check("an export is JSON-serialisable", bool(json.dumps(export, default=str)))
    check("an export does not reach another user",
          all(t["id"] != "b1" for t in export["trades"]))

    counts = store.delete_user(ALICE)
    check("deletion reports what it removed",
          counts == {"portfolios": 1, "snapshots": 1, "accounts": 1, "trades": 2},
          f"got {counts}")
    check("the user is gone", store.get_user(ALICE) is None)
    check("the portfolios are gone", store.list_portfolios(ALICE) == [])
    check("the snapshots are gone", store.list_snapshots(ALICE, pf) == [])
    check("the trades are gone", store.count_trades(ALICE) == 0)
    check("the accounts are gone", store.list_accounts(ALICE) == [])

    check("the other user is untouched", store.count_trades(BOB) == 1
          and len(store.list_portfolios(BOB)) == 1)

    # Nothing orphaned behind the cascade.
    orphans = store._read(
        "SELECT COUNT(*) AS n FROM snapshots WHERE portfolio_id NOT IN "
        "(SELECT id FROM portfolios)")
    check("no orphaned snapshots remain", int(orphans[0]["n"]) == 0)


# =============================================================================
# 3. CONSTRAINTS
# =============================================================================

def test_constraints():
    print("\nConstraints")
    store = fresh_store("constraints.db")
    store.save_trades(ALICE, [a_trade()])

    version = store._read("PRAGMA user_version")[0][0]
    check("a fresh database is stamped with the current version",
          version == SCHEMA_VERSION, f"got {version}")

    keys = store._read("PRAGMA foreign_keys")[0][0]
    check("foreign keys are enforced on the connection", keys == 1)

    # The CHECK on direction is the only one on `trades`, and it is there
    # because a third value would mean a P&L sign nothing can interpret.
    try:
        with store._write() as conn:
            conn.execute(
                "INSERT INTO trades (id, user_email, symbol, direction, entry_price,"
                " size, opened_at, created_at, updated_at) VALUES"
                " ('bad', ?, 'EURUSD', 'sideways', 1.0, 1.0, ?, ?, ?)",
                (ALICE, _now(), _now(), _now()))
        check("an unknown direction is rejected", False)
    except sqlite3.IntegrityError:
        check("an unknown direction is rejected", True)

    # And the constraints deliberately *not* present: the journal must accept a
    # trade whose numbers are wrong and flag it, rather than refuse an import.
    broken = Trade(id="broken", symbol="EURUSD", direction=Direction.LONG,
                   entry_price=1.1, size=-1.0, opened_at=datetime(2025, 3, 10),
                   exit_price=1.2, closed_at=datetime(2025, 3, 9),
                   stop_loss=1.5)
    store.save_trades(ALICE, [broken])
    check("a trade with impossible numbers is still stored",
          store.get_trade(ALICE, "broken") is not None)

    from sensitor.trading.journal import TradeJournal
    problems = TradeJournal(store.list_trades(ALICE)).validate()
    check("and the journal reports it rather than the database refusing it",
          any(p["id"] == "broken" for p in problems), f"problems {problems}")


# =============================================================================
# 4. MIGRATION FROM THE PREVIOUS SCHEMA
# =============================================================================

V1_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY, tier TEXT NOT NULL DEFAULT 'free',
    display_name TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT NOT NULL,
    name TEXT NOT NULL, holdings TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'simulation', currency TEXT NOT NULL DEFAULT '$',
    notes TEXT, client_name TEXT, created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL, UNIQUE(user_email, name));
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT, portfolio_id INTEGER NOT NULL,
    taken_at TEXT NOT NULL, total_value REAL, weights TEXT NOT NULL,
    metrics TEXT NOT NULL,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS trading_accounts (
    id TEXT NOT NULL, user_email TEXT NOT NULL, name TEXT NOT NULL,
    broker TEXT, currency TEXT NOT NULL DEFAULT 'USD',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    PRIMARY KEY (user_email, id));
CREATE TABLE IF NOT EXISTS trades (
    id TEXT NOT NULL, user_email TEXT NOT NULL, account_id TEXT,
    symbol TEXT NOT NULL, direction TEXT NOT NULL, entry_price REAL NOT NULL,
    exit_price REAL, size REAL NOT NULL, stop_loss REAL, take_profit REAL,
    opened_at TEXT NOT NULL, closed_at TEXT, gross_pnl REAL,
    commission REAL NOT NULL DEFAULT 0, swap REAL NOT NULL DEFAULT 0,
    account_currency TEXT NOT NULL DEFAULT 'USD',
    setups TEXT NOT NULL DEFAULT '[]', mistakes TEXT NOT NULL DEFAULT '[]',
    timeframe TEXT, market_regime TEXT, setup_quality INTEGER,
    confidence INTEGER, entry_reason TEXT, exit_reason TEXT,
    emotion_before TEXT, emotion_during TEXT, emotion_after TEXT,
    discipline INTEGER, notes TEXT, image_pre TEXT, image_post TEXT,
    image_annotated TEXT, source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    PRIMARY KEY (user_email, id));
"""


def build_v1(path: str) -> dict:
    """A populated database at the previous schema, with no `users` rows."""
    conn = sqlite3.connect(path)
    conn.executescript(V1_SCHEMA)
    stamp = "2025-01-01T09:00:00"

    conn.execute(
        "INSERT INTO portfolios (user_email, name, holdings, mode, currency,"
        " notes, client_name, created_at, updated_at)"
        " VALUES (?, 'Legacy', ?, 'simulation', '$', 'kept', NULL, ?, ?)",
        (ALICE, json.dumps({"SPY": 0.7, "AGG": 0.3}), stamp, stamp))
    portfolio_id = conn.execute(
        "SELECT id FROM portfolios WHERE user_email = ?", (ALICE,)).fetchone()[0]
    conn.execute(
        "INSERT INTO snapshots (portfolio_id, taken_at, total_value, weights, metrics)"
        " VALUES (?, ?, 50000.0, ?, ?)",
        (portfolio_id, stamp, json.dumps({"SPY": 0.7}), json.dumps({"sharpe": 0.9})))
    conn.execute(
        "INSERT INTO trading_accounts (id, user_email, name, broker, currency,"
        " created_at, updated_at) VALUES ('old-acct', ?, 'Old', 'B', 'USD', ?, ?)",
        (ALICE, stamp, stamp))
    for i, email in enumerate((ALICE, ALICE, BOB)):
        conn.execute(
            "INSERT INTO trades (id, user_email, account_id, symbol, direction,"
            " entry_price, exit_price, size, opened_at, closed_at, gross_pnl,"
            " setups, notes, source, created_at, updated_at)"
            " VALUES (?, ?, 'old-acct', 'EURUSD', 'long', 1.1, 1.2, 1.0, ?, ?,"
            " 100.0, ?, 'legacy note', 'manual', ?, ?)",
            (f"legacy-{i}", email, stamp, stamp, json.dumps(["bos"]), stamp, stamp))
    conn.commit()
    conn.close()
    return {"portfolio_id": portfolio_id}


def test_migration():
    print("\nMigration from the previous schema")

    path = os.path.join(WORK, "legacy.db")
    if os.path.exists(path):
        os.remove(path)
    info = build_v1(path)

    before = sqlite3.connect(path)
    check("the old database has no users rows",
          before.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0)
    check("and no version stamp",
          before.execute("PRAGMA user_version").fetchone()[0] == 0)
    check("and no foreign key on trades",
          before.execute("PRAGMA foreign_key_list(trades)").fetchall() == [])
    before.close()

    store = Store(path)

    check("the migrated database is stamped",
          store._read("PRAGMA user_version")[0][0] == SCHEMA_VERSION)
    check("trades now reference users",
          any(r["table"] == "users"
              for r in store._read("PRAGMA foreign_key_list(trades)")))
    check("portfolios now reference users",
          any(r["table"] == "users"
              for r in store._read("PRAGMA foreign_key_list(portfolios)")))

    # Nothing may be lost. This is the assertion the rebuild exists to satisfy.
    check("the portfolio survived", len(store.list_portfolios(ALICE)) == 1)
    portfolio = store.list_portfolios(ALICE)[0]
    check("with its holdings", portfolio.holdings == {"SPY": 0.7, "AGG": 0.3})
    check("and its notes", portfolio.notes == "kept")
    check("the snapshot survived",
          len(store.list_snapshots(ALICE, info["portfolio_id"])) == 1)
    check("with its metrics",
          store.latest_snapshot(ALICE, info["portfolio_id"]).metrics == {"sharpe": 0.9})
    check("the account survived", len(store.list_accounts(ALICE)) == 1)
    check("alice's trades survived", store.count_trades(ALICE) == 2,
          f"got {store.count_trades(ALICE)}")
    check("bob's trade survived", store.count_trades(BOB) == 1)
    trade = store.get_trade(ALICE, "legacy-0")
    check("with its setups", trade.setups == ["bos"])
    check("and its notes", trade.notes == "legacy note")

    # Users were backfilled from the rows that referenced them, which is what
    # makes the new foreign key satisfiable at all.
    check("users were backfilled from the existing rows",
          {u["email"] for u in store.list_users()} == {ALICE, BOB})

    # The column added by the previous phase is present whether or not the old
    # file had received it.
    check("the raw column is present",
          "raw" in [r["name"] for r in store._read("PRAGMA table_info(trades)")])
    check("and the sync columns are",
          {"last_synced_at", "last_sync_trades"} <=
          {r["name"] for r in store._read("PRAGMA table_info(trading_accounts)")})

    # Indexes dropped with the rebuilt tables must come back.
    indexes = {r["name"] for r in
               store._read("SELECT name FROM sqlite_master WHERE type = 'index'")}
    check("the indexes were recreated",
          {"idx_trades_user", "idx_portfolios_user"} <= indexes,
          f"got {sorted(indexes)}")

    # The trap this migration hit: renaming `portfolios` aside repointed the
    # snapshots foreign key at the scratch table, and dropping it left the
    # reference dangling — a database that opens fine and fails on the first
    # cascade.
    snapshot_fks = store._read("PRAGMA foreign_key_list(snapshots)")
    check("snapshots still reference portfolios, not a scratch table",
          any(r["table"] == "portfolios" for r in snapshot_fks),
          f"points at {[r['table'] for r in snapshot_fks]}")
    check("no reference is left dangling",
          store._read("PRAGMA foreign_key_check") == [])

    check("no migration scratch tables are left behind",
          not any(r["name"].startswith("_migrating_") for r in
                  store._read("SELECT name FROM sqlite_master WHERE type = 'table'")))

    # Reopening must be a no-op, not a second migration.
    store.close()
    again = Store(path)
    check("reopening does not migrate twice", again.count_trades(ALICE) == 2)
    check("and the version is unchanged",
          again._read("PRAGMA user_version")[0][0] == SCHEMA_VERSION)

    # The cascade the migration added must now actually work.
    again.delete_user(ALICE)
    check("the new cascade removes the migrated rows",
          again.count_trades(ALICE) == 0 and again.list_portfolios(ALICE) == [])
    check("and leaves the other user alone", again.count_trades(BOB) == 1)


def test_fresh_database_is_not_migrated():
    print("\nA fresh database")
    path = os.path.join(WORK, "brand-new.db")
    if os.path.exists(path):
        os.remove(path)

    store = Store(path)
    check("is stamped at the current version",
          store._read("PRAGMA user_version")[0][0] == SCHEMA_VERSION)
    check("has no scratch tables",
          not any(r["name"].startswith("_migrating_") for r in
                  store._read("SELECT name FROM sqlite_master WHERE type='table'")))
    store.save_trades(ALICE, [a_trade()])
    check("and works", store.count_trades(ALICE) == 1)


def main() -> int:
    for test in (test_isolation, test_every_user_method_is_scoped,
                 test_user_lifecycle, test_constraints, test_migration,
                 test_fresh_database_is_not_migrated):
        test()

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
