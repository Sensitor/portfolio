"""
A PostgreSQL address as people paste it, and the page that says why it fails.

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

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
