"""
A PostgreSQL address as people paste it, the page that says why it fails, and
a connection the server drops.

    python tests/test_db_errors.py

No server is reached: the address used for the page points at a Supabase host
that does not exist, so the connection fails the way an IPv6-only address does
from Streamlit Cloud, and the page must explain it without ever showing the
password.
"""

from __future__ import annotations

import os
import sys
from html import unescape

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECRET = "Un-secret-de-test@"
os.environ["SENSITOR_DB_URL"] = f"postgresql://postgres:{SECRET}@db.nexistepas-sensitor-test.supabase.co:5432/postgres"
os.environ["SENSITOR_AUTH"] = "multi"

from streamlit.testing.v1 import AppTest  # noqa: E402

TEST_PG = os.getenv("SENSITOR_TEST_PG", "")

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sensitor_app.py")
CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def main() -> int:
    from psycopg2.extensions import parse_dsn
    from sensitor.database.postgres import explain, normalise_url

    print("\nAn address as it is pasted")
    cases = {
        "postgresql://postgres:mot@@db.x.supabase.co:5432/postgres": ("postgres", "mot@", "db.x.supabase.co"),
        "postgresql://u:p:q/r@h:5432/db": ("u", "p:q/r", "h"),
        "postgresql://u:a%40b@h/db?sslmode=require": ("u", "a@b", "h"),
        "postgresql://postgres.ref:simple@aws-0-eu-west-3.pooler.supabase.com:5432/postgres":
            ("postgres.ref", "simple", "aws-0-eu-west-3.pooler.supabase.com"),
    }
    for raw, (user, password, host) in cases.items():
        dsn = parse_dsn(normalise_url(raw))
        check(f"read as user « {user} », host « {host} »",
              (dsn.get("user"), dsn.get("password"), dsn.get("host")) == (user, password, host), str(dsn))
    check("an address without a password, or not a URL, is left as it is",
          normalise_url("postgresql://h/db") == "postgresql://h/db" and normalise_url("data.db") == "data.db")

    print("\nWhy it fails, without the secret")
    url = os.environ["SENSITOR_DB_URL"]
    direct = explain(Exception('could not translate host name "db.x.supabase.co" to address'), url)
    check("the direct Supabase address is named for what it is: IPv6 only, use the Session pooler",
          "IPv6" in direct and "Session pooler" in direct)
    refused = explain(Exception('FATAL:  password authentication failed for user "postgres"'),
                      "postgresql://postgres:x@aws-0.pooler.supabase.com:5432/postgres")
    check("a refused password says so", "Le mot de passe est refusé" in refused)
    leaked = explain(Exception(f"something echoed {SECRET} back"), url)
    check("a message that would echo the password is replaced", SECRET not in leaked and "Exception" in leaked)

    print("\nThe account page")
    app = AppTest.from_file(APP, default_timeout=120)
    app.session_state["ac_route"] = {"page": "account"}
    app.run()
    shown = unescape(" ".join([e.value for e in app.error] + [m.value for m in app.markdown]))
    check("the page says the database is unavailable, and why", not app.exception
          and "La base de données est indisponible" in shown and "Session pooler" in shown,
          str(app.exception[0].value)[:200] if app.exception else shown[-400:])
    check("the password appears nowhere on the page", SECRET not in shown and SECRET.rstrip("@") not in shown)

    print("\nA connection the server drops (simulated)")
    simulated_drops()
    if TEST_PG:
        print("\nA connection the server drops (real PostgreSQL)")
        real_drops()
    else:
        print("\n(SENSITOR_TEST_PG not set: the real PostgreSQL checks are skipped)")

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


class _FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.description, self.rowcount = (("n",),), 1

    def execute(self, sql, params=()):
        import psycopg2
        if self.conn.fail_next:
            self.conn.fail_next = False
            self.conn.closed = 2
            raise psycopg2.OperationalError("server closed the connection unexpectedly")
        self.conn.statements.append(sql)

    def fetchall(self):
        return [(1,)]


class _FakeConn:
    def __init__(self, log):
        self.closed, self.fail_next, self.statements, self.autocommit = 0, False, [], True
        log.append(self)

    def cursor(self):
        return _FakeCursor(self)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        self.closed = 1


def simulated_drops() -> None:
    import psycopg2
    from sensitor.database.postgres import Connection

    opened: list = []
    conn = Connection("postgresql://u:p@h/db", connect=lambda: _FakeConn(opened))
    conn.execute("SELECT 1")
    conn.end_read()
    opened[-1].fail_next = True
    conn.execute("SELECT 2")
    check("a read on a connection the server closed reopens it and succeeds",
          len(opened) == 2 and opened[-1].statements == ["SELECT 2"] and conn.reconnects == 1)
    conn.end_read()

    conn.execute("INSERT INTO t VALUES (1)")
    opened[-1].fail_next = True
    try:
        conn.execute("INSERT INTO t VALUES (2)")
        raised = False
    except psycopg2.OperationalError:
        raised = True
    check("a drop in the middle of a write is raised, never replayed on a new connection",
          raised and len(opened) == 2)
    conn.rollback()
    conn.execute("INSERT INTO t VALUES (3)")
    check("the next unit of work gets a fresh connection", len(opened) == 3
          and opened[-1].statements == ["INSERT INTO t VALUES (3)"])


def real_drops() -> None:
    import psycopg2
    from sensitor.database import Store

    store = Store(TEST_PG)
    store.upsert_user("coupure@example.com")

    def kill() -> None:
        pid = store._conn._conn.get_backend_pid()                 # noqa: SLF001
        admin = psycopg2.connect(TEST_PG)
        admin.autocommit = True
        admin.cursor().execute("SELECT pg_terminate_backend(%s)", (pid,))
        admin.close()

    before = store._conn.reconnects                               # noqa: SLF001
    kill()
    check("after the server ends the connection, the next read works without a restart",
          store.get_user("coupure@example.com") is not None and store._conn.reconnects == before + 1)  # noqa: SLF001
    kill()
    store.upsert_user("coupure-2@example.com")
    check("and so does the next write", store.get_user("coupure-2@example.com") is not None)
    idle = psycopg2.connect(TEST_PG)
    cur = idle.cursor()
    cur.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction' AND pid = %s",
                (store._conn._conn.get_backend_pid(),))                # noqa: SLF001
    stuck = cur.fetchone()[0]
    idle.close()
    check("a read leaves no transaction open on the shared connection", stuck == 0, str(stuck))
    try:
        store._read("SELECT * FROM no_such_table")                # noqa: SLF001
    except Exception:                                             # noqa: BLE001
        pass
    check("a failed read does not block the next statements", store.get_user("coupure@example.com") is not None)


if __name__ == "__main__":
    raise SystemExit(main())
