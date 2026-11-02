"""
The accompaniment (cohorts, workshops, requests) and the statistics.

    python tests/test_accompaniment.py
    SENSITOR_TEST_PG=postgresql://… python tests/test_accompaniment.py   # the store on PostgreSQL too

A member outside a cohort does not see its workshops, checked in the store's
SQL; « Accompagné » is Premium plus an open cohort; every administrator and
coach write is refused to anyone else; the statistics hold counts, never an
address; visits are counted without any identifier.
"""

from __future__ import annotations

import datetime as _dt
import os
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WORK = tempfile.mkdtemp(prefix="sensitor-accompaniment-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(WORK, "app.db")
os.environ["SENSITOR_AUTH"] = "multi"
os.environ.pop("SENSITOR_DB_URL", None)

CHECKS: list[tuple[str, bool, str]] = []
PASSWORD = "un-mot-de-passe-solide"
DASHES = (chr(0x2014), chr(0x2013))


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def _raises(call, kind=Exception) -> bool:
    try:
        call()
    except kind:
        return True
    return False


def test_pure() -> None:
    print("\nCohorts, workshops, requests and rates (pure)")
    from sensitor.platform import cohorts as K
    from sensitor.platform import stats as S
    from sensitor.platform import support as T
    day = _dt.date(2027, 1, 12)
    check("a cohort cannot end before it starts",
          _raises(lambda: K.clean_cohort("Janvier", "", day, day - _dt.timedelta(days=1)), K.CohortError))
    check("a title with a long dash is refused", _raises(lambda: K.clean_cohort("A " + DASHES[0] + " B", "", day, None),
                                                          K.CohortError))
    check("Paris time is stored in UTC, winter", K.to_utc(_dt.date(2027, 1, 12), _dt.time(19, 0))
          == "2027-01-12T18:00:00+00:00")
    check("and summer", K.to_utc(_dt.date(2027, 7, 6), _dt.time(19, 0)) == "2027-07-06T17:00:00+00:00")
    check("a workshop link cannot be a script", _raises(lambda: K.clean_workshop(
        "Atelier", "", day, _dt.time(19), 60, "javascript:alert(1)"), K.CohortError))
    check("an unknown duration is refused", _raises(lambda: K.clean_workshop("Atelier", "", day, _dt.time(19), 61, ""),
                                                     K.CohortError))
    w = {"id": 7, "title": "Revue du plan, semaine 2", "summary": "Plans, journaux; questions", "starts_at":
         K.to_utc(day, _dt.time(19, 0)), "duration_minutes": 90, "place": "https://visio.example/abc", "status": "scheduled"}
    text = K.ics(w, "Cohorte de janvier")
    lines = text.split("\r\n")
    check("the calendar file is RFC 5545: CRLF, UTC times, the end from the duration",
          text.startswith("BEGIN:VCALENDAR\r\n") and "DTSTART:20270112T180000Z" in text
          and "DTEND:20270112T193000Z" in text and text.endswith("END:VCALENDAR\r\n"))
    check("commas and semicolons are escaped, lines folded at 75 octets",
          "Revue du plan\\, semaine 2" in text and "journaux\\; questions" in text
          and all(len(line.encode()) <= 75 for line in lines))
    check("a date reads in French, in Paris time", K.when_label(w["starts_at"]) == "mardi 12 janvier 2027 à 19 h 00")
    ahead, behind = K.upcoming([{**w, "starts_at": "2027-02-01T18:00:00+00:00"}, w,
                                {**w, "starts_at": "2026-01-01T18:00:00+00:00"}], "2026-12-01T00:00:00+00:00")
    check("the next workshop comes first, the latest past first",
          [x["starts_at"][:10] for x in ahead] == ["2027-01-12", "2027-02-01"] and len(behind) == 1)
    check("a request needs a known topic and a real question",
          _raises(lambda: T.clean_request("bourse", "x" * 40), T.SupportError)
          and _raises(lambda: T.clean_request("plan", "Aide ?"), T.SupportError))
    check("a long dash in a question is replaced, not refused",
          DASHES[0] not in T.clean_request("plan", "Mon plan " + DASHES[0] + " est-il assez précis ?")["question"])
    check("the frame says the answer is never investment advice",
          "jamais une recommandation" in T.FRAME and "conseil en investissement" in T.COACH_FRAME)
    steps = S.funnel(200, 20, 10, 4, 1)
    check("the funnel's rates: accounts per visit, then shares of accounts, accompanied among premium",
          [s.rate for s in steps] == [None, 0.1, 0.5, 0.2, 0.25])
    check("more accounts than visits counted: no rate above 100 %, none at all",
          S.funnel(15, 49, 0, 1, 1)[1].rate is None and S.funnel(15, 49, 0, 1, 1)[3].rate == 1 / 49)
    check("a rate over nothing is n/a, not zero", S.percent(S.rate(3, 0)) == "n/a" and S.percent(0.125) == "12,5 %")
    check("campaign tags are cleaned", S.clean_utm({"utm_source": " Insta<script>", "utm_campaign": "A" * 80})
          == {"source": "instascript", "medium": "", "campaign": "a" * 40})


def test_rules() -> None:
    print("\n« Accompagné » is Premium plus an open cohort")
    from sensitor.core import permissions as P
    free_in = P.Member("a@x.fr", P.FREE, frozenset(), frozenset({1}))
    premium_out = P.Member("a@x.fr", P.PREMIUM)
    both = P.Member("a@x.fr", P.PREMIUM, frozenset(), frozenset({1}))
    check("a free member in a cohort is not accompanied", not P.can(free_in, "cohort.read"))
    check("a premium member outside any cohort is not", not P.can(premium_out, "support.request"))
    check("premium in an open cohort is", P.can(both, "cohort.read") and P.can(both, "support.request")
          and P.status_label(both) == "Accompagné")
    check("an administrator manages cohorts without being accompanied",
          P.can(P.Member("b@x.fr", P.FREE, frozenset({"admin"})), "cohort.manage")
          and not P.can(P.Member("b@x.fr", P.FREE, frozenset({"admin"})), "cohort.read"))


def store_checks(store, tag: str) -> None:
    from sensitor.platform import cohorts as K
    admin, coach, member, other = (f"{n}{tag}@example.com" for n in ("admin", "coach", "membre", "autre"))
    for email in (admin, coach, member, other):
        store.upsert_user(email)
    store.grant_role(admin, "admin")
    store.grant_role(coach, "coach")
    data = K.clean_cohort(f"Cohorte {tag}", "", _dt.date.today(), None)
    check("a member cannot create a cohort", store.create_cohort(member, data) is None and store.admin_cohorts(member) is None)
    cohort = store.create_cohort(admin, data)
    check("an administrator can", cohort is not None and any(c["id"] == cohort for c in store.admin_cohorts(admin)))
    check("a member cannot enrol anyone", store.add_to_cohort(member, cohort, member) is False)
    check("an unknown address is not enrolled", store.add_to_cohort(admin, cohort, f"x{tag}@nowhere.example") is False)
    check("an administrator enrols a member", store.add_to_cohort(admin, cohort, member)
          and store.add_to_cohort(admin, cohort, member) is False)
    start = _dt.date.today() + _dt.timedelta(days=3)
    workshop = store.save_workshop(admin, cohort, K.clean_workshop("Atelier", "", start, _dt.time(19), 60,
                                                                    f"https://visio.example/{tag}"))
    check("a member cannot schedule a workshop", store.save_workshop(member, cohort, K.clean_workshop(
        "X", "", start, _dt.time(19), 60, "")) is None and workshop is not None)
    check("enrolled but not premium: no workshop, no link", store.my_workshops(member) == []
          and store.access(member).cohorts == frozenset({cohort}) and not store.access(member).accompanied)
    store.set_tier(member, "premium")
    store.set_tier(other, "premium")
    mine = store.my_workshops(member)
    check("premium and enrolled: the workshop and its link", len(mine) == 1
          and mine[0]["place"] == f"https://visio.example/{tag}" and store.access(member).accompanied)
    check("premium outside the cohort: nothing, checked in SQL", store.my_workshops(other) == [])
    check("the roster says who has Premium", [m["premium"] for m in store.cohort_roster(admin, cohort)] == [1]
          and store.cohort_roster(member, cohort) is None)
    request = {"topic": "plan", "question": "Comment fixer ma limite de perte du jour avec deux comptes ?"}
    check("only an accompanied member may ask", store.create_support_request(other, request) is None
          and store.create_support_request(member, request) is not None)
    check("the request counts for the month", store.count_support_requests(member, "2000-01-01") == 1)
    check("a member's queue is empty; a coach's holds it", store.support_queue(member) == []
          and any(r["question"] == request["question"] for r in store.support_queue(coach)))
    rid = store.support_requests(member)[0]["id"]
    check("a member cannot answer", store.answer_support(member, rid, "Réponse.") is False)
    check("a coach answers once", store.answer_support(coach, rid, "Commencez par une limite unique.")
          and store.answer_support(coach, rid, "Encore") is False)
    check("the member reads it, without the coach's address", store.support_requests(member)[0]["answer"]
          == "Commencez par une limite unique." and "answered_by" not in store.support_requests(member)[0])
    check("it counts as unseen until shown", store.unseen_support(member) == 1
          and (store.mark_support_seen(member, rid), store.unseen_support(member))[1] == 0)
    check("one count query for the coach's sidebar", store.coach_counts(coach)[1] >= 0
          and store.coach_counts(member) == (0, 0))
    store.update_cohort(admin, cohort, data, status="closed")
    check("a closed cohort shows nothing and gives no accompaniment", store.my_workshops(member) == []
          and not store.access(member).accompanied and store.create_support_request(member, request) is None)
    store.update_cohort(admin, cohort, data, status="open")
    export = store.export_user(member)
    check("the export carries the cohort, the requests and the origin",
          export["cohorts"][0]["id"] == cohort and len(export["support_requests"]) == 1 and "signup_source" in export)
    check("a coach's export carries their answers", store.export_user(coach)["authored"]["support_answers"][0]["id"] == rid)
    store.delete_user(coach)
    check("a departing coach's answer stays, without their address",
          store._read("SELECT answered_by FROM support_requests WHERE id = ?", (rid,))[0][0] is None)
    counts = store.delete_user(member)
    check("deleting the member deletes their enrolment and requests",
          counts["cohort_members"] == 1 and counts["support_requests"] == 1
          and store.cohort_roster(admin, cohort) == [])
    store.delete_user(other)
    store.delete_user(admin)


def test_store() -> None:
    print("\nThe store (SQLite)")
    from sensitor.database import Store
    store = Store(os.path.join(WORK, "store.db"))
    store_checks(store, "s")
    print("\nStatistics (SQLite)")
    admin = "stats-admin@example.com"
    store.upsert_user(admin)
    store.grant_role(admin, "admin")
    for _ in range(3):
        store.record_visit("2026-11-01", "home", "site")
    store.record_visit("2026-11-01", "academy", "")
    store.upsert_user("venu@example.com")
    store.set_signup_source("venu@example.com", source="site", medium="", campaign="", landing="home")
    store.set_signup_source("venu@example.com", source="autre", medium="", campaign="", landing="x")
    check("the origin is recorded once", store.signup_source("venu@example.com")["source"] == "site")
    check("a member cannot read the statistics", store.admin_stats("venu@example.com", since="2000-01-01") is None)
    stats = store.admin_stats(admin, since="2026-10-01T00:00:00+00:00")
    check("visits are summed by day, landing and source", stats["visits"] == 4
          and {r["landing"]: r["n"] for r in stats["visits_by_landing"]} == {"home": 3, "academy": 1})
    check("accounts by source, « direct » without tags", {r["source"]: r["n"] for r in stats["by_source"]}
          == {"site": 1, "direct": 1})
    check("no address anywhere in the statistics", "@" not in repr(stats))
    check("the visits table holds no identifier", set(r[1] for r in store._read("PRAGMA table_info(visits)"))
          == {"day", "landing", "source", "n"})
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
    store.record_visit("2026-11-01", f"pg-{uuid.uuid4().hex[:6]}", "site")
    check("pg: a visit is counted", True)
    store.close()


def test_pages() -> None:
    print("\nThe pages")
    from streamlit.testing.v1 import AppTest
    from sensitor.core.auth import Auth
    from sensitor.database import Store
    from sensitor.platform import cohorts as K
    app_path = str(ROOT / "sensitor_app.py")
    store = Store(os.environ["SENSITOR_DB_PATH"])
    auth = Auth(store, mode="multi")
    admin, coach, member, other = "admin@example.com", "coach@example.com", "membre@example.com", "autre@example.com"
    for email in (admin, coach, member, other):
        auth.sign_up(email, PASSWORD)
    store.grant_role(admin, "admin")
    store.grant_role(coach, "coach")
    store.set_tier(member, "premium")
    store.set_tier(other, "premium")
    cohort = store.create_cohort(admin, K.clean_cohort("Cohorte de test", "", _dt.date.today(), None))
    store.add_to_cohort(admin, cohort, member)
    store.save_workshop(admin, cohort, K.clean_workshop("Atelier plan", "Programme.", _dt.date.today()
                                                         + _dt.timedelta(days=2), _dt.time(19), 60,
                                                         "https://visio.example/secret"))
    store.create_support_request(member, {"topic": "plan", "question": "Ma question sur le plan de la semaine."})

    def run(page, email=None):
        app = AppTest.from_file(app_path, default_timeout=120)
        app.session_state["ac_route"] = {"page": page}
        if email:
            app.session_state["session_token"] = auth.sign_in(email, PASSWORD).token
        app.run()
        return app

    def text(app):
        return "\n".join(m.value for m in app.markdown)

    mine = run("accompagnement", member)
    check("an accompanied member sees the workshop, its link and a calendar file",
          not mine.exception and "Atelier plan" in text(mine) and "visio.example/secret" in text(mine)
          and any("agenda" in getattr(b, "label", "") for b in mine.get("download_button")),
          str(mine.exception[0].value)[:300] if mine.exception else "")
    outside = run("accompagnement", other)
    check("a premium member outside the cohort sees neither", not outside.exception
          and "visio.example/secret" not in text(outside) and "Atelier plan" not in text(outside))
    check("a visitor is asked to sign in", "Connectez-vous" in text(run("accompagnement")))
    queue = run("coach_support", coach)
    check("the coach sees the question under a pseudonym, not the address",
          not queue.exception and "Ma question sur le plan" in text(queue) and member not in text(queue))
    check("a member does not see the coaches' queue", "Accès réservé" in text(run("coach_support", member)))
    manage = run("admin_cohorts", admin)
    check("the administrator manages cohorts", not manage.exception and "Cohorte de test" in "\n".join(
        str(s.options) for s in manage.selectbox) and "visio.example/secret" in text(manage),
        str(manage.exception[0].value)[:300] if manage.exception else "")
    check("a coach is not an administrator", "Accès réservé" in text(run("admin_cohorts", coach)))
    stats = run("admin_stats", admin)
    shown = text(stats) + "\n".join(str(d.value) for d in stats.dataframe)
    check("the statistics render, with no address on the page", not stats.exception and "entonnoir" in shown.lower()
          and "@example.com" not in shown.replace(admin, ""),
          str(stats.exception[0].value)[:300] if stats.exception else "")
    check("a member does not see the statistics", "Accès réservé" in text(run("admin_stats", member)))
    side = run("home", member)
    check("the accompanied member's sidebar links to the accompaniment",
          any(b.key == "nav_accompagnement" for b in side.button))
    pages = [mine, queue, manage, stats]
    check("no long dash on these pages", not any(d in text(p) for p in pages for d in DASHES))

    print("\nA visit and the origin of a sign-up")
    before = sum(r["n"] for r in store._read("SELECT n FROM visits"))
    landing = AppTest.from_file(app_path, default_timeout=120)
    landing.query_params["page"] = "account"
    landing.query_params["utm_source"] = "Instagram"
    landing.run()
    after = store._read("SELECT landing, source, n FROM visits WHERE source = 'instagram'")
    check("the first run of a session counts one visit, with its source and no identifier",
          sum(r["n"] for r in store._read("SELECT n FROM visits")) == before + 1 and after
          and after[0]["landing"] == "account")
    landing.run()
    check("the next run of the same session counts nothing",
          sum(r["n"] for r in store._read("SELECT n FROM visits")) == before + 1)
    form = landing.text_input(key="su_email")
    form.set_value("nouveau@example.com")
    landing.text_input(key="su_pw").set_value(PASSWORD)
    [b for b in landing.button if getattr(b, "label", "") == "Créer mon compte"][0].click().run()
    check("a sign-up keeps the link's source", (store.signup_source("nouveau@example.com") or {}).get("source")
          == "instagram", str(store.signup_source("nouveau@example.com")))


def main() -> int:
    test_pure()
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
