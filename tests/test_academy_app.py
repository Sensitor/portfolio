"""
The Sensitor platform app (Academy and the other spaces), run headless with
`streamlit.testing`.

Every page renders without an exception for a visitor and for a member; member
lessons stay locked for a visitor; marking a lesson done and submitting a quiz
write rows under the signed-in member only; a forged session token grants
nothing.

Run with:  python tests/test_academy_app.py
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SENSITOR_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="sensitor-academy-app-"), "app.db")
os.environ["SENSITOR_AUTH"] = "multi"
os.environ.pop("SENSITOR_ACADEMY_PREVIEW", None)

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sensitor_app.py")
LEGACY_APP = os.path.join(os.path.dirname(APP), "academy_app.py")
FAILURES: list[str] = []
COUNT = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global COUNT
    COUNT += 1
    if condition:
        print(f"  ok    {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


def store():
    from sensitor.database import Store
    return Store(os.environ["SENSITOR_DB_PATH"])


def token(email: str) -> str:
    from sensitor.core.auth import Auth
    auth = Auth(store(), mode="multi")
    result = auth.sign_up(email, "un-mot-de-passe-solide")
    return result.token if result else auth.sign_in(email, "un-mot-de-passe-solide").token


def run(route: dict, tok: str | None = None, *, entry: str = APP) -> AppTest:
    app = AppTest.from_file(entry, default_timeout=60)
    app.session_state["ac_route"] = route
    if tok:
        app.session_state["session_token"] = tok
    app.run()
    return app


def text(app: AppTest) -> str:
    return "\n".join(m.value for m in app.markdown)


def error(app: AppTest) -> str:
    return str(app.exception[0].value)[:300] if app.exception else ""


ROUTES = [
    {"page": "home"},
    {"page": "academy"},
    {"page": "paths"},
    {"page": "resource", "resource": "fiche-vocabulaire-execution"},
    {"page": "resource", "resource": "checklist-avant-trade"},
    {"page": "resource", "resource": "inexistante"},
    {"page": "psychology"},
    {"page": "market"},
    {"page": "community"},
    {"page": "tools"},
    {"page": "reset"},
    {"page": "reset", "token": "invalide"},
    {"page": "verify", "token": "invalide"},
    {"page": "page-inconnue"},
    {"page": "course", "course": "premiers-pas"},
    {"page": "lesson", "course": "premiers-pas", "lesson": "fonctionnement-marche"},
    {"page": "lesson", "course": "premiers-pas", "lesson": "ordres-et-couts"},
    {"page": "lesson", "course": "premiers-pas", "lesson": "structure-de-marche"},
    {"page": "lesson", "course": "premiers-pas", "lesson": "budget-de-risque"},
    {"page": "lesson", "course": "premiers-pas", "lesson": "cas-pratique"},
    {"page": "lesson", "course": "premiers-pas", "lesson": "recapitulatif"},
    {"page": "quiz", "quiz": "premiers-pas-validation", "course": "premiers-pas"},
    {"page": "library"},
    {"page": "lab"},
    {"page": "progress"},
    {"page": "account"},
    {"page": "course", "course": "inexistant"},
    {"page": "lesson", "course": "premiers-pas", "lesson": "inexistante"},
]


def label(route: dict) -> str:
    return "/".join(str(v) for v in route.values())


def main() -> int:
    alice = token("alice@example.com")

    print("\nEvery page renders")
    dashed = []
    for route in ROUTES:
        for who, tok in (("visitor", None), ("member", alice)):
            app = run(route, tok)
            check(f"{who} · {label(route)}", not app.exception, error(app))
            if any(d in m.value for m in app.markdown if not m.value.startswith("<style")
                   for d in ("\u2014", "\u2013")):
                dashed.append(f"{who} · {label(route)}")
    check("no em or en dash on any rendered page (house style)", not dashed, str(dashed))

    print("\nAccount")
    me = run({"page": "account"}, alice)
    body = text(me)
    labels = [b.label for b in me.button]
    check("the member sees sign-out everywhere", "Se déconnecter de tous les appareils" in labels)
    check("…a password change form", any(f.label == "Changer le mot de passe" for f in me.button)
          or "Changer le mot de passe" in str(me))
    check("…a full export", "Exporter toutes mes données (JSON)" in str(me))
    check("…and account deletion", "Supprimer le compte" in body)
    check("verification status is shown", "Adresse vérifiée" in body)
    visitor = run({"page": "account"})
    check("a visitor sees the forgotten-password tab", "Mot de passe oublié" in str(visitor))
    check("…which says e-mail is not configured here", "non configuré" in text(visitor))
    bad = run({"page": "verify", "token": "invalide"})
    check("a bad verification link says so", "expiré" in text(bad))

    print("\nAccess")
    locked = run({"page": "lesson", "course": "premiers-pas", "lesson": "budget-de-risque"})
    body = text(locked)
    check("a member lesson is locked for a visitor", "Leçon réservée aux membres" in body)
    check("…and its content is not rendered", "Commencer par ce que l'on accepte de perdre" not in body)
    open_ = run({"page": "lesson", "course": "premiers-pas", "lesson": "budget-de-risque"}, alice)
    check("a member reads it", "Commencer par ce que l'on accepte de perdre" in text(open_))
    forged = run({"page": "lesson", "course": "premiers-pas", "lesson": "budget-de-risque"},
                 "not-a-real-token")
    check("a forged token is a visitor", "Leçon réservée aux membres" in text(forged))
    public = run({"page": "lesson", "course": "premiers-pas", "lesson": "fonctionnement-marche"})
    check("a public lesson reads without an account", "Le carnet d'ordres" in text(public))
    check("dollar amounts are escaped, not LaTeX",
          all("$" not in m.value or "\\$" in m.value or "&#36;" in m.value
              for m in public.markdown if not m.value.startswith("<style")))

    print("\nProgress is written under the member, and only the member")
    app = run({"page": "lesson", "course": "premiers-pas", "lesson": "fonctionnement-marche"}, alice)
    done = [b for b in app.button if b.label == "Marquer la leçon comme terminée"]
    check("the completion button is offered", len(done) == 1)
    done[0].click().run()
    check("clicking it renders cleanly", not app.exception, error(app))
    rows = store().completed_lessons("alice@example.com")
    check("the completion is stored", [r["lesson_id"] for r in rows] == ["fonctionnement-marche"])
    visitor = run({"page": "lesson", "course": "premiers-pas", "lesson": "fonctionnement-marche"})
    check("a visitor gets no completion button",
          not any(b.label == "Marquer la leçon comme terminée" for b in visitor.button))

    print("\nA quiz attempt is graded and stored")
    app = run({"page": "quiz", "quiz": "premiers-pas-validation", "course": "premiers-pas"}, alice)
    first = app.radio[0]
    first.set_value("bid").run()
    submit = [b for b in app.button if b.label == "Soumettre mes réponses"]
    submit[0].click().run()
    force = [b for b in app.button if b.label == "Soumettre quand même"]
    check("unanswered questions ask for confirmation", len(force) == 1)
    force[0].click().run()
    check("the review renders", not app.exception and "1<small> / 10</small>" in text(app), error(app))
    attempts = store().quiz_attempts("alice@example.com", "premiers-pas-validation")
    check("the attempt is stored", len(attempts) == 1 and attempts[0]["correct"] == 1)
    check("bob has none", store().quiz_attempts("bob@example.com") == [])

    dash = run({"page": "home"}, alice)
    check("the dashboard reads the real progress", "<b>1</b> / 6" in text(dash))

    print("\nThe platform")
    legacy = run({"page": "home"}, entry=LEGACY_APP)
    check("the old academy_app.py entry point still renders", not legacy.exception, error(legacy))
    old = run({"page": "paths"})
    check("the old « paths » page opens the Academy home",
          "Construire une <em>méthode</em>" in text(old))
    for page in ("psychology", "market", "community"):
        app = run({"page": page})
        body = text(app)
        check(f"{page}: says plainly it is not open", "pas encore ouvert" in body)
        check(f"{page}: offers no input of any kind",
              not app.text_input and not app.radio and not app.checkbox and not app.text_area)
    tools = run({"page": "tools"})
    check("tools: no link when the address is not configured",
          "Lien non configuré" in text(tools))
    sidebar = [b.label for b in run({"page": "home"}).sidebar.button]
    from sensitor.platform import spaces
    check("the sidebar lists every space, in registry order",
          [l for l in sidebar if l in {s.label for s in spaces.SPACES}] == [s.label for s in spaces.SPACES],
          str(sidebar))
    unknown = run({"page": "page-inconnue"})
    check("an unknown page falls back to the home page", "Comprendre le marché." in text(unknown))

    print(f"\n{COUNT} checks, {len(FAILURES)} failures")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
