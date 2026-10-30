"""
The trading room: what a session may contain, who may write and read it, and
how its pages render for a visitor, a member and a coach.

    python tests/test_market.py

The pure module first (no Streamlit, no database), then the store on a
throwaway database, then the pages through Streamlit's AppTest.
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SENSITOR_DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="sensitor-market-"), "market.db")
os.environ["SENSITOR_AUTH"] = "multi"

from sensitor.platform import market as M  # noqa: E402

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sensitor_app.py")
CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def raises(call) -> bool:
    try:
        call()
    except ValueError:
        return True
    return False


SCENARIO = {"instrument": "eurusd", "title": "Balayage des plus bas de vendredi",
            "condition": "Si le prix passe sous les plus bas de vendredi puis réintègre la zone en clôture horaire",
            "observe": "La vitesse du retour", "invalidation": "Une clôture en H1 sous le plus bas du balayage",
            "lessons": ["lesson:liquidite-et-scenarios/sweeps"]}


def raw_session(**over) -> dict:
    base = {"session_date": "2026-10-27", "access": "member", "context": "Semaine des banques centrales.",
            "calendar": "14:30 | Emploi américain | forte\n10:00 | Indice Ifo | ", "scenarios": [SCENARIO, {}],
            "live_url": "", "lessons": ["lesson:processus-de-trading/preparer-seance"]}
    base.update(over)
    return base


def test_module() -> None:
    print("\nWhat a session may contain")
    s = M.clean_session(raw_session())
    check("a session is cleaned: default title, upper-case instrument, empty slot dropped",
          s["title"] == "Séance du mardi 27 octobre 2026" and s["content"]["scenarios"][0]["instrument"] == "EURUSD"
          and len(s["content"]["scenarios"]) == 1)
    check("the calendar is sorted by time, its weight defaults to moyenne",
          [(c["time"], c["weight"]) for c in s["content"]["calendar"]] == [("10:00", "moyenne"), ("14:30", "forte")])
    check("the calendar goes back to its editable form",
          M.calendar_text(s["content"]["calendar"]) == "10:00 | Indice Ifo | moyenne\n14:30 | Emploi américain | forte")
    check("a scenario without its invalidation is refused",
          raises(lambda: M.clean_session(raw_session(scenarios=[{**SCENARIO, "invalidation": ""}]))))
    check("a session needs a context and a date",
          raises(lambda: M.clean_session(raw_session(context=""))) and raises(lambda: M.clean_session(raw_session(session_date=""))))
    check("at most four scenarios", raises(lambda: M.clean_session(raw_session(scenarios=[SCENARIO] * 5))))
    check("a malformed calendar line is refused with its number",
          raises(lambda: M.parse_calendar("8h30 Emploi")) and raises(lambda: M.parse_calendar("08:30 | Emploi | énorme")))
    check("only https YouTube or Vimeo for a live",
          M.clean_video_url("https://www.youtube.com/watch?v=abc") and M.clean_video_url("https://youtu.be/abc")
          and M.clean_video_url("https://vimeo.com/1") and raises(lambda: M.clean_video_url("http://youtube.com/x"))
          and raises(lambda: M.clean_video_url("https://example.com/live"))
          and raises(lambda: M.clean_video_url("javascript:alert(1)")))
    check("a linked lesson must name a lesson", raises(lambda: M.clean_lessons(["https://ailleurs"])))

    print("\nNo signal, no promise")
    flagged = {
        "Achetez EURUSD au-dessus de 1,0850.": "achetez",
        "On vend la cassure.": "vendez",
        "Prenez position dès l'ouverture.": "prenez position",
        "Signal d'achat sur l'or.": "signal d'achat",
        "Objectif de cours : 1,10.": "objectif de gain",
        "Un gain garanti.": "promesse",
        "ACHETEZ maintenant": "achetez",
    }
    for text, what in flagged.items():
        check(f"flagged: {text}", bool(M.signal_phrases(text)), what)
    allowed = ["Rien n'est garanti.", "Un signal de faiblesse sur l'unité inférieure.", "Les vendeurs reprennent la main.",
               "Si la clôture se fait sous 1,0820, le scénario est invalidé.", "Les acheteurs défendent la zone."]
    for text in allowed:
        check(f"allowed: {text}", not M.signal_phrases(text))
    check("a session without scenario cannot be published", M.publishable(M.clean_session(raw_session(scenarios=[]))))
    check("a clean session can", M.publishable(s) == [])
    dirty = M.clean_session(raw_session(context="Achetez l'euro avant la Fed."))
    check("a signal in the context blocks publication", any("achetez" in p for p in M.publishable(dirty)))

    print("\nThe review")
    r = M.clean_review({"outcomes": [{"outcome": "invalide", "comment": "Clôture sous 1,0820 dès 15 h."}],
                        "takeaway": "L'invalidation écrite le matin disait quoi faire : rien."}, s["content"]["scenarios"])
    check("each scenario gets its outcome", r["outcomes"][0]["outcome"] == "invalide")
    check("an outcome is required for every scenario",
          raises(lambda: M.clean_review({"outcomes": [], "takeaway": "x"}, s["content"]["scenarios"])))
    check("a takeaway is required",
          raises(lambda: M.clean_review({"outcomes": [{"outcome": "joue"}], "takeaway": ""}, s["content"]["scenarios"])))
    check("a review cannot carry a signal either",
          raises(lambda: M.clean_review({"outcomes": [{"outcome": "joue"}], "takeaway": "Achetez demain."},
                                        s["content"]["scenarios"])))
    t = M.tally([r, {"outcomes": [{"outcome": "joue"}, {"outcome": "non-declenche"}]}])
    check("the record counts outcomes across sessions", (t.played, t.invalidated, t.untriggered, t.total) == (1, 1, 1, 3))
    check("dates read in French", M.date_label("2026-10-27") == "mardi 27 octobre 2026")


def test_store() -> None:
    print("\nWho may write, who may read")
    from sensitor.core.auth import Auth
    from sensitor.database import Store

    store = Store(os.environ["SENSITOR_DB_PATH"])
    auth = Auth(store, mode="multi")
    for email in ("coach@example.com", "membre@example.com"):
        auth.sign_up(email, "un-mot-de-passe-solide")
    store.set_role("coach@example.com", "coach")
    s = M.clean_session(raw_session())
    check("a member cannot write a session", store.save_market_session("membre@example.com", s) is None)
    sid = store.save_market_session("coach@example.com", s)
    check("a coach can", isinstance(sid, int))
    check("a draft is invisible to members and visitors",
          store.market_session(sid) is None and store.market_session(sid, coach="membre@example.com") is None
          and store.market_sessions() == [] and store.market_drafts("membre@example.com") == [])
    check("a coach sees it, with its author", store.market_session(sid, coach="coach@example.com")["author_email"]
          == "coach@example.com" and len(store.market_drafts("coach@example.com")) == 1)
    check("a member cannot publish", store.publish_market_session("membre@example.com", sid) is None)
    store.save_market_session("coach@example.com", M.clean_session(raw_session(context="Achetez l'euro.")), sid)
    check("the store refuses to publish a signal", store.publish_market_session("coach@example.com", sid))
    store.save_market_session("coach@example.com", s, sid)
    check("then publishes the clean version", store.publish_market_session("coach@example.com", sid) == [])
    published = store.market_session(sid)
    check("a published session is readable, without its author's address",
          published and "author_email" not in published and [x["id"] for x in store.market_sessions()] == [sid])
    check("a published session cannot be deleted", not store.delete_market_session("coach@example.com", sid))
    review = M.clean_review({"outcomes": [{"outcome": "joue"}], "takeaway": "Le scénario s'est déroulé."},
                            s["content"]["scenarios"])
    check("a member cannot review", not store.review_market_session("membre@example.com", sid, review))
    check("a coach can", store.review_market_session("coach@example.com", sid, review)
          and store.market_session(sid)["review"]["outcomes"][0]["outcome"] == "joue")
    check("unpublishing makes it a draft again", store.unpublish_market_session("coach@example.com", sid)
          and store.market_session(sid) is None)
    store.publish_market_session("coach@example.com", sid)
    store.delete_user("coach@example.com")
    check("a departing coach's sessions stay, without the address",
          store.market_session(sid) is not None
          and store._read("SELECT author_email FROM market_sessions WHERE id = ?", (sid,))[0]["author_email"] is None)


def test_pages() -> None:
    print("\nThe pages")
    from streamlit.testing.v1 import AppTest
    from sensitor.core.auth import Auth
    from sensitor.database import Store

    store = Store(os.environ["SENSITOR_DB_PATH"])
    auth = Auth(store, mode="multi")

    def token(email):
        result = auth.sign_up(email, "un-mot-de-passe-solide")
        return result.token if result else auth.sign_in(email, "un-mot-de-passe-solide").token

    def run(route, tok=None):
        app = AppTest.from_file(APP, default_timeout=60)
        app.session_state["ac_route"] = route
        if tok:
            app.session_state["session_token"] = tok
        app.run()
        return app

    def text(app):
        return "\n".join(m.value for m in app.markdown)

    member, coach = token("lectrice@example.com"), token("equipe@example.com")
    store.set_role("equipe@example.com", "coach")
    with store._write() as conn:                 # start from an empty room
        conn.execute("DELETE FROM market_sessions")
    empty = run({"page": "market"})
    check("with no session, the room says so and invents nothing",
          "Aucune séance publiée pour l'instant" in text(empty) and not empty.exception)
    s = M.clean_session(raw_session(access="member"))
    sid = store.save_market_session("equipe@example.com", s)
    store.publish_market_session("equipe@example.com", sid)
    public = store.save_market_session("equipe@example.com", M.clean_session(raw_session(access="public",
                                                                                         session_date="2026-10-26")))
    store.publish_market_session("equipe@example.com", public)
    draft = store.save_market_session("equipe@example.com", M.clean_session(raw_session(session_date="2026-10-30",
                                                                                        context="Brouillon secret.")))
    room = run({"page": "market"})
    body = text(room)
    check("the room lists the published sessions", "Séance du mardi 27 octobre 2026" in body and not room.exception,
          str(room.exception[0].value)[:200] if room.exception else "")
    check("a draft never shows in the room", "Brouillon secret" not in body and "vendredi 30 octobre" not in body)
    locked = run({"page": "market_session", "session": str(sid)})
    check("a member session is locked for a visitor",
          "Séance réservée aux membres" in text(locked) and SCENARIO["invalidation"] not in text(locked))
    opened = run({"page": "market_session", "session": str(sid)}, member)
    check("a member reads it, invalidation included",
          SCENARIO["invalidation"] in text(opened) and "Ni signal" in text(opened) and not opened.exception)
    free = run({"page": "market_session", "session": str(public)})
    check("a public session reads without an account", SCENARIO["invalidation"] in text(free))
    hidden = run({"page": "market_session", "session": str(draft)}, member)
    check("a draft is not found by a member", "Séance introuvable" in text(hidden))
    refused = run({"page": "market_edit"}, member)
    check("a member cannot open the editor", "Accès réservé" in text(refused) and not refused.text_area)
    editor = run({"page": "market_edit"}, coach)
    check("a coach can, with the four scenario slots", not editor.exception and len(editor.expander) >= 4,
          str(editor.exception[0].value)[:200] if editor.exception else "")
    # The editor end to end: a coach writes a session and publishes it, then a
    # session that gives an instruction is saved as a draft but not published.
    def fill(app, context, condition):
        app.date_input(key="menew_date").set_value(__import__("datetime").date(2026, 11, 2))
        app.text_area(key="menew_context").set_value(context)
        app.text_input(key="menew_s0_instrument").set_value("gbpusd")
        app.text_input(key="menew_s0_title").set_value("Retour sur la zone de Londres")
        app.text_area(key="menew_s0_condition").set_value(condition)
        app.text_area(key="menew_s0_invalidation").set_value("Une clôture horaire sous la zone")
        publish = [b for b in app.button if b.label == "Publier"]
        publish[0].click().run()
        return app

    before = {x["id"] for x in store.market_sessions()}
    done = fill(run({"page": "market_edit"}, coach), "Semaine calme avant la BoE.",
                "Si le prix revient sur la zone de Londres")
    new = [x for x in store.market_sessions() if x["id"] not in before]
    check("the editor publishes a clean session", not done.exception and len(new) == 1
          and new[0]["content"]["scenarios"][0]["instrument"] == "GBPUSD",
          str(done.exception[0].value)[:200] if done.exception else str(len(new)))
    drafts_before = len(store.market_drafts("equipe@example.com"))
    refused_app = fill(run({"page": "market_edit"}, coach), "Achetez la livre avant la BoE.",
                       "Si le prix revient sur la zone")
    check("the editor keeps a signal as a draft, unpublished",
          not refused_app.exception and len(store.market_drafts("equipe@example.com")) == drafts_before + 1
          and len(store.market_sessions()) == len(before) + 1)
    team_room = run({"page": "market"}, coach)
    check("a coach sees the drafts in the room", "Brouillon secret" not in text(team_room)
          and "vendredi 30 octobre 2026" in text(team_room))
    dashes = [name for name, app in (("room", room), ("session", opened), ("editor", editor))
              if any(d in m.value for m in app.markdown if not m.value.startswith("<style") for d in ("\u2014", "\u2013"))]
    check("no long dash on the room's pages", not dashes, str(dashes))
    labels = " ".join(str(getattr(w, "label", "")) for w in list(editor.text_input) + list(editor.text_area)).lower()
    check("no field asks for a seed phrase or a private key",
          "seed" not in labels and "clé privée" not in labels and "phrase de récupération" not in labels)


def main() -> int:
    test_module()
    test_store()
    test_pages()
    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
