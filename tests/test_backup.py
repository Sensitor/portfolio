"""
The whole database saved to a file, and restored from it.

    python tests/test_backup.py
    SENSITOR_TEST_PG=postgresql://… python tests/test_backup.py   # restores into PostgreSQL too

A store is filled with a little of everything a member writes, dumped, and
restored into an empty database; every table must come back row for row.
"""

from __future__ import annotations

import gzip
import json
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensitor.database import Store  # noqa: E402
from sensitor.database import backup as B  # noqa: E402
from sensitor.database.models import TABLES  # noqa: E402
from sensitor.trading.models import Direction, Trade  # noqa: E402

WORK = tempfile.mkdtemp(prefix="sensitor-backup-")
TEST_PG = os.getenv("SENSITOR_TEST_PG", "")
CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def filled(path: str) -> Store:
    store = Store(path)
    for email in ("alice@example.com", "bob@example.com"):
        store.upsert_user(email)
        store.set_password_hash(email, "scrypt$fake-hash-for-the-test")
    store.set_tier("alice@example.com", "premium")
    pid = store.save_portfolio("alice@example.com", "Prudent", {"SPY": 0.6, "GLD": 0.4}, notes="à revoir")
    store.add_snapshot("alice@example.com", pid, total_value=10_000.0, weights={"SPY": 0.6, "GLD": 0.4},
                       metrics={"volatility": 0.12})
    store.save_workspace("alice@example.com", {"SPY": 1.0}, mode="real", quantities={"SPY": 10.0},
                         manual_prices={"APPARTEMENT": {"price": 250000.0, "currency": "EUR", "at": "2026-10-30"}})
    store.save_trades("alice@example.com", [Trade(
        id="t1", symbol="EURUSD", direction=Direction.LONG, entry_price=1.1, size=100_000.0,
        opened_at=datetime(2026, 10, 1, 9), exit_price=1.105, closed_at=datetime(2026, 10, 1, 11),
        stop_loss=1.095, gross_pnl=500.0, commission=-7.0, setups=["ote"], notes="note privée")])
    store.mark_lesson_complete("alice@example.com", "la-monnaie", "fonctions-monnaie")
    store.record_quiz_attempt("bob@example.com", "check-fvg", version=1, correct=3, total=4, passed=True,
                              responses={"q1": "a"})
    store.add_journal_entry("bob@example.com", kind="free", body="Rester patient.", mood=4)
    store.save_trading_plan("alice@example.com", {"risk_pct": 1.0})
    return store


def snapshot(store: Store) -> dict:
    return {t: sorted(json.dumps([r[c] for c in B._table_columns(store, t)], default=str)  # noqa: SLF001
                      for r in store._read(f"SELECT * FROM {t}"))           # noqa: SLF001
            for t in TABLES}


def main() -> int:
    print("\nDump")
    source = filled(os.path.join(WORK, "source.db"))
    path = os.path.join(WORK, "sensitor-backup-test.json.gz")
    counts = B.write(source, path)
    check("every table is in the file, with its rows",
          set(counts) == set(TABLES) and counts["users"] == 2 and counts["trades"] == 1 and counts["snapshots"] == 1,
          str(counts))
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        raw = json.load(handle)
    check("the file says what it is and which schema it was taken at",
          raw["format"] == B.FORMAT and raw["schema_version"] and raw["created_at"])

    print("\nRestore into an empty SQLite database")
    target = Store(os.path.join(WORK, "target.db"))
    written = B.restore(target, B.read(path))
    check("every row comes back, table by table", snapshot(target) == snapshot(source), str(written))
    check("the premium level and the private note survive",
          target.get_user("alice@example.com")["tier"] == "premium"
          and target.get_trade("alice@example.com", "t1").notes == "note privée")
    new_id = target.save_portfolio("bob@example.com", "Après restauration", {"SPY": 1.0})
    check("a new row after the restore gets a new identifier", new_id > max(r["id"] for r in target._read(  # noqa: SLF001
        "SELECT id FROM portfolios WHERE user_email = 'alice@example.com'")))

    print("\nWhat a restore refuses")
    try:
        B.restore(target, B.read(path))
        refused = False
    except B.BackupError as exc:
        refused = "pas vide" in str(exc)
    check("a database that is not empty", refused)
    other = os.path.join(WORK, "not-a-backup.json.gz")
    with gzip.open(other, "wt", encoding="utf-8") as handle:
        json.dump({"hello": "world"}, handle)
    for label, file in (("a file that is not a Sensitor backup", other),
                        ("a file that is not gzipped JSON", __file__)):
        try:
            B.read(file)
            ok = False
        except B.BackupError:
            ok = True
        check(label, ok)
    newer = dict(raw, schema_version=raw["schema_version"] + 1)
    future = os.path.join(WORK, "future.json.gz")
    with gzip.open(future, "wt", encoding="utf-8") as handle:
        json.dump(newer, handle)
    try:
        B.read(future)
        ok = False
    except B.BackupError as exc:
        ok = "plus récente" in str(exc)
    check("a backup taken by a newer schema", ok)

    print("\nThe command line")
    out = os.path.join(WORK, "sensitor-backup-cli.json.gz")
    check("dump then restore through the command", B.main(["dump", out, "--db", os.path.join(WORK, "source.db")]) == 0
          and B.main(["restore", out, "--db", os.path.join(WORK, "cli-target.db")]) == 0
          and snapshot(Store(os.path.join(WORK, "cli-target.db"))) == snapshot(source))

    if TEST_PG:
        print("\nRestore into PostgreSQL, and back")
        pg = Store(TEST_PG)
        with pg._write() as conn:                                    # noqa: SLF001
            for table in reversed(list(TABLES)):
                conn.execute(f"DELETE FROM {table}")
        B.restore(pg, B.read(path))
        check("every row comes back in PostgreSQL", snapshot(pg) == snapshot(source))
        pid = pg.save_portfolio("bob@example.com", "Après restauration", {"SPY": 1.0})
        check("the identifier counters follow the restored rows", pid > 1, str(pid))
        back = os.path.join(WORK, "sensitor-backup-from-pg.json.gz")
        B.write(pg, back)
        sqlite_again = Store(os.path.join(WORK, "from-pg.db"))
        B.restore(sqlite_again, B.read(back))
        check("a PostgreSQL dump restores into SQLite", snapshot(sqlite_again) == snapshot(pg))
    else:
        print("\n(SENSITOR_TEST_PG not set: the PostgreSQL restore is skipped)")

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
