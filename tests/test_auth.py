"""
Authentication: the crypto primitives, both modes, and what an attacker cannot do.

`streamlit` is poisoned before the imports — authentication must be reusable by
the API, which has no UI.

The interesting assertions are the negative ones. It is easy to check that a
correct password signs in; what matters is that a wrong one does not, that a
revoked session stops working immediately, that a password change ends every
other session, and that one account's token cannot reach another's data.

Run with:  python tests/test_auth.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules["streamlit"] = None

WORK = tempfile.mkdtemp(prefix="sensitor-auth-test-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(WORK, "auth.db")

from sensitor.core import auth as auth_module                        # noqa: E402
from sensitor.core.auth import Auth, MULTI, SINGLE, auth_mode        # noqa: E402
from sensitor.core.security import (                                 # noqa: E402
    MIN_PASSWORD_LENGTH, PasswordError, check_password_strength, hash_password,
    needs_rehash, new_token, token_fingerprint, tokens_match, verify_password,
)
from sensitor.database import Store                                  # noqa: E402
from sensitor.trading.models import Direction, Trade                 # noqa: E402

ALICE = "alice@example.com"
BOB = "bob@example.com"
GOOD_PASSWORD = "correct-horse-battery"

CHECKS = []


def check(name, condition, detail=""):
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}"
          + (f"   {detail}" if detail and not condition else ""))


def fresh(name, mode=MULTI, **kwargs) -> tuple[Auth, Store]:
    path = os.path.join(WORK, name)
    if os.path.exists(path):
        os.remove(path)
    store = Store(path)
    return Auth(store, mode=mode, **kwargs), store


def a_trade(trade_id="t1") -> Trade:
    return Trade(id=trade_id, symbol="EURUSD", direction=Direction.LONG,
                 entry_price=1.1, size=1.0, opened_at=datetime(2025, 3, 10),
                 exit_price=1.2, closed_at=datetime(2025, 3, 10, 12),
                 gross_pnl=100.0, notes="private")


# =============================================================================
# 1. PRIMITIVES
# =============================================================================

def test_password_hashing():
    print("\nPassword hashing")

    stored = hash_password(GOOD_PASSWORD)
    check("a hash names its scheme", stored.startswith("scrypt$"))
    check("the plaintext is not in it", GOOD_PASSWORD not in stored)
    check("the right password verifies", verify_password(GOOD_PASSWORD, stored))
    check("a wrong password does not", not verify_password("wrong", stored))
    check("an empty password does not", not verify_password("", stored))

    # The salt is what stops one cracked hash from cracking every reuse of the
    # same password across accounts.
    other = hash_password(GOOD_PASSWORD)
    check("the same password hashes differently each time", stored != other)
    check("and both still verify", verify_password(GOOD_PASSWORD, other))

    check("a missing hash verifies nothing",
          not verify_password(GOOD_PASSWORD, None))
    check("a malformed hash returns False rather than raising",
          not verify_password(GOOD_PASSWORD, "not-a-hash"))
    check("an unknown scheme is refused",
          not verify_password(GOOD_PASSWORD, "md5$1$2$3$aa$bb"))

    # Parameters travel with the hash, so raising the cost later does not lock
    # anyone out of their own account.
    weak = hash_password(GOOD_PASSWORD, n=1024)
    check("an old, cheaper hash still verifies", verify_password(GOOD_PASSWORD, weak))
    check("and is marked for rehashing", needs_rehash(weak))
    check("a current hash is not", not needs_rehash(stored))
    check("a malformed hash is", needs_rehash("nonsense"))


def test_password_strength():
    print("\nPassword strength")

    try:
        check_password_strength("short")
        check("a short password is refused", False)
    except PasswordError as exc:
        check("a short password is refused", str(MIN_PASSWORD_LENGTH) in str(exc))

    try:
        check_password_strength(" " + GOOD_PASSWORD)
        check("a padded password is refused", False)
    except PasswordError:
        check("a padded password is refused", True)

    check_password_strength(GOOD_PASSWORD)
    check("a reasonable password is accepted", True)

    # A length floor and nothing else, on purpose: composition rules reliably
    # produce "Password1!" and nothing else.
    check_password_strength("aaaaaaaaaaaaaaaaaaaa")
    check("length is the only rule", True)


def test_tokens():
    print("\nSession tokens")

    token = new_token()
    check("tokens are long", len(token) >= 40, f"len {len(token)}")
    check("tokens are unique", new_token() != new_token())

    fingerprint = token_fingerprint(token)
    check("the fingerprint is not the token", fingerprint != token)
    check("it is a sha256 digest", len(fingerprint) == 64)
    check("it is stable", token_fingerprint(token) == fingerprint)
    check("a matching token compares equal", tokens_match(token, fingerprint))
    check("a different token does not", not tokens_match(new_token(), fingerprint))
    check("an empty fingerprint matches nothing", not tokens_match(token, ""))


# =============================================================================
# 2. MODE
# =============================================================================

def test_mode_detection():
    print("\nMode")

    original = os.environ.get("SENSITOR_AUTH")
    try:
        os.environ.pop("SENSITOR_AUTH", None)
        check("the default is single-user", auth_mode() == SINGLE)

        os.environ["SENSITOR_AUTH"] = "multi"
        check("multi is opt-in by environment", auth_mode() == MULTI)
        os.environ["SENSITOR_AUTH"] = "MULTI"
        check("and is case-insensitive", auth_mode() == MULTI)

        # A typo must not silently disable authentication, so the safe reading
        # is the mode that asks for less, not more.
        os.environ["SENSITOR_AUTH"] = "multiuser"
        check("an unrecognised value falls back to single", auth_mode() == SINGLE)
    finally:
        if original is None:
            os.environ.pop("SENSITOR_AUTH", None)
        else:
            os.environ["SENSITOR_AUTH"] = original


def test_single_user_mode():
    print("\nSingle-user mode")
    auth, store = fresh("single.db", mode=SINGLE)

    result = auth.sign_in(ALICE)
    check("any email signs in", bool(result) and result.email == ALICE)
    check("and a session is issued", bool(result.token))
    check("the token resolves", auth.resolve(result.token) == ALICE)
    check("the user row was created", store.get_user(ALICE) is not None)
    check("no password was stored",
          store.credential(ALICE)["password_hash"] is None)

    check("the mode is reported honestly",
          auth.describe_mode()["mode"] == SINGLE
          and auth.describe_mode()["verified"] is False)

    # The plumbing multi-user depends on runs here too, which is the point of
    # not having a second, simpler code path.
    auth.sign_out(result.token)
    check("signing out revokes the session", auth.resolve(result.token) is None)

    check("changing a password is refused in single mode",
          auth.change_password(ALICE, None, GOOD_PASSWORD).reason == "not_multi_user")

    check("an address without an @ is still refused",
          auth.sign_in("").reason == "invalid_email")


# =============================================================================
# 3. MULTI-USER MODE
# =============================================================================

def test_sign_up_and_in():
    print("\nMulti-user sign-up and sign-in")
    auth, store = fresh("multi.db")

    weak = auth.sign_up(ALICE, "short")
    check("a weak password is refused", weak.reason == "weak_password")
    check("and no account was created", store.get_user(ALICE) is None)

    check("an address without an @ is refused",
          auth.sign_up("nonsense", GOOD_PASSWORD).reason == "invalid_email")

    created = auth.sign_up(ALICE, GOOD_PASSWORD)
    check("a valid sign-up succeeds", bool(created))
    check("and signs the new user in", auth.resolve(created.token) == ALICE)
    check("the stored credential is a hash, not the password",
          GOOD_PASSWORD not in (store.credential(ALICE)["password_hash"] or ""))

    check("signing up twice is refused",
          auth.sign_up(ALICE, GOOD_PASSWORD).reason == "already_registered")

    check("the right password signs in", bool(auth.sign_in(ALICE, GOOD_PASSWORD)))
    check("a wrong password does not",
          auth.sign_in(ALICE, "wrong-password").reason == "invalid_credentials")
    check("no password does not", auth.sign_in(ALICE, None).reason
          == "invalid_credentials")

    # An unknown address and a wrong password give the same answer, because
    # telling them apart tells an attacker which addresses are registered.
    unknown = auth.sign_in("nobody@example.com", GOOD_PASSWORD)
    wrong = auth.sign_in(ALICE, "wrong-password")
    check("an unknown account is indistinguishable from a wrong password",
          unknown.reason == wrong.reason == "invalid_credentials")

    # An account created before passwords existed has no credential, and must
    # not be signable-into with an empty one.
    store.upsert_user(BOB, "free")
    check("an account with no password cannot be signed into",
          auth.sign_in(BOB, "").reason == "invalid_credentials")
    check("nor with any password", auth.sign_in(BOB, "anything").reason
          == "invalid_credentials")


def test_lockout():
    print("\nThrottling")
    auth, store = fresh("lockout.db")
    auth.sign_up(ALICE, GOOD_PASSWORD)

    for _ in range(auth_module.MAX_FAILED_LOGINS):
        auth.sign_in(ALICE, "wrong")

    locked = auth.sign_in(ALICE, GOOD_PASSWORD)
    check("repeated failures lock the account", locked.reason == "locked")
    check("even the correct password is refused while locked", not locked)
    check("and the lockout says until when", bool(locked.detail))

    # The counter lives on the row, not in memory, so a restart does not hand
    # an attacker a fresh budget.
    reopened = Auth(Store(os.path.join(WORK, "lockout.db")), mode=MULTI)
    check("a restart does not reset the lockout",
          reopened.sign_in(ALICE, GOOD_PASSWORD).reason == "locked")

    # Clearing the lock lets the right password back in.
    store.record_login_success(ALICE)
    check("clearing the lock restores access",
          bool(auth.sign_in(ALICE, GOOD_PASSWORD)))


def test_sessions():
    print("\nSessions")
    auth, store = fresh("sessions.db")
    first = auth.sign_up(ALICE, GOOD_PASSWORD)
    second = auth.sign_in(ALICE, GOOD_PASSWORD)

    check("two sign-ins give two different tokens", first.token != second.token)
    check("both resolve", auth.resolve(first.token) == ALICE
          and auth.resolve(second.token) == ALICE)
    check("both are listed", len(store.list_sessions(ALICE)) == 2)

    auth.sign_out(first.token)
    check("signing out revokes only that session",
          auth.resolve(first.token) is None and auth.resolve(second.token) == ALICE)

    check("an invented token resolves to nobody", auth.resolve(new_token()) is None)
    check("an empty token resolves to nobody", auth.resolve("") is None)
    check("None resolves to nobody", auth.resolve(None) is None)

    # Expiry is applied in the query, so a session cannot outlive its date by
    # being read through a path that forgot to check.
    expired = Auth(store, mode=MULTI, session_days=0)
    stale = expired.sign_in(ALICE, GOOD_PASSWORD)
    time.sleep(1.1)
    check("an expired session stops resolving", expired.resolve(stale.token) is None)
    check("and is not listed",
          all(s["fingerprint"] != token_fingerprint(stale.token)
              for s in store.list_sessions(ALICE)))
    check("purging removes it", store.purge_expired_sessions() >= 1)

    auth.sign_out_everywhere(ALICE)
    check("signing out everywhere revokes the rest",
          auth.resolve(second.token) is None)


def test_password_change():
    print("\nChanging a password")
    auth, store = fresh("change.db")
    session = auth.sign_up(ALICE, GOOD_PASSWORD)
    elsewhere = auth.sign_in(ALICE, GOOD_PASSWORD)

    check("the wrong current password is refused",
          auth.change_password(ALICE, "wrong", "a-new-long-password").reason
          == "invalid_credentials")
    check("a weak new password is refused",
          auth.change_password(ALICE, GOOD_PASSWORD, "short").reason
          == "weak_password")

    changed = auth.change_password(ALICE, GOOD_PASSWORD, "a-new-long-password")
    check("a valid change succeeds", bool(changed))
    check("the old password stops working",
          auth.sign_in(ALICE, GOOD_PASSWORD).reason == "invalid_credentials")
    check("the new password works", bool(auth.sign_in(ALICE, "a-new-long-password")))

    # The reason to change a password is usually that someone else may know it,
    # so a change that leaves their session alive has solved nothing.
    check("every other session is revoked",
          auth.resolve(session.token) is None and auth.resolve(elsewhere.token) is None)
    check("and the caller is issued a fresh one",
          auth.resolve(changed.token) == ALICE)


def test_rehash_on_sign_in():
    print("\nUpgrading an old hash")
    auth, store = fresh("rehash.db")

    store.upsert_user(ALICE, "free")
    store.set_password_hash(ALICE, hash_password(GOOD_PASSWORD, n=1024))
    before = store.credential(ALICE)["password_hash"]
    check("the stored hash is below current cost", needs_rehash(before))

    check("it still signs in", bool(auth.sign_in(ALICE, GOOD_PASSWORD)))
    after = store.credential(ALICE)["password_hash"]
    check("and is upgraded in the process", not needs_rehash(after))
    check("the upgraded hash verifies", verify_password(GOOD_PASSWORD, after))
    check("the hash actually changed", before != after)


# =============================================================================
# 4. WHAT AN ATTACKER CANNOT DO
# =============================================================================

def test_one_account_cannot_reach_another():
    print("\nOne account cannot reach another")
    auth, store = fresh("attack.db")

    auth.sign_up(ALICE, GOOD_PASSWORD)
    bob_session = auth.sign_up(BOB, GOOD_PASSWORD)

    store.save_portfolio(ALICE, "Alice's", {"SPY": 1.0})
    store.save_trades(ALICE, [a_trade()])
    alice_pf = store.list_portfolios(ALICE)[0].id

    # Bob holds a genuine session. Everything he can do with it resolves to
    # Bob, and the store is scoped by that — the two layers together are what
    # make this safe, and this asserts the join between them.
    who = auth.resolve(bob_session.token)
    check("Bob's token resolves to Bob", who == BOB)
    check("and reaches none of Alice's portfolios",
          store.get_portfolio(who, alice_pf) is None)
    check("nor her trades", store.list_trades(who) == [])
    check("nor her snapshots", store.list_snapshots(who, alice_pf) == [])

    check("Bob cannot sign in as Alice without her password",
          auth.sign_in(ALICE, GOOD_PASSWORD + "x").reason == "invalid_credentials")

    # The database holds no material that would let an attacker with the file
    # impersonate anyone.
    rows = store._read("SELECT password_hash FROM users")
    check("no plaintext password is stored anywhere",
          all(GOOD_PASSWORD not in (r["password_hash"] or "") for r in rows))
    sessions = store._read("SELECT fingerprint FROM sessions")
    check("no usable session token is stored",
          all(r["fingerprint"] != bob_session.token for r in sessions))
    check("only its fingerprint is",
          any(r["fingerprint"] == token_fingerprint(bob_session.token)
              for r in sessions))

    # Deleting a user takes their sessions with them, so a revoked account
    # cannot keep using a token it already holds.
    counts = store.delete_user(BOB)
    check("deleting a user removes their sessions", counts["sessions"] >= 1)
    check("and their token stops resolving", auth.resolve(bob_session.token) is None)


def test_no_streamlit():
    print("\nLayering")
    import ast
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent / "sensitor" / "core"
    for name in ("auth.py", "security.py"):
        tree = ast.parse((root / name).read_text())
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imports.add(node.module.split(".")[0])
        check(f"{name} imports no streamlit", "streamlit" not in imports)
        check(f"{name} imports no database", "sensitor" not in imports
              and "database" not in imports)

    check("streamlit was never imported by this run",
          sys.modules.get("streamlit") is None)


def main() -> int:
    for test in (test_password_hashing, test_password_strength, test_tokens,
                 test_mode_detection, test_single_user_mode, test_sign_up_and_in,
                 test_lockout, test_sessions, test_password_change,
                 test_rehash_on_sign_in, test_one_account_cannot_reach_another,
                 test_no_streamlit):
        test()

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
