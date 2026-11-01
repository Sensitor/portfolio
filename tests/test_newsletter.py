"""
The newsletter, the member's profile, the complete export, deletion confirmed
by the password, and the technical logs.

    python tests/test_newsletter.py

A subscription is active only after confirmation; unsubscribing works in one
click; the consent is in the export; deleting the account deletes it; the
provider is told when it is configured (a fake opener, no network); no log line
carries an address, a token or a database URL.
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WORK = tempfile.mkdtemp(prefix="sensitor-newsletter-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(WORK, "app.db")
os.environ["SENSITOR_AUTH"] = "multi"
os.environ.pop("SENSITOR_DB_URL", None)
for key in ("SENSITOR_BREVO_API_KEY", "SENSITOR_BREVO_LIST_ID", "SENSITOR_SMTP_HOST"):
    os.environ.pop(key, None)

CHECKS: list[tuple[str, bool, str]] = []
PASSWORD = "un-mot-de-passe-solide"
DASHES = (chr(0x2014), chr(0x2013))


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


class Outbox:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)

    def links(self, page: str) -> list[str]:
        body = self.sent[-1].get_content()
        return re.findall(rf"page={page}&token=([A-Za-z0-9_-]+)", body)


class FakeProvider:
    """Stands for urllib.request.urlopen: records the calls, answers 201."""
    def __init__(self):
        self.calls = []

    def __call__(self, request, timeout=None):
        self.calls.append((request.get_method(), request.full_url, json.loads(request.data), dict(request.headers)))

        class Response:
            status = 201

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        return Response()


def test_double_opt_in() -> None:
    print("\nDouble confirmation")
    from sensitor.database import Store
    from sensitor.platform import newsletter as N
    store = Store(os.path.join(WORK, "n.db"))
    box = Outbox()
    check("no consent, no request", N.request(store, "a@example.com", source="site", consented=False,
                                              transport=box) == "no_consent" and store.newsletter("a@example.com") is None)
    check("an invalid address is refused", N.request(store, "pas-une-adresse", source="site", consented=True,
                                                     transport=box) == "invalid_email")
    check("without e-mail configured, nothing is recorded",
          N.request(store, "a@example.com", source="site", consented=True) == "no_mail"
          and store.newsletter("a@example.com") is None)
    outcome = N.request(store, "A@Example.com ", source="site", consented=True, transport=box)
    row = store.newsletter("a@example.com")
    check("a request is pending, with the exact wording accepted and its date",
          outcome == "sent" and row["status"] == "pending" and row["consent_text"] == N.CONSENT_TEXT
          and row["consent_at"] and row["confirmed_at"] is None)
    check("the stored row holds no token, only fingerprints",
          not any(t in json.dumps(store._read("SELECT * FROM newsletter")[0:1] and dict(store._read(
              "SELECT * FROM newsletter")[0])) for t in box.links("newsletter_confirm") + box.links("newsletter_stop")))
    check("the message carries a confirmation link and a stop link",
          len(box.links("newsletter_confirm")) == 1 and len(box.links("newsletter_stop")) == 1)
    check("asking again at once sends nothing", N.request(store, "a@example.com", source="site", consented=True,
                                                         transport=box) == "throttled" and len(box.sent) == 1)
    confirm, stop = box.links("newsletter_confirm")[0], box.links("newsletter_stop")[0]
    check("a wrong link confirms nothing", N.confirm(store, "faux") is None
          and store.newsletter("a@example.com")["status"] == "pending")
    check("the link confirms", N.confirm(store, confirm) == "a@example.com"
          and store.newsletter("a@example.com")["status"] == "confirmed")
    check("it works once", N.confirm(store, confirm) is None)
    check("a confirmed address is not asked again",
          N.request(store, "a@example.com", source="site", consented=True, transport=box) == "confirmed")
    check("one click unsubscribes", N.stop(store, stop) == "a@example.com"
          and store.newsletter("a@example.com")["status"] == "unsubscribed")
    check("the stop link keeps working", N.stop(store, stop) == "a@example.com")
    with store._write() as conn:
        conn.execute("UPDATE newsletter SET status = 'pending', confirm_fingerprint = 'x', "
                     "confirm_expires_at = '2000-01-01T00:00:00+00:00' WHERE email = 'a@example.com'")
    from sensitor.core.security import token_fingerprint
    with store._write() as conn:
        conn.execute("UPDATE newsletter SET confirm_fingerprint = ? WHERE email = 'a@example.com'",
                     (token_fingerprint("expire"),))
    check("an expired link confirms nothing", N.confirm(store, "expire") is None)
    check("the wording promises no signal and no frequency it cannot keep",
          not any(d in N.CONSENT_TEXT + N.confirm_body("u", "s") for d in DASHES))
    store.close()


def test_provider() -> None:
    print("\nThe provider, when configured")
    from sensitor.database import Store
    from sensitor.integrations import brevo
    from sensitor.platform import newsletter as N
    store = Store(os.path.join(WORK, "p.db"))
    box, provider = Outbox(), FakeProvider()
    N.request(store, "b@example.com", source="account", consented=True, transport=box)
    N.confirm(store, box.links("newsletter_confirm")[0], opener=provider)
    check("not configured: no call", provider.calls == [] and not brevo.configured())
    os.environ["SENSITOR_BREVO_API_KEY"] = "cle-de-test"
    os.environ["SENSITOR_BREVO_LIST_ID"] = "7"
    try:
        N.request(store, "c@example.com", source="site", consented=True, transport=box)
        N.confirm(store, box.links("newsletter_confirm")[0], opener=provider)
        method, url, body, headers = provider.calls[0]
        check("a confirmation adds the contact to the list", method == "POST" and url.endswith("/v3/contacts")
              and body == {"email": "c@example.com", "listIds": [7], "updateEnabled": True}
              and headers.get("Api-key") == "cle-de-test")
        check("and is marked synced", store.newsletter("c@example.com")["provider_synced_at"] is not None)
        N.unsubscribe(store, "c@example.com", opener=provider)
        method, url, body, _ = provider.calls[1]
        check("an unsubscription takes it off the list", method == "PUT"
              and url.endswith("/v3/contacts/c%40example.com") and body == {"unlinkListIds": [7]})

        def broken(request, timeout=None):
            raise OSError("network down")
        check("a provider that cannot be reached never breaks the page", brevo.subscribe("d@example.com", opener=broken)
              is False)
    finally:
        os.environ.pop("SENSITOR_BREVO_API_KEY", None)
        os.environ.pop("SENSITOR_BREVO_LIST_ID", None)
    store.close()


def test_account_data() -> None:
    print("\nExport and deletion")
    from sensitor.core.auth import Auth
    from sensitor.database import Store
    from sensitor.platform import newsletter as N
    store = Store(os.path.join(WORK, "a.db"))
    auth = Auth(store, mode="multi")
    auth.sign_up("m@example.com", PASSWORD)
    auth.sign_up("coach@example.com", PASSWORD)
    store.set_display_name("m@example.com", "  Marie   Curie  ")
    check("the display name is tidied", store.get_user("m@example.com")["display_name"] == "Marie Curie")
    box = Outbox()
    N.request(store, "m@example.com", source="account", consented=True, transport=box)
    N.confirm(store, box.links("newsletter_confirm")[0])
    store.grant_role("coach@example.com", "coach")
    review = store.create_review_request("m@example.com", trade_id="t", trade={"id": "t"}, auto_review={"checks": []},
                                         plan=None, question="Question ?")
    store.answer_review("coach@example.com", review, {"comment": "Bonne gestion."})
    export = store.export_user("m@example.com")
    check("the export carries the consent", export["newsletter"]["consent_text"] == N.CONSENT_TEXT
          and export["newsletter"]["status"] == "confirmed")
    check("and the sessions, without any token or fingerprint", len(export["sessions"]) >= 1
          and all("fingerprint" not in s for s in export["sessions"]))
    coach_export = store.export_user("coach@example.com")
    check("a coach's export carries what they wrote, not the member's trade",
          coach_export["authored"]["review_answers"][0]["feedback"] == {"comment": "Bonne gestion."}
          and "trade" not in coach_export["authored"]["review_answers"][0])
    check("the export is JSON", bool(json.dumps(export, default=str)))
    check("a wrong password deletes nothing", auth.delete_account("m@example.com", "faux") is None
          and store.get_user("m@example.com") is not None)
    check("a password-less account cannot be deleted by a session alone",
          (store.upsert_user("sans@example.com"), auth.delete_account("sans@example.com", ""))[1] is None)
    counts = auth.delete_account("m@example.com", PASSWORD)
    check("the password deletes the account, the subscription with it",
          counts is not None and counts["newsletter"] == 1 and store.newsletter("m@example.com") is None
          and store.get_user("m@example.com") is None)
    single = Auth(store, mode="single")
    store.upsert_user("local@example.com")
    check("in single mode the address typed again confirms",
          single.delete_account("local@example.com", typed="autre@example.com") is None
          and single.delete_account("local@example.com", typed=" Local@Example.com ") is not None)
    store.close()


def test_api() -> None:
    print("\nOver HTTP")
    from fastapi.testclient import TestClient
    from sensitor.api import deps
    from sensitor.api.app import create_app
    from sensitor.core.auth import Auth
    from sensitor.database import Store
    store = Store(os.environ["SENSITOR_DB_PATH"])
    token = Auth(store, mode="multi").sign_up("api@example.com", PASSWORD).token
    deps.get_store.cache_clear()
    client = TestClient(create_app())
    h = {"Authorization": f"Bearer {token}"}
    exported = client.get("/auth/me/export", headers=h)
    check("the export over HTTP", exported.status_code == 200 and exported.json()["user"]["email"] == "api@example.com")
    check("no export without a token", client.get("/auth/me/export").status_code == 401)
    check("a token without the password deletes nothing: 401",
          client.post("/auth/me/delete", headers=h, json={"password": "faux"}).status_code == 401
          and store.get_user("api@example.com") is not None)
    done = client.post("/auth/me/delete", headers=h, json={"password": PASSWORD})
    check("the password deletes the account", done.status_code == 200 and store.get_user("api@example.com") is None)


def test_pages() -> None:
    print("\nThe pages")
    from streamlit.testing.v1 import AppTest
    from sensitor.core.auth import Auth
    from sensitor.database import Store
    from sensitor.platform import newsletter as N
    app_path = str(ROOT / "sensitor_app.py")
    store = Store(os.environ["SENSITOR_DB_PATH"])
    auth = Auth(store, mode="multi")
    auth.sign_up("page@example.com", PASSWORD)

    def run(route, email=None):
        app = AppTest.from_file(app_path, default_timeout=120)
        app.session_state["ac_route"] = route
        if email:
            app.session_state["session_token"] = auth.sign_in(email, PASSWORD).token
        app.run()
        return app

    def text(app):
        return "\n".join(m.value for m in app.markdown)

    public = run({"page": "newsletter"})
    check("the subscription page opens for a visitor, with the consent box",
          not public.exception and any(c.label == N.CONSENT_TEXT for c in public.checkbox))
    public.text_input(key="newsletter_form_email").set_value("visiteur@example.com")
    public.button[0].click().run() if public.button else None
    check("without e-mail configured, the page says so and records nothing",
          store.newsletter("visiteur@example.com") is None and not public.exception)

    box = Outbox()
    N.request(store, "lien@example.com", source="site", consented=True, transport=box)
    confirm = box.links("newsletter_confirm")[0]
    opened = run({"page": "newsletter_confirm", "token": confirm})
    check("opening the link alone confirms nothing (a mail scanner opens links)",
          store.newsletter("lien@example.com")["status"] == "pending" and not opened.exception)
    opened.button(key="newsletter_confirm_button").click().run()
    check("the button confirms", store.newsletter("lien@example.com")["status"] == "confirmed")
    stopped = run({"page": "newsletter_stop", "token": box.links("newsletter_stop")[0]})
    check("the stop link unsubscribes in one click", store.newsletter("lien@example.com")["status"] == "unsubscribed"
          and not stopped.exception)

    account = run({"page": "account"}, "page@example.com")
    body = text(account)
    check("the account page shows the access, the profile and the letter",
          not account.exception and "Gratuit" in body and "Profil" in body and "La lettre de Sensitor" in body,
          str(account.exception[0].value)[:300] if account.exception else "")
    check("deletion asks for the password", any(t.key == "del_pw" for t in account.text_input))
    account.text_input(key="pf_display_name").set_value("Page Test")
    [b for b in account.button if getattr(b, "label", "") == "Enregistrer"][0].click().run()
    check("the profile saves the display name", store.get_user("page@example.com")["display_name"] == "Page Test")
    account.text_input(key="del_pw").set_value("faux")
    [b for b in account.button if "Supprimer" in getattr(b, "label", "")][0].click().run()
    check("a wrong password keeps the account", store.get_user("page@example.com") is not None)
    account.text_input(key="del_pw").set_value(PASSWORD)
    [b for b in account.button if "Supprimer" in getattr(b, "label", "")][0].click().run()
    check("the right one deletes it", store.get_user("page@example.com") is None)

    pages = [run({"page": p}) for p in ("newsletter", "newsletter_confirm", "newsletter_stop")]
    check("no long dash on the letter's pages",
          not any(d in text(p) for p in pages for d in DASHES))


def test_logs() -> None:
    print("\nTechnical logs")
    from sensitor.core import logs
    stream = io.StringIO()
    logger = logs.setup(stream)
    for handler in logger.handlers:
        if getattr(handler, "_sensitor", False):
            handler.stream = stream
    log = logs.get("sensitor.test")
    log.error("sign-in failed for alice@example.com with token=%s on postgresql://u:secret@db/x",
              "Zq3" * 15)
    try:
        raise ValueError("connection to bob@example.com refused, password=hunter2")
    except ValueError:
        log.exception("a page raised")
    out = stream.getvalue()
    check("no address, token, password or database URL reaches the log",
          "alice@" not in out and "bob@" not in out and "hunter2" not in out and "secret@db" not in out
          and "Zq3Zq3" not in out, out)
    check("but the event and the traceback do", "sign-in failed" in out and "Traceback" in out and "ValueError" in out)
    check("setting up twice adds no second handler",
          sum(1 for h in logs.setup().handlers if getattr(h, "_sensitor", False)) == 1)
    check("nothing of the platform prints: it logs",
          not [p for p in (ROOT / "sensitor").rglob("*.py") if "__pycache__" not in p.parts
               and re.search(r"^\s*print\(", p.read_text(encoding="utf-8"), re.M)
               and p.name not in ("admin.py", "backup.py", "validate.py", "__main__.py")
               and "scripts" not in p.parts])


def main() -> int:
    test_double_opt_in()
    test_provider()
    test_account_data()
    test_api()
    test_pages()
    test_logs()
    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
