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
    {"page": "journal"},
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


def _catalog_routes() -> list[dict]:
    """Every course, lesson and final quiz of every open path."""
    from sensitor.academy.content import load_catalog
    routes = []
    for course in load_catalog().available_courses():
        routes.append({"page": "course", "course": course.id})
        routes += [{"page": "lesson", "course": course.id, "lesson": l.id} for l in course.lessons]
        if course.final_quiz_id:
            routes.append({"page": "quiz", "quiz": course.final_quiz_id, "course": course.id})
    return routes


ROUTES += [r for r in _catalog_routes() if r not in ROUTES]


def label(route: dict) -> str:
    return "/".join(str(v) for v in route.values())


def fixture_tree() -> str:
    """
    The real content plus one opened Bitcoin-track course: a sourced public
    lesson using every new block (update date, opinion, debate, chart) and a
    premium lesson. Rendered through SENSITOR_ACADEMY_CONTENT, so the real
    curriculum is never touched.
    """
    import shutil
    from pathlib import Path
    from sensitor.academy.content import CONTENT_ROOT
    root = Path(tempfile.mkdtemp(prefix="academy-fixture-")) / "academy"
    shutil.copytree(CONTENT_ROOT, root)
    cur = root / "curriculum.toml"
    import re
    text = cur.read_text()
    block = re.search(r'id = "monnaie-inflation".*?courses = \[([^\]]*)\]', text, re.S)
    assert block, "the Monnaie et Bitcoin path 1 must list its courses"
    start, end = block.span(1)
    cur.write_text(text[:start] + block.group(1) + ', "fixture-monnaie"' + text[end:])
    course = root / "courses" / "fixture-monnaie"
    (course / "lessons").mkdir(parents=True)
    (course / "course.toml").write_text(
        'id = "fixture-monnaie"\npath = "monnaie-inflation"\ntitle = "Cours de démonstration"\n'
        'summary = "Un cours de test."\nlevel = "debutant"\nstatus = "published"\nversion = 1\n'
        'objectives = ["Tester."]\n\n[[module]]\nid = "m1"\ntitle = "Module"\n'
        'lessons = ["lecon-sourcee", "lecon-premium"]\n')
    body = ('\n## Une section\n\nDu texte.\n\n::: callout opinion\nJe pense que Bitcoin a sa place dans un '
            'patrimoine.\n:::\n\n::: callout debate\nLes écoles de pensée divergent.\n:::\n\n'
            '::: chart emission-bitcoin\nL\'offre de Bitcoin par époque.\n:::\n\n::: tool risk-calculator\n:::\n\n'
            '::: callout recap\n- Retenir.\n:::\n')
    head = ('+++\nid = "{id}"\ntitle = "{title}"\nsummary = "Résumé."\nduration_minutes = 5\n'
            'access = "{access}"\nstatus = "published"\nversion = 1\nobjectives = ["Comprendre."]\n'
            'updated = 2026-10-17\nsources = ["Nakamoto, S. (2008). Bitcoin: A Peer-to-Peer Electronic Cash System."]\n+++\n')
    (course / "lessons" / "lecon-sourcee.md").write_text(
        head.format(id="lecon-sourcee", title="Leçon sourcée", access="public") + body)
    (course / "lessons" / "lecon-premium.md").write_text(
        head.format(id="lecon-premium", title="Leçon premium", access="premium")
        + "\nLe contenu premium visible.\n\n::: tool risk-calculator\n:::\n\n::: callout recap\n- Retenir.\n:::\n")
    return str(root)


def test_new_tracks(alice: str) -> None:
    print("\nNew tracks: sourced lessons, charts, premium")
    os.environ["SENSITOR_ACADEMY_CONTENT"] = fixture_tree()
    try:
        home = run({"page": "academy"})
        body = text(home)
        check("the programme is grouped by track, trading first",
              body.index("Trading · 9 sur 10") < body.index("Monnaie et Bitcoin · 2 sur 2") < body.index("Crypto · 2 sur 2"))
        lesson = run({"page": "lesson", "course": "fixture-monnaie", "lesson": "lecon-sourcee"})
        body = text(lesson)
        check("the sourced lesson renders", not lesson.exception, error(lesson))
        check("its review date is shown", "mis à jour le 17 octobre 2026" in body)
        check("an opinion is framed as the founder's", "Opinion du fondateur" in body)
        check("a debate has its own frame", "Débat" in body)
        check("the chart is drawn", len(lesson.get("plotly_chart")) == 1)
        check("its source line is printed under it", "Calcul : règles du protocole Bitcoin" in body
              and "licence : calcul Sensitor" in body)
        check("its sources are listed", "Nakamoto, S. (2008)" in body)
        locked = run({"page": "lesson", "course": "fixture-monnaie", "lesson": "lecon-premium"})
        check("premium, visitor: asked to sign in", "Créez un compte gratuit" in text(locked)
              and "Le contenu premium visible" not in text(locked))
        free = run({"page": "lesson", "course": "fixture-monnaie", "lesson": "lecon-premium"}, alice)
        check("premium, free member: told it is premium, nothing to pay",
              "Leçon Premium" in text(free) and "aucun paiement" in text(free)
              and "Le contenu premium visible" not in text(free))
        pro = token("pro@example.com")
        store().upsert_user("pro@example.com", tier="pro")
        opened = run({"page": "lesson", "course": "fixture-monnaie", "lesson": "lecon-premium"}, pro)
        check("premium, pro member: the lesson opens", "Le contenu premium visible" in text(opened)
              and not opened.exception, error(opened))
        course = run({"page": "course", "course": "fixture-monnaie"})
        check("the outline marks the premium lesson", "Premium" in text(course))
        check("the course names its track and number", "Monnaie et Bitcoin · Parcours 01" in text(course))
    finally:
        os.environ.pop("SENSITOR_ACADEMY_CONTENT", None)


def test_universes() -> None:
    print("\nOne ecosystem, two universes")
    landing = text(run({"page": "home"}))
    check("the landing presents one ecosystem", "L'écosystème Sensitor" in landing
          and "Apprendre le <em>trading</em>." in landing
          and 'Comprendre la <em class="cu">monnaie</em>.' in landing
          and 'Diversifier avec la <em class="cu">crypto</em>.' in landing)
    check("…with both universes side by side, trading not placed above money",
          'sx-ucard uni-trading' in landing and 'sx-ucard uni-monnaie' in landing)
    check("…and the first course of each universe to start with",
          "Par où commencer" in landing and 'sx-feature uni-trading' in landing
          and 'sx-feature uni-monnaie' in landing)
    academy = text(run({"page": "academy"}))
    check("the Academy opens on its two universes", "Deux univers, un seul programme" in academy
          and 'comprendre la <em class="cu">monnaie</em>' in academy)
    check("open courses are listed under the head of their universe",
          academy.index('sx-uhead uni-trading') < academy.index('sx-feature uni-trading')
          < academy.index('sx-uhead uni-monnaie') < academy.index('sx-feature uni-monnaie'))
    for page, route in (("course", {"course": "premiers-pas"}),
                        ("lesson", {"course": "premiers-pas", "lesson": "fonctionnement-marche"})):
        app = run({"page": page, **route})
        body = text(app)
        check(f"trading {page}: marked trading, in blue", 'sx-scope uni-trading' in body
              and 'sx-uni uni-trading' in body and 'sx-scope uni-monnaie' not in body, error(app))
    for page, route in (("course", {"course": "la-monnaie"}),
                        ("lesson", {"course": "la-monnaie", "lesson": "fonctions-monnaie"}),
                        ("quiz", {"quiz": "monnaie-validation", "course": "la-monnaie"})):
        app = run({"page": page, **route})
        body = text(app)
        check(f"money {page}: marked Monnaie et crypto, in copper", 'sx-scope uni-monnaie' in body
              and not app.exception and (page == "quiz" or "Monnaie et crypto" in body), error(app))
    from sensitor.platform.ui import theme
    css = theme.stylesheet()
    check("the stylesheet recolours a money page and changes its title face",
          '.stApp:has(.sx-scope.uni-monnaie) [data-testid="stMain"]' in css
          and "--serif: var(--grotesk)" in css and "Space+Grotesk" in css)
    from sensitor.academy import content as C
    from sensitor.academy.ui import chart_view
    catalog = C.load_catalog()
    chart = catalog.chart("taux-bce-fed")
    fig = chart_view.figure(chart, catalog.dataset(chart.dataset), universe="monnaie")
    check("a money chart leads with copper", fig.data[0].line.color == theme.TOKENS["copper-2"])


def test_hash_demo(tok: str) -> None:
    print("\nThe hash demonstration")
    from sensitor.academy import hashing as H
    page = run({"page": "lesson", "course": "bitcoin-fonctionnement", "lesson": "preuve-de-travail"}, tok)
    check("the lesson renders with its demonstration", not page.exception
          and any(t.label == "Texte" for t in page.text_input), error(page))
    check("the digest of the default text is shown", H.digest("Alice paie 1 BTC à Bob") in text(page))
    next(t for t in page.text_input if t.label == "Texte").set_value("Sensitor").run()
    check("a new text gives a new digest", H.digest("Sensitor") in text(page))
    next(b for b in page.button if b.label == "Chercher le nonce").click().run()
    mined = H.mine("Sensitor", 3)
    body = text(page)
    check("the nonce found is the first that works, and its digest starts with 000",
          "Nonce trouvé" in body and f"{mined.nonce:,}".replace(",", "\u202f") in body
          and mined.digest[3:] in body and not page.exception, error(page))
    check("no key or seed phrase is asked for", all("phrase" not in t.label.lower() and "clé" not in t.label.lower()
                                                   for t in page.text_input))


def test_no_secret_asked(tok: str) -> None:
    print("\nNo key or seed phrase is ever asked for")
    from sensitor.academy import content as C
    catalog = C.load_catalog()
    words = ("phrase", "seed", "clé", "cle privée", "mnémonique", "mot de passe du portefeuille", "private")
    for course_id in ("bitcoin-fonctionnement", "bitcoin-reserve-de-valeur", "crypto-en-securite", "analyser-un-projet-crypto"):
        for lesson in catalog.course(course_id).lessons:
            page = run({"page": "lesson", "course": course_id, "lesson": lesson.id}, tok)
            labels = [t.label.lower() for t in page.text_input] + [t.label.lower() for t in page.text_area]
            check(f"{lesson.id}: renders, no field asks for a secret",
                  not page.exception and not any(w in label for w in words for label in labels),
                  error(page) or str(labels))


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
    check("a visitor sees the forgotten-password panel", "Mot de passe oublié" in str(visitor))
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
    from sensitor.academy.content import load_catalog
    total = sum(len(c.lessons) for c in load_catalog().available_courses())
    check("the dashboard reads the real progress", f"<b>1</b> / {total}" in text(dash))

    print("\nThe savings simulator")
    sim = run({"page": "lesson", "course": "inflation-et-patrimoine", "lesson": "simulateur-epargne"}, alice)
    check("the simulator renders in its lesson", not sim.exception and len(sim.get("plotly_chart")) >= 1, error(sim))
    def plain(app):
        return text(app).replace("\u202f", " ").replace("\xa0", " ")
    check("its defaults: 206 295 € shown, 113 889 € of purchasing power",
          "206 295 €" in plain(sim) and "113 889 €" in plain(sim))
    sim.number_input(key="savings_lesson_simulateur-epargne_rate").set_value(0.0)
    sim.number_input(key="savings_lesson_simulateur-epargne_monthly").set_value(0.0)
    sim.run()
    check("set to cash: 10 000 € shown, 5 521 € of purchasing power",
          "10 000 €" in plain(sim) and "5 521 €" in plain(sim) and not sim.exception, error(sim))

    print("\nThe reflection journal")
    visitor = run({"page": "psychology"})
    check("visitor: the space is open and explains the journal",
          not visitor.exception and "Pourquoi écrire" in text(visitor), error(visitor))
    check("visitor: asked to sign in, offered no field",
          "Connectez-vous pour tenir votre journal" in text(visitor) and not visitor.text_area)
    page = run({"page": "psychology"}, alice)
    check("member: the journal renders", not page.exception and page.text_area, error(page))
    check("member: the privacy notice is shown", "Seul votre compte peut lire ces notes" in text(page))
    check("member: no note yet", "Aucune note pour l" in text(page))
    secret = "Trop pressé ce matin <script>alert(1)</script>\nDeuxième ligne $ 100"
    page.text_area(key="jr_body_pre").input(secret)
    page.radio(key="jr_mood_pre").set_value(2)
    check("the routine before the session is offered", len(page.checkbox) == 5)
    page.checkbox(key="jr_chk_pre_etat").check()
    page.checkbox(key="jr_chk_pre_limites").check()
    next(b for b in page.button if b.label == "Enregistrer la note").click().run()
    notes = store().journal_entries("alice@example.com")
    check("the note is stored under the member", len(notes) == 1 and notes[0]["mood"] == 2
          and notes[0]["kind"] == "pre", str(notes))
    check("bob has no note", store().journal_entries("bob@example.com") == [])
    body = text(page)
    check("the note is shown, escaped", "&lt;script&gt;" in body and "<script>" not in body)
    check("its line breaks are kept", "<br>Deuxième ligne" in body)
    check("its routine is stored in order", store().journal_entries("alice@example.com")[0]["checks"]
          == ["etat", "limites"])
    check("its routine is shown on the note", "Routine : 2 sur 5" in body)
    check("each routine item is counted with its sample size",
          "Mes limites du jour sont écrites</td><td>1 sur 1 note</td>" in body
          and "Chaque scénario a son invalidation écrite</td><td>0 sur 1 note</td>" in body)
    check("nothing is announced as planned any more", "Ce qui est prévu" not in body)
    check("its sample size is shown", "1 note</td>" in body)
    check("no diagnosis is offered", "ni une évaluation ni un diagnostic" in body)
    page.text_area(key="jr_body_pre").input("   ")
    next(b for b in page.button if b.label == "Enregistrer la note").click().run()
    check("an empty note is refused", "Écrivez quelques mots" in "\n".join(e.value for e in page.error)
          and len(store().journal_entries("alice@example.com")) == 1)
    bob = token("bob@example.com")
    bob_page = run({"page": "psychology"}, bob)
    check("bob's journal does not show alice's note",
          "Trop pressé" not in text(bob_page) and "Aucune note pour l" in text(bob_page))
    next(b for b in page.button if b.label == "Supprimer").click().run()
    check("deleting asks for confirmation first", len(store().journal_entries("alice@example.com")) == 1
          and any(b.label == "Oui, supprimer" for b in page.button))
    next(b for b in page.button if b.label == "Oui, supprimer").click().run()
    check("then deletes the note", store().journal_entries("alice@example.com") == []
          and not page.exception, error(page))

    test_new_tracks(alice)
    test_universes()
    test_hash_demo(alice)
    test_no_secret_asked(alice)

    print("\nThe platform")
    legacy = run({"page": "home"}, entry=LEGACY_APP)
    check("the old academy_app.py entry point still renders", not legacy.exception, error(legacy))
    old = run({"page": "paths"})
    check("the old « paths » page opens the Academy home",
          'comprendre la <em class="cu">monnaie</em>' in text(old))
    for page in ("market", "community"):
        app = run({"page": page})
        body = text(app)
        check(f"{page}: says plainly it is not open", "pas encore ouvert" in body)
        check(f"{page}: offers no input of any kind",
              not app.text_input and not app.radio and not app.checkbox and not app.text_area)
    journal = run({"page": "journal"})
    check("journal: describes the trading journal, no link without an address",
          "Le journal du trader" in text(journal) and "Lien non configuré" in text(journal))
    os.environ["SENSITOR_TOOLS_URL"] = "https://outils.example"
    try:
        linked = run({"page": "journal"})
        check("journal: opens the trading side of the analytics app",
              any(b.url == "https://outils.example/?page=trading_overview" for b in linked.get("link_button")))
        linked = run({"page": "tools"})
        check("tools: opens the portfolio side of the analytics app",
              any(b.url == "https://outils.example/?page=overview" for b in linked.get("link_button")))
    finally:
        os.environ.pop("SENSITOR_TOOLS_URL", None)
    shell = run({"page": "home"})
    check("the brand reads trading, money, crypto", "TRADING · MONNAIE · CRYPTO" in text(shell))
    labels = [m.value for m in shell.sidebar.markdown]
    order = [g for g in ("APPRENDRE", "TRADER", "INVESTIR", "ÉCHANGER") for v in labels if g in v]
    check("the sidebar is grouped Apprendre, Trader, Investir, Échanger",
          order == ["APPRENDRE", "TRADER", "INVESTIR", "ÉCHANGER"], str(order))
    check("the visitor's landing speaks of trading and of money",
          "Apprendre le <em>trading</em>." in text(run({"page": "home"})))
    tools = run({"page": "tools"})
    check("tools: no link when the address is not configured",
          "Lien non configuré" in text(tools))
    sidebar = [b.label for b in run({"page": "home"}).sidebar.button]
    from sensitor.platform import spaces
    check("the sidebar lists every space, in registry order",
          [l for l in sidebar if l in {s.label for s in spaces.SPACES}] == [s.label for s in spaces.SPACES],
          str(sidebar))
    unknown = run({"page": "page-inconnue"})
    check("an unknown page falls back to the home page", "L'écosystème Sensitor" in text(unknown))

    print(f"\n{COUNT} checks, {len(FAILURES)} failures")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
