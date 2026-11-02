"""
The community and the notifications.

    python tests/test_community.py
    SENSITOR_TEST_PG=postgresql://… python tests/test_community.py   # the store on PostgreSQL too

A message that looks like a recovery phrase or a private key is not published;
authors appear by name or pseudonym, never by address; every member can report
a message and only an administrator decides, the author reading the reason;
deleting an account deletes the member's messages; notifications reach the
right members, and the sidebar's count is one query.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WORK = tempfile.mkdtemp(prefix="sensitor-community-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(WORK, "app.db")
os.environ["SENSITOR_AUTH"] = "multi"
os.environ.pop("SENSITOR_DB_URL", None)
os.environ.pop("SENSITOR_SMTP_HOST", None)

CHECKS: list[tuple[str, bool, str]] = []
PASSWORD = "un-mot-de-passe-solide"
DASHES = (chr(0x2014), chr(0x2013))
SEED = "abandon ability able about above absent absorb abstract absurd abuse access accident"


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def _raises(call, kind=Exception) -> bool:
    try:
        call()
    except kind:
        return True
    return False


def test_rules() -> None:
    print("\nThe charter's rules (pure)")
    from sensitor.platform import community as C
    check("a recovery phrase is refused", C.secret_in(f"Voici mes mots : {SEED}") == "une phrase de récupération"
          and _raises(lambda: C.clean_post(SEED), C.CommunityError))
    check("so is a private key, hexadecimal or WIF",
          C.secret_in("clé " + "a1" * 32) == "une clé privée"
          and C.secret_in("5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ") == "une clé privée")
    check("and an extended private key", C.secret_in("xprv" + "9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4" * 3)
          == "une clé privée étendue")
    french = ("Je pense que la zone des 1,0850 reste valable tant que le prix ne clôture pas sous le plus bas de "
              "mardi ; mon invalidation est simple, et je réduis ma taille quand le spread s'élargit avant les "
              "annonces, comme le dit la leçon sur le calendrier économique.")
    check("an ordinary analysis in French is not mistaken for one", C.secret_in(french) is None)
    check("an address, a hash or a transaction id alone is not one",
          C.secret_in("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq") is None)
    check("a title and a message have their limits",
          _raises(lambda: C.clean_thread("trading", "Court", "x" * 30), C.CommunityError)
          and _raises(lambda: C.clean_thread("nulle-part", "Un titre assez long", "x" * 30), C.CommunityError))
    check("a long dash in a message is replaced, not refused",
          DASHES[0] not in C.clean_post("Mon avis " + DASHES[0] + " à discuter"))
    check("an author is a name or a pseudonym, never an address",
          C.author_label("Marie", "m@example.com") == "Marie"
          and "@" not in C.author_label("", "m@example.com") and C.author_label(None, None) == "Ancien membre")
    check("the charter says no signals, no secrets, no advertising",
          all(word in " ".join(t + x for t, x in C.CHARTER) for word in ("acheter", "phrase de récupération",
                                                                         "parrainage")))


def store_checks(store, tag: str) -> None:
    from sensitor.platform import community as C
    admin, alice, bob, carol = (f"{n}{tag}@example.com" for n in ("admin", "alice", "bob", "carol"))
    for email in (admin, alice, bob, carol):
        store.upsert_user(email)
    store.grant_role(admin, "admin")
    store.set_display_name(alice, "Alice")
    check("a visitor (no account) reads nothing", store.community_threads(f"nobody{tag}@example.com") == []
          and store.community_thread(f"nobody{tag}@example.com", 1) is None)
    tid = store.create_thread(alice, C.clean_thread("trading", "Ma zone tient-elle ?", "Je décris mon scénario et "
                                                    "son invalidation en détail."))
    check("a member opens a discussion with its first message", tid is not None
          and store.community_thread(bob, tid)["posts"][0]["author"] == "Alice")
    listed = [t for t in store.community_threads(bob, theme="trading") if t["id"] == tid]
    check("it is listed in its theme, without the author's address", listed and "@" not in repr(listed))
    pid = store.reply(bob, tid, C.clean_post("Où est ton stop exactement ?"))
    check("a reply is posted, and the other participants are told",
          pid is not None and any(n["kind"] == "reply" and n["fields"]["thread"] == str(tid)
                                  for n in store.notifications(alice))
          and not any(n["kind"] == "reply" for n in store.notifications(bob)))
    thread = store.community_thread(alice, tid)
    check("a reader sees who wrote, by pseudonym when there is no name",
          "@" not in thread["posts"][1]["author"] and thread["posts"][1]["mine"] is False)
    check("only the author edits or deletes a message",
          store.edit_post(carol, pid, "x") is False and store.delete_post(carol, pid) is False
          and store.edit_post(bob, pid, "Où est ton stop, précisément ?"))
    rid = store.report_post(carol, pid, C.clean_report("signal", "Un appel à acheter."))
    check("any member can report a message, once", rid is not None
          and store.report_post(carol, pid, C.clean_report("signal", "")) is None)
    check("a member has no moderation queue", store.moderation_queue(carol) is None
          and store.moderate(carol, rid, hide=True) is False)
    queue = store.moderation_queue(admin)
    check("the administrator sees the report and the message", any(r["id"] == rid and "stop" in r["body"]
                                                                   for r in queue))
    check("the administrator hides it, with a reason", store.moderate(admin, rid, hide=True, note="Pas de signal."))
    hidden = store.community_thread(bob, tid)["posts"][1]
    seen_by_other = store.community_thread(carol, tid)["posts"][1]
    check("its author reads the reason; the others see it hidden, with no text and no reason",
          hidden["hidden"] and "Pas de signal" in (hidden["hidden_reason"] or "")
          and seen_by_other["body"] == "" and seen_by_other["hidden_reason"] is None)
    check("the author is told", any(n["kind"] == "moderation" for n in store.notifications(bob)))
    check("the report is closed", all(r["id"] != rid for r in store.moderation_queue(admin)))
    check("a locked discussion takes no reply", store.lock_thread(admin, tid, True)
          and store.reply(carol, tid, "Encore une question") is None and store.lock_thread(carol, tid, False) is False)
    store.lock_thread(admin, tid, False)
    store.reply(carol, tid, C.clean_post("Merci pour le partage."))
    export = store.export_user(carol)
    check("the export carries the member's messages and reports", len(export["community"]["posts"]) == 1
          and len(export["community"]["reports"]) == 1)
    counts = store.delete_user(alice)
    after = store.community_thread(bob, tid)
    check("deleting an account deletes its messages; the discussion stays for the others, without its author",
          counts["community_posts"] == 1 and after is not None and after["author"] == "Ancien membre"
          and all(p["author"] != "Alice" for p in after["posts"]))
    solo = store.create_thread(carol, C.clean_thread("crypto", "Une question seule", "Personne n'a encore "
                                                     "répondu à ce message."))
    store.delete_user(carol)
    check("a discussion left with no message goes too", store.community_thread(bob, solo) is None)
    store.delete_user(bob)
    store.delete_user(admin)


def test_store() -> None:
    print("\nThe store (SQLite)")
    from sensitor.database import Store
    store = Store(os.path.join(WORK, "store.db"))
    store_checks(store, "s")
    print("\nNotifications (SQLite)")
    from sensitor.platform import cohorts as K
    import datetime as dt
    admin, coach, member = "n-admin@example.com", "n-coach@example.com", "n-membre@example.com"
    for email in (admin, coach, member):
        store.upsert_user(email)
    store.grant_role(admin, "admin")
    store.grant_role(coach, "coach")
    store.set_tier(member, "premium")
    cohort = store.create_cohort(admin, K.clean_cohort("Cohorte", "", dt.date.today(), None))
    store.add_to_cohort(admin, cohort, member)
    store.save_workshop(admin, cohort, K.clean_workshop("Atelier", "", dt.date.today() + dt.timedelta(days=2),
                                                         dt.time(19), 60, ""))
    check("a new workshop tells the cohort", any(n["kind"] == "workshop" for n in store.notifications(member))
          and store.notifications(coach) == [])
    store.create_support_request(member, {"topic": "plan", "question": "Une question assez longue pour passer."})
    rid = store.support_requests(member)[0]["id"]
    store.answer_support(coach, rid, "Une réponse assez longue pour l'exemple.")
    check("an answer to a request tells the member", any(n["kind"] == "support" for n in store.notifications(member)))
    review = store.create_review_request(member, trade_id="t", trade={"id": "t"}, auto_review={"checks": []},
                                         plan=None, question="Question ?")
    store.answer_review(coach, review, {"comment": "Bien."})
    check("so does an answer to a review", any(n["kind"] == "review" for n in store.notifications(member)))
    state = store.notification_state(member, ("public", "member", "premium"))
    check("the sidebar's state: unread count in one query", state["mine"] == 3 and state["since"])
    from sensitor.platform import market as M
    with store._write() as conn:                 # the member joined before the session, not in the same second
        conn.execute("UPDATE users SET created_at = '2026-01-01T00:00:00+00:00' WHERE email = ?", (member,))
    session = store.save_market_session(coach, M.clean_session({
        "session_date": dt.date.today().isoformat(), "title": "Séance du jour", "access": "premium",
        "context": "Un contexte détaillé pour la séance du jour, assez long pour être publié sans difficulté.",
        "calendar": [], "scenarios": [{"instrument": "EURUSD", "title": "Rebond sur la zone",
                                      "condition": "Une clôture horaire au-dessus de la zone",
                                      "observe": "La réaction des acheteurs", "invalidation": "Une clôture sous 1,0800"}]}))
    published = store.publish_market_session(coach, session) if session else None
    check("a published session counts as new, for a member who may read it",
          published == [] and store.notification_state(member, ("public", "member", "premium"))["sessions"] == 1
          and store.notification_state(member, ("public", "member"))["sessions"] == 0, str(published))
    store.mark_notifications_read(member)
    state = store.notification_state(member, ("public", "member", "premium"))
    check("reading clears both", state["mine"] == 0 and state["sessions"] == 0)
    counts = store.delete_user(member)
    check("deleting the account deletes its notifications", counts["notifications"] == 3
          and store.notifications(member) == [])
    store.close()


def test_postgres() -> None:
    url = os.getenv("SENSITOR_TEST_PG", "").strip()
    print("\nThe store (PostgreSQL)")
    if not url:
        print("  (SENSITOR_TEST_PG not set: skipped)")
        return
    from sensitor.database import Store
    store = Store(url)
    store_checks(store, uuid.uuid4().hex[:8])
    email = f"pgn{uuid.uuid4().hex[:6]}@example.com"
    store.upsert_user(email)
    check("pg: the notification state reads in one query", store.notification_state(email, ("public",))["mine"] == 0)
    store.mark_notifications_read(email)
    store.delete_user(email)
    store.close()


def test_pages() -> None:
    print("\nThe pages")
    from streamlit.testing.v1 import AppTest
    from sensitor.core.auth import Auth
    from sensitor.database import Store
    from sensitor.platform import community as C
    app_path = str(ROOT / "sensitor_app.py")
    store = Store(os.environ["SENSITOR_DB_PATH"])
    auth = Auth(store, mode="multi")
    admin, alice, bob = "admin@example.com", "alice@example.com", "bob@example.com"
    for email in (admin, alice, bob):
        auth.sign_up(email, PASSWORD)
    store.grant_role(admin, "admin")
    store.set_display_name(alice, "Alice")
    tid = store.create_thread(alice, C.clean_thread("methode", "Tenir son plan après deux pertes",
                                                    "Comment faites-vous pour ne pas doubler la taille ensuite ?"))

    def run(route, email=None):
        app = AppTest.from_file(app_path, default_timeout=120)
        app.session_state["ac_route"] = route
        if email:
            app.session_state["session_token"] = auth.sign_in(email, PASSWORD).token
        app.run()
        return app

    def text(app):
        return "\n".join(m.value for m in app.markdown)

    index = run({"page": "community"}, bob)
    check("a member sees the discussions and the form", not index.exception and "Tenir son plan" in text(index)
          and any(t.key == "community_new_title" for t in index.text_input),
          str(index.exception[0].value)[:300] if index.exception else "")
    check("no address on the page", alice not in text(index))
    thread = run({"page": "community_thread", "thread": str(tid)}, bob)
    check("a discussion shows its messages, by name", not thread.exception and "Alice" in text(thread)
          and "doubler la taille" in text(thread))
    thread.text_area(key="thread_reply_body").set_value(SEED)
    [b for b in thread.button if getattr(b, "label", "") == "Répondre"][0].click().run()
    check("a reply carrying a recovery phrase is refused, with the reason",
          len(store.community_thread(bob, tid)["posts"]) == 1
          and any("phrase de récupération" in e.value for e in thread.error))
    thread.text_area(key="thread_reply_body").set_value("Je réduis ma taille de moitié pendant une semaine.")
    [b for b in thread.button if getattr(b, "label", "") == "Répondre"][0].click().run()
    check("an ordinary reply is published", len(store.community_thread(bob, tid)["posts"]) == 2)
    bell = run({"page": "home"}, alice)
    check("the author's sidebar shows one notification", any(b.key == "nav_notifications" and "· 1" in b.label
                                                             for b in bell.button))
    notes = run({"page": "notifications"}, alice)
    check("the notifications page lists the reply, then marks it read",
          not notes.exception and "Nouvelle réponse" in text(notes)
          and store.notification_state(alice, ("public",))["mine"] == 0)
    check("a member has no moderation page", "Accès réservé" in text(run({"page": "admin_moderation"}, bob)))
    post = store.community_thread(alice, tid)["posts"][1]["id"]
    store.report_post(alice, post, C.clean_report("other", ""))
    mod = run({"page": "admin_moderation"}, admin)
    check("the administrator's queue shows the report", not mod.exception and "réduis ma taille" in text(mod))
    visitor = run({"page": "community_thread", "thread": str(tid)})
    check("a visitor does not read a discussion", "doubler la taille" not in text(visitor))
    check("no long dash on the community's pages",
          not any(d in text(p) for p in (index, thread, notes, mod) for d in DASHES))


def main() -> int:
    test_rules()
    test_store()
    test_postgres()
    test_pages()
    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
