"""
Account lifecycle: password reset, address verification, e-mail, the operator
command, data export and deletion, and the v6 → v7 upgrade.

No network: the mailer is given a fake transport, and SMTP settings are only
ever read from a test environment.

Run with:  python tests/test_accounts.py
"""

from __future__ import annotations

import io
import os
import sqlite3
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules["streamlit"] = None

WORK = tempfile.mkdtemp(prefix="sensitor-accounts-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(WORK, "accounts.db")
for key in ("SENSITOR_SMTP_HOST", "SENSITOR_PUBLIC_URL"):
    os.environ.pop(key, None)

from sensitor.core import admin, mailer  # noqa: E402
from sensitor.core.auth import Auth  # noqa: E402
from sensitor.core.security import token_fingerprint  # noqa: E402
from sensitor.database import Store  # noqa: E402
from sensitor.database.models import SCHEMA_VERSION  # noqa: E402

FAILURES: list[str] = []
COUNT = 0
PASSWORD = "correct-horse-battery"


def check(name: str, condition: bool, detail: str = "") -> None:
    global COUNT
    COUNT += 1
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"  {detail}" if not condition else ""))
    if not condition:
        FAILURES.append(f"{name}: {detail}")


class FakeTransport:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


def test_reset(store: Store) -> None:
    print("\nPassword reset")
    auth = Auth(store, mode="multi")
    session = auth.sign_up("alice@example.com", PASSWORD).token

    check("no token for an unknown address", auth.request_password_reset("nobody@example.com") is None)
    check("no token in single-user mode",
          Auth(store, mode="single").request_password_reset("alice@example.com") is None)
    first = auth.request_password_reset("Alice@Example.com ")
    check("a token for a real account, whatever the case", bool(first))
    row = store.account_token(token_fingerprint(first), "reset")
    check("only the fingerprint is stored", row is not None and first not in str(row))

    second = auth.request_password_reset("alice@example.com")
    check("asking again retires the earlier link",
          not auth.reset_password(first, "another-strong-one"))

    weak = auth.reset_password(second, "short")
    check("a weak new password is refused", weak.reason == "weak_password")
    result = auth.reset_password(second, "another-strong-one")
    check("…without spending the link", bool(result))
    check("the new password works", bool(auth.sign_in("alice@example.com", "another-strong-one")))
    check("the old one does not", not auth.sign_in("alice@example.com", PASSWORD))
    check("every earlier session was revoked", auth.resolve(session) is None)
    check("the reset signs the person in", auth.resolve(result.token) == "alice@example.com")
    check("a link works once", auth.reset_password(second, "yet-another-one").reason == "invalid_token")
    check("a forged token is refused", auth.reset_password("forged", "yet-another-one").reason == "invalid_token")

    expired = auth.request_password_reset("alice@example.com")
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(timespec="seconds")
    with store._write() as conn:
        conn.execute("UPDATE account_tokens SET expires_at = ? WHERE fingerprint = ?",
                     (past, token_fingerprint(expired)))
    check("an expired link is refused", auth.reset_password(expired, "yet-another-one").reason == "invalid_token")
    verify = auth.request_verification("alice@example.com")
    check("a verification token cannot reset a password",
          auth.reset_password(verify, "yet-another-one").reason == "invalid_token")


def test_verification(store: Store) -> None:
    print("\nAddress verification")
    auth = Auth(store, mode="multi")
    auth.sign_up("bob@example.com", PASSWORD)
    check("a new account is not verified", not store.get_user("bob@example.com")["email_verified_at"])
    token = auth.request_verification("bob@example.com")
    result = auth.verify_email(token)
    check("the link verifies the address", bool(result) and result.email == "bob@example.com")
    check("the date is recorded", bool(store.get_user("bob@example.com")["email_verified_at"]))
    check("the link works once", not auth.verify_email(token))
    check("no token for an unknown address", auth.request_verification("ghost@example.com") is None)


def test_mailer() -> None:
    print("\nE-mail")
    check("not configured without a host", not mailer.configured())
    try:
        mailer.send("a@example.com", "s", "b")
        check("sending without SMTP raises", False)
    except mailer.MailError:
        check("sending without SMTP raises", True)
    fake = FakeTransport()
    mailer.send("a@example.com", "Sujet", "Corps", transport=fake)
    message = fake.sent[0]
    check("the transport receives the message",
          message["To"] == "a@example.com" and message["Subject"] == "Sujet")
    os.environ["SENSITOR_PUBLIC_URL"] = "https://sensitor.example/"
    check("links use the public address", mailer.link("reset", "abc") ==
          "https://sensitor.example/?page=reset&token=abc")
    os.environ["SENSITOR_SMTP_HOST"] = "smtp.example.com"
    os.environ["SENSITOR_SMTP_PORT"] = "465"
    cfg = mailer.config()
    check("configuration is read from the environment", mailer.configured() and cfg.port == 465)
    os.environ.pop("SENSITOR_SMTP_HOST")
    os.environ.pop("SENSITOR_SMTP_PORT")
    body = mailer.reset_body("https://x/?page=reset&token=t")
    check("the reset e-mail carries the link and its limits",
          "https://x/?page=reset&token=t" in body and "l'heure" in body and "qu'une fois" in body)
    check("the e-mails use no em dash", "—" not in body + mailer.verify_body("u"))


def test_admin(store: Store) -> None:
    print("\nOperator command")
    out = io.StringIO()
    with redirect_stdout(out):
        code = admin.main(["reset-link", "bob@example.com"])
    line = out.getvalue().strip()
    check("prints a reset link", code == 0 and line.startswith("https://sensitor.example/?page=reset&token="))
    token = line.rsplit("=", 1)[1]
    check("the printed link works", bool(Auth(store, mode="multi").reset_password(token, "brand-new-pass")))
    out = io.StringIO()
    with redirect_stdout(out):
        code = admin.main(["reset-link", "ghost@example.com"])
    check("nothing printed for an unknown address", code == 1 and "token" not in out.getvalue())
    with redirect_stdout(io.StringIO()):
        check("bad usage exits 2", admin.main([]) == 2)


def test_export_and_delete(store: Store) -> None:
    print("\nExport and deletion")
    export = store.export_user("bob@example.com")
    check("the export carries no credential",
          not {"password_hash", "failed_logins", "locked_until"} & set(export["user"]))
    check("the export keeps the address", export["user"]["email"] == "bob@example.com")
    store.delete_user("bob@example.com")
    left = store._read("SELECT COUNT(*) AS n FROM account_tokens WHERE user_email = ?",
                       ("bob@example.com",))[0]["n"]
    check("deleting an account removes its tokens", left == 0)


def test_upgrade() -> None:
    print("\nUpgrading a version-6 database")
    path = os.path.join(WORK, "v6.db")
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (email TEXT PRIMARY KEY, tier TEXT NOT NULL DEFAULT 'free',
            display_name TEXT, password_hash TEXT, last_login_at TEXT,
            failed_logins INTEGER NOT NULL DEFAULT 0, locked_until TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        INSERT INTO users (email, created_at, updated_at) VALUES ('old@example.com', 'x', 'x');
        PRAGMA user_version = 6;
    """)
    conn.commit()
    conn.close()
    store = Store(path)
    check("the user survives", store.get_user("old@example.com") is not None)
    check("the new column is there", "email_verified_at" in store.get_user("old@example.com"))
    check("tokens can be stored at once",
          bool(Auth(store, mode="multi").request_verification("old@example.com")))
    check("the journal table is there after the upgrade",
          store.add_journal_entry("old@example.com", kind="free", body="Première note.") > 0)
    check("the database is at the current version",
          store._read("PRAGMA user_version")[0][0] == SCHEMA_VERSION == 11)

    print("\nUpgrading a version-8 database (journal without routines)")
    path = os.path.join(WORK, "v8.db")
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (email TEXT PRIMARY KEY, tier TEXT NOT NULL DEFAULT 'free',
            display_name TEXT, password_hash TEXT, last_login_at TEXT,
            failed_logins INTEGER NOT NULL DEFAULT 0, locked_until TEXT, email_verified_at TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        INSERT INTO users (email, created_at, updated_at) VALUES ('old@example.com', 'x', 'x');
        CREATE TABLE journal_entries (id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE ON UPDATE CASCADE,
            kind TEXT NOT NULL CHECK (kind IN ('pre', 'post', 'free')),
            mood INTEGER CHECK (mood IS NULL OR mood BETWEEN 1 AND 5),
            prompt TEXT NOT NULL DEFAULT '', body TEXT NOT NULL CHECK (length(body) > 0),
            created_at TEXT NOT NULL);
        INSERT INTO journal_entries (user_email, kind, body, created_at)
            VALUES ('old@example.com', 'pre', 'Une note d''avant.', '2026-10-01T08:00:00+00:00');
        PRAGMA user_version = 8;
    """)
    conn.commit()
    conn.close()
    store = Store(path)
    old = store.journal_entries("old@example.com")
    check("the old note survives, with no routine", len(old) == 1 and old[0]["checks"] is None)
    store.add_journal_entry("old@example.com", kind="pre", body="Nouvelle note.", checks=["etat"])
    check("a new note stores its routine", store.journal_entries("old@example.com")[0]["checks"] == ["etat"])
    check("the database is at the current version", store._read("PRAGMA user_version")[0][0] == SCHEMA_VERSION)

    print("\nUpgrading a version-9 database (no roles, no journal review)")
    path = os.path.join(WORK, "v9.db")
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (email TEXT PRIMARY KEY, tier TEXT NOT NULL DEFAULT 'free',
            display_name TEXT, password_hash TEXT, last_login_at TEXT,
            failed_logins INTEGER NOT NULL DEFAULT 0, locked_until TEXT, email_verified_at TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        INSERT INTO users (email, created_at, updated_at) VALUES ('old@example.com', 'x', 'x');
        INSERT INTO users (email, created_at, updated_at) VALUES ('team@example.com', 'x', 'x');
        PRAGMA user_version = 9;
    """)
    conn.commit()
    conn.close()
    store = Store(path)
    check("every existing account starts as a member, not a coach",
          store.get_user("old@example.com")["role"] == "" and not store.is_coach("team@example.com"))
    store.set_role("team@example.com", "coach")
    check("a coach can be named after the upgrade", store.is_coach("team@example.com"))
    store.save_trading_plan("old@example.com", {"risk_pct": 1.0})
    request = store.create_review_request("old@example.com", trade_id="t", trade={"id": "t"},
                                          auto_review={"checks": []}, plan=None, question="Question ?")
    check("the plan and review tables are there",
          store.get_trading_plan("old@example.com") == {"risk_pct": 1.0}
          and [r["id"] for r in store.coach_queue("team@example.com")] == [request])
    check("the trading room's table is there, empty", store.market_sessions() == [])
    check("the database is at the current version", store._read("PRAGMA user_version")[0][0] == SCHEMA_VERSION)


def test_limits(store: Store) -> None:
    print("\nLimits on e-mails and on the lockout")
    from datetime import datetime, timedelta, timezone
    from sensitor.core import auth as A
    auth = Auth(store, mode="multi")
    auth.sign_up("quota@example.com", PASSWORD)
    tokens = [auth.request_password_reset("quota@example.com") for _ in range(A.MAX_TOKENS_PER_HOUR + 1)]
    check("three reset e-mails an hour per address, then none", all(tokens[:-1]) and tokens[-1] is None,
          str([bool(t) for t in tokens]))
    check("the last link sent still works", bool(auth.reset_password(tokens[-2], "un-nouveau-mot-de-passe")))
    check("the operator's command is not limited", bool(auth.request_password_reset("quota@example.com", limited=False)))
    verifies = [auth.request_verification("quota@example.com") for _ in range(A.MAX_TOKENS_PER_HOUR + 1)]
    check("the same for the verification e-mail", all(verifies[:-1]) and verifies[-1] is None)

    auth.sign_up("verrou@example.com", PASSWORD)
    for _ in range(A.MAX_FAILED_LOGINS):
        auth.sign_in("verrou@example.com", "pas-le-bon")
    check("the account is locked after the failures", auth.sign_in("verrou@example.com", PASSWORD).reason == "locked")
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(timespec="seconds")
    with store._write() as conn:                                     # noqa: SLF001
        conn.execute("UPDATE users SET locked_until = ? WHERE email = ?", (past, "verrou@example.com"))
    auth.sign_in("verrou@example.com", "pas-le-bon")
    after = store.credential("verrou@example.com")
    check("once the lock has run out, one more failure counts as the first, not a new lock",
          after["failed_logins"] == 1 and not auth._locked_until(after))  # noqa: SLF001
    check("and the owner signs in", bool(auth.sign_in("verrou@example.com", PASSWORD)))


def test_check() -> None:
    print("\nThe pre-launch check")
    saved = {k: os.environ.get(k) for k in ("SENSITOR_AUTH", "SENSITOR_SMTP_HOST", "SENSITOR_PUBLIC_URL")}
    try:
        os.environ.update(SENSITOR_AUTH="multi", SENSITOR_SMTP_HOST="smtp.example.com",
                          SENSITOR_PUBLIC_URL="https://sensitor.example")
        results = dict((what, ok) for ok, what in admin.checks())
        check("passwords, e-mails and the https address are reported as done",
              results.get("Comptes avec mot de passe (SENSITOR_AUTH=multi)") is True
              and results.get("Envoi d'e-mails configuré (SENSITOR_SMTP_*)") is True
              and results.get("Adresse publique https://sensitor.example") is True)
        check("a local SQLite file is reported as not durable", any("SQLite" in w and not ok for w, ok in results.items()))
        check("the legal pages left to complete are reported", any("Pages légales" in w and not ok for w, ok in results.items()))
        with redirect_stdout(io.StringIO()):
            check("the command exits 1 while anything is missing", admin.main(["check"]) == 1)
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main() -> int:
    store = Store(os.environ["SENSITOR_DB_PATH"])
    test_reset(store)
    test_verification(store)
    test_mailer()
    test_admin(store)
    test_limits(store)
    test_check()
    test_export_and_delete(store)
    test_upgrade()
    print(f"\n{COUNT} checks, {len(FAILURES)} failures")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
