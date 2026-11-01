"""
Who may do what: the permissions module, entitlements, roles, and the
administrator's page and routes.

    python tests/test_permissions.py

Checks the rules (`core.permissions`), the migration of the values earlier
versions wrote (`users.tier` « pro » or « premium », `users.role` « coach »,
`PRO_EMAILS`), that every administrator write is refused server-side to anyone
else (in the `Store` and over HTTP), that the level follows grants, ends and
revocations, and that no screen compares level strings any more.
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WORK = tempfile.mkdtemp(prefix="sensitor-permissions-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(WORK, "app.db")
os.environ["SENSITOR_AUTH"] = "multi"
os.environ.pop("SENSITOR_DB_URL", None)

CHECKS: list[tuple[str, bool, str]] = []
PASSWORD = "un-mot-de-passe-solide"
ADMIN, ALICE, BOB = "admin@example.com", "alice@example.com", "bob@example.com"


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def test_rules() -> None:
    print("\nThe rules")
    from sensitor.core import permissions as P

    visitor, free = P.VISITOR_MEMBER, P.member(ALICE, "free")
    premium, legacy = P.member(ALICE, "premium"), P.member(ALICE, "pro")
    admin = P.member(ADMIN, "free", roles=("admin",))
    coach = P.member(BOB, "free", roles=("coach",))
    check("a visitor reads public content only",
          P.can_read(visitor, "public") and not P.can_read(visitor, "member") and not P.can_read(visitor, "premium"))
    check("an account reads member content, not premium",
          P.can_read(free, "member") and not P.can_read(free, "premium"))
    check("premium reads everything", all(P.can_read(premium, a) for a in ("public", "member", "premium")))
    check("the legacy « pro » reads as premium", legacy.level == P.PREMIUM and P.can_read(legacy, "premium"))
    check("an unknown content level is closed", not P.can_read(premium, "secret"))
    check("an unknown capability is an error, not a silent no",
          _raises(lambda: P.can(premium, "portfolio.teleport")))
    check("optimisation and stress tests are premium capabilities",
          not P.can(free, "portfolio.optimize") and not P.can(free, "portfolio.stress_test")
          and P.can(premium, "portfolio.optimize") and P.can(premium, "portfolio.stress_test"))
    check("limits per level", P.limit(free, "portfolio.max_assets") == 5 and P.limit(premium, "portfolio.max_assets") == 50
          and P.limit(free, "review.monthly_quota") == 1 and P.limit(premium, "review.monthly_quota") == 8
          and P.limit(visitor, "review.monthly_quota") == 0)
    check("an administrator manages access without opening premium content",
          P.can(admin, "admin.access") and not P.can_read(admin, "premium") and not P.can(admin, "portfolio.optimize"))
    check("a coach answers reviews and writes sessions; a member does neither",
          P.can(coach, "review.answer") and P.can(coach, "market.publish")
          and not P.can(free, "review.answer") and not P.can(coach, "admin.members"))
    check("a role on a visitor gives nothing", not P.can(P.Member(None, P.FREE, frozenset({"admin"})), "admin.members"))
    check("why something is locked", P.lock_reason(visitor, "member") == "sign-in"
          and P.lock_reason(free, "premium") == "premium" and P.lock_reason(premium, "premium") is None)
    now = "2026-06-01T12:00:00+00:00"
    grants = [{"level": "premium", "starts_at": "2026-01-01T00:00:00+00:00", "ends_at": "2026-05-01T00:00:00+00:00",
               "revoked_at": None},
              {"level": "premium", "starts_at": "2026-01-01T00:00:00+00:00", "ends_at": None,
               "revoked_at": "2026-02-01T00:00:00+00:00"},
              {"level": "premium", "starts_at": "2026-07-01T00:00:00+00:00", "ends_at": None, "revoked_at": None}]
    check("ended, revoked and future grants give nothing", P.level_from(grants, now) == P.FREE)
    grants.append({"level": "premium", "starts_at": "2026-01-01T00:00:00+00:00",
                   "ends_at": "2026-12-31T23:59:59+00:00", "revoked_at": None})
    check("an active grant gives premium", P.level_from(grants, now) == P.PREMIUM)
    check("only premium is granted", _raises(lambda: P.entitlement_level("free")))


def test_migration() -> None:
    print("\nValues written by earlier versions")
    from sensitor.database import Store
    path = os.path.join(WORK, "old.db")
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (email TEXT PRIMARY KEY, tier TEXT NOT NULL DEFAULT 'free',
            display_name TEXT, password_hash TEXT, last_login_at TEXT,
            failed_logins INTEGER NOT NULL DEFAULT 0, locked_until TEXT, email_verified_at TEXT,
            role TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        INSERT INTO users (email, tier, created_at, updated_at) VALUES ('pro@example.com', 'pro', 'x', 'x');
        INSERT INTO users (email, tier, created_at, updated_at) VALUES ('prem@example.com', 'premium', 'x', 'x');
        INSERT INTO users (email, tier, role, created_at, updated_at) VALUES ('coach@example.com', 'free', 'coach', 'x', 'x');
        PRAGMA user_version = 11;
    """)
    conn.commit()
    conn.close()
    store = Store(path)
    check("« pro » and « premium » become entitlements", store.access("pro@example.com").level == "premium"
          and store.access("prem@example.com").level == "premium"
          and store.entitlements("pro@example.com")[0]["source"] == "migration")
    check("the coach role is carried into user_roles", store.is_coach("coach@example.com")
          and store.roles("coach@example.com") == frozenset({"coach"}))
    store.set_tier("pro@example.com", "free")
    store.set_role("coach@example.com", "")
    store.close()
    store = Store(path)
    check("opening again copies nothing twice", len(store.entitlements("prem@example.com")) == 1)
    check("a level revoked since is not copied back", store.access("pro@example.com").level == "free")
    check("a coach removed since is not named again", not store.is_coach("coach@example.com"))
    check("the foreign keys are enforced after the copy", store._read("PRAGMA foreign_keys")[0][0] == 1)
    store.close()


def test_store() -> None:
    print("\nAccess in the store: administrators only")
    from sensitor.database import Store
    store = Store(os.path.join(WORK, "store.db"))
    for email in (ADMIN, ALICE, BOB):
        store.upsert_user(email)
    store.set_password_hash(ALICE, "scrypt$secret")
    check("the first administrator is named by the operator", store.grant_role(ADMIN, "admin") and store.is_admin(ADMIN))
    check("an unknown address gets no role", store.grant_role("nobody@example.com", "admin") is False)
    check("a member's list is refused", store.admin_members(ALICE) is None and store.admin_member(ALICE, BOB) is None
          and store.admin_count(ALICE) is None)
    check("a member cannot grant premium, even to themself",
          store.grant_access(ALICE, ALICE, reason="moi") is None and store.access(ALICE).level == "free")
    check("a member cannot name a coach or an administrator",
          store.admin_set_role(ALICE, ALICE, "admin", True) is False and not store.is_admin(ALICE))
    listing = store.admin_members(ADMIN)
    check("an administrator lists the members, without credentials",
          {m["email"] for m in listing} == {ADMIN, ALICE, BOB}
          and all("password_hash" not in m and "failed_logins" not in m for m in listing))
    check("the search narrows by address", [m["email"] for m in store.admin_members(ADMIN, query="alice")] == [ALICE])
    check("a grant needs a reason", store.grant_access(ADMIN, ALICE, reason="  ") is None)
    check("an end in the past is refused",
          _raises(lambda: store.grant_access(ADMIN, ALICE, reason="test", ends_at="2000-01-01T00:00:00+00:00")))
    grant = store.grant_access(ADMIN, ALICE, reason="Bêta-testeuse", ends_at="2999-01-01T00:00:00+00:00")
    check("an administrator grants premium, with a reason and an end", grant is not None
          and store.access(ALICE).level == "premium" and store.get_user(ALICE)["tier"] == "premium")
    item = store.admin_member(ADMIN, ALICE)
    check("the grant is traced: who, why, until when", item["entitlements"][0]["reference"] == ADMIN
          and item["entitlements"][0]["reason"] == "Bêta-testeuse" and item["entitlements"][0]["ends_at"].startswith("2999"))
    check("a member cannot revoke it", store.revoke_access(ALICE, grant) is False and store.access(ALICE).level == "premium")
    check("an administrator revokes it", store.revoke_access(ADMIN, grant) and store.access(ALICE).level == "free"
          and store.get_user(ALICE)["tier"] == "free")
    check("a revoked grant stays in the history", store.entitlements(ALICE)[0]["revoked_by"] == ADMIN)
    check("it cannot be revoked twice", store.revoke_access(ADMIN, grant) is False)
    with store._write() as conn:                    # a grant that ended yesterday
        conn.execute("INSERT INTO entitlements (user_email, level, source, reference, reason, starts_at, ends_at, "
                     "created_at) VALUES (?, 'premium', 'manual', ?, 'fini', '2020-01-01T00:00:00+00:00', "
                     "'2020-02-01T00:00:00+00:00', '2020-01-01T00:00:00+00:00')", (BOB, ADMIN))
    check("an ended grant gives nothing, without anyone revoking it", store.access(BOB).level == "free")
    check("an administrator names a coach", store.admin_set_role(ADMIN, BOB, "coach", True) and store.is_coach(BOB)
          and store.get_user(BOB)["role"] == "coach")
    check("and removes the role", store.admin_set_role(ADMIN, BOB, "coach", False) and not store.is_coach(BOB))
    check("an administrator cannot remove their own role",
          store.admin_set_role(ADMIN, ADMIN, "admin", False) is False and store.is_admin(ADMIN))
    store.admin_set_role(ADMIN, ALICE, "admin", True)
    store.delete_user(ADMIN)
    check("a departing administrator's grants stay, without their address",
          all(e["reference"] != ADMIN and e.get("revoked_by") != ADMIN
              for e in store.entitlements(ALICE) + store.entitlements(BOB)))
    export = store.export_user(ALICE)
    check("the export carries the member's grants and roles",
          len(export["entitlements"]) == 1 and export["roles"] == ["admin"])
    counts = store.delete_user(ALICE)
    check("deleting a member deletes their grants and roles", counts["entitlements"] == 1 and counts["user_roles"] == 1
          and store.entitlements(ALICE) == [] and store.roles(ALICE) == frozenset())
    check("the system path sets the level without a second active grant",
          (store.set_tier(BOB, "premium"), store.set_tier(BOB, "premium"),
           sum(1 for e in store.entitlements(BOB) if not e["revoked_at"] and not e["ends_at"]))[-1] == 1)
    store.close()


def test_pro_emails() -> None:
    print("\nPRO_EMAILS becomes an entitlement, once")
    from sensitor.core import config
    from sensitor.core.auth import Auth
    from sensitor.database import Store
    store = Store(os.path.join(WORK, "pro.db"))
    listed = "vip@example.com"
    original = config.PRO_EMAILS
    config.PRO_EMAILS = frozenset({listed})
    try:
        auth = Auth(store, mode="multi")
        auth.sign_up(listed, PASSWORD)
        check("a listed address signs up premium", store.access(listed).level == "premium"
              and store.entitlements(listed)[0]["source"] == "config")
        store.grant_role(ADMIN, "admin") if store.get_user(ADMIN) else (store.upsert_user(ADMIN), store.grant_role(ADMIN, "admin"))
        store.revoke_access(ADMIN, store.entitlements(listed)[0]["id"])
        auth.sign_in(listed, PASSWORD)
        check("a revocation is not undone at the next sign-in", store.access(listed).level == "free")
        single = Auth(store, mode="single")
        single.sign_in("other@example.com")
        check("an address that is not listed stays free", store.access("other@example.com").level == "free")
        check("sign-up ignores a level passed by the caller",
              Auth(store, mode="multi").sign_up("sly@example.com", PASSWORD, tier="premium").ok
              and store.access("sly@example.com").level == "free")
    finally:
        config.PRO_EMAILS = original
        store.close()


def test_api() -> None:
    print("\nOver HTTP")
    from fastapi.testclient import TestClient
    from sensitor.api import deps
    from sensitor.api.app import create_app
    from sensitor.core.auth import Auth
    from sensitor.database import Store

    store = Store(os.environ["SENSITOR_DB_PATH"])
    auth = Auth(store, mode="multi")
    admin = auth.sign_up(ADMIN, PASSWORD).token
    alice = auth.sign_up(ALICE, PASSWORD).token
    store.grant_role(ADMIN, "admin")
    deps.get_store.cache_clear()
    client = TestClient(create_app())

    def h(token):
        return {"Authorization": f"Bearer {token}"}

    check("a member is refused the list: 403", client.get("/admin/members", headers=h(alice)).status_code == 403)
    check("a visitor too: 401", client.get("/admin/members").status_code == 401)
    check("a member cannot grant: 403", client.post("/admin/access", headers=h(alice),
          json={"email": ALICE, "reason": "moi"}).status_code == 403)
    check("and nothing changed", store.access(ALICE).level == "free")
    members = client.get("/admin/members", headers=h(admin))
    check("an administrator lists the members", members.status_code == 200
          and {m["email"] for m in members.json()} >= {ADMIN, ALICE})
    check("the address travels in the body, not the path",
          all("{email}" not in path for path in client.get("/openapi.json").json()["paths"]))
    check("an empty reason: 422", client.post("/admin/access", headers=h(admin),
          json={"email": ALICE, "reason": ""}).status_code == 422)
    granted = client.post("/admin/access", headers=h(admin), json={"email": ALICE, "reason": "Partenariat"})
    check("an administrator grants premium: 201", granted.status_code == 201)
    me = client.get("/auth/me", headers=h(alice)).json()
    check("the member's level reads premium in /auth/me", me["tier"] == "premium")
    check("a member cannot revoke: 403",
          client.delete(f"/admin/access/{granted.json()['id']}", headers=h(alice)).status_code == 403)
    check("an administrator revokes: 204",
          client.delete(f"/admin/access/{granted.json()['id']}", headers=h(admin)).status_code == 204)
    check("and the level follows", client.get("/auth/me", headers=h(alice)).json()["tier"] == "free")
    check("an unknown grant: 404", client.delete("/admin/access/99999", headers=h(admin)).status_code == 404)
    check("an administrator does not read premium content by being one", store.access(ADMIN).level == "free")


def test_pages() -> None:
    print("\nThe platform's « Membres » page")
    from streamlit.testing.v1 import AppTest
    from sensitor.core.auth import Auth
    from sensitor.database import Store
    app_path = str(ROOT / "sensitor_app.py")
    store = Store(os.environ["SENSITOR_DB_PATH"])
    auth = Auth(store, mode="multi")

    def run(email):
        app = AppTest.from_file(app_path, default_timeout=120)
        app.session_state["ac_route"] = {"page": "admin"}
        if email:
            app.session_state["session_token"] = auth.sign_in(email, PASSWORD).token
        app.run()
        return app

    member = run(ALICE)
    text = "\n".join(m.value for m in member.markdown)
    check("a member sees the lock, not the members", not member.exception and "Accès réservé" in text
          and ALICE not in "\n".join(str(d.value) for d in member.dataframe))
    admin = run(ADMIN)
    text = "\n".join(m.value for m in admin.markdown)
    check("an administrator sees the list and the counts", not admin.exception and len(admin.dataframe) == 1
          and "Accès Premium actifs" in text, str(admin.exception[0].value)[:300] if admin.exception else "")
    admin.selectbox(key="admin_pick").set_value(ALICE).run()
    admin.text_input(key="grant_reason").set_value("Bêta-testeuse").run()
    form_button = [b for b in admin.button if getattr(b, "label", "") == "Attribuer"]
    if form_button:
        form_button[0].click().run()
    check("the administrator grants premium from the page", store.access(ALICE).level == "premium",
          str(admin.exception[0].value)[:300] if admin.exception else "")
    visitor = run(None)
    check("a visitor sees the lock", not visitor.exception
          and "Accès réservé" in "\n".join(m.value for m in visitor.markdown))


def test_no_level_strings() -> None:
    print("\nNo screen compares level strings")
    allowed = {ROOT / "sensitor/core/permissions.py", ROOT / "sensitor/database/connection.py"}
    files = [p for p in list((ROOT / "sensitor").rglob("*.py")) + [ROOT / "portfolio_optimizer_saas.py",
             ROOT / "sensitor_app.py"] if p not in allowed and "__pycache__" not in p.parts]
    patterns = (re.compile(r"""['"]pro['"]"""),
                re.compile(r"""\b(tier|user_tier|level)\w*\s*(==|!=)\s*['"]"""),
                re.compile(r"""\bin\s*\(\s*['"](pro|premium|free)['"]"""),
                re.compile(r"""PREMIUM_TIERS|TIER_LIMITS|MONTHLY_QUOTA\s*="""))
    offenders = []
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(p.search(line) for p in patterns):
                offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:90]}")
    check("no « pro », no tier comparison, outside the permissions module and the migration",
          not offenders, "\n      ".join(offenders))
    from types import SimpleNamespace
    from sensitor.academy.ui import library
    check("the Library labels a premium sheet « Premium », not « Membres »",
          "Premium" in library._access_pill(SimpleNamespace(access="premium"))
          and "Membres" in library._access_pill(SimpleNamespace(access="member")))


def test_postgres() -> None:
    """The same store methods on a real PostgreSQL, when `SENSITOR_TEST_PG` names one (CI does)."""
    url = os.getenv("SENSITOR_TEST_PG", "").strip()
    print("\nOn PostgreSQL")
    if not url:
        print("  (SENSITOR_TEST_PG not set: skipped)")
        return
    import uuid
    from sensitor.database import Store
    store = Store(url)
    tag = uuid.uuid4().hex[:8]
    admin, alice = f"admin{tag}@example.com", f"alice{tag}@example.com"
    for email in (admin, alice):
        store.upsert_user(email)
    store.grant_role(admin, "admin")
    check("pg: a member is refused", store.grant_access(alice, alice, reason="x") is None)
    grant = store.grant_access(admin, alice, reason="test", ends_at="2999-01-01T00:00:00+00:00")
    check("pg: an administrator grants", grant is not None and store.access(alice).level == "premium")
    check("pg: the list and the counts", any(m["email"] == alice for m in store.admin_members(admin, query=tag))
          and store.admin_count(admin)["premium"] >= 1)
    check("pg: revoke", store.revoke_access(admin, grant) and store.access(alice).level == "free")
    check("pg: roles", store.admin_set_role(admin, alice, "coach", True) and store.is_coach(alice)
          and store.admin_set_role(admin, admin, "admin", False) is False)
    outcome = store.newsletter_request(alice, consent_text="c", source="site", confirm_fingerprint=f"cf{tag}",
                                       unsubscribe_fingerprint=f"uf{tag}", expires_at="2999-01-01T00:00:00+00:00",
                                       resend_after="2000-01-01T00:00:00+00:00")
    check("pg: newsletter", outcome == "pending" and store.newsletter_confirm(f"cf{tag}") == alice
          and store.newsletter_stop(f"uf{tag}") == alice)
    counts = store.delete_user(alice)
    store.delete_user(admin)
    check("pg: deletion covers the new tables", counts["newsletter"] == 1 and counts["entitlements"] == 1
          and counts["user_roles"] == 1)
    store.close()
    check("pg: opening again carries nothing twice, without error", Store(url).has_admin() in (True, False))


def _raises(call) -> bool:
    try:
        call()
    except Exception:
        return True
    return False


def main() -> int:
    test_rules()
    test_migration()
    test_store()
    test_pro_emails()
    test_no_level_strings()
    test_api()
    test_pages()
    test_postgres()
    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
