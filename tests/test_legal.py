"""
The legal pages: legal notice, terms of use, privacy policy.

    python tests/test_legal.py

They render for anyone, every page links to them, nothing in them is invented
(an empty detail reads « [à compléter] » and the page says the text is not
final), and the privacy policy says what the code does: the cookie, the
lifetimes, and every table that holds a member's data.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from html import unescape
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SENSITOR_DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="sensitor-legal-"), "l.db")
os.environ["SENSITOR_AUTH"] = "multi"

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sensitor_app.py")
CHECKS: list[tuple[str, bool, str]] = []
DASHES = (chr(0x2014), chr(0x2013))
# Where the privacy policy speaks of each table that holds a member's data.
TABLE_WORDS = {
    "users": "Votre compte", "sessions": "Vos sessions", "account_tokens": "lien de réinitialisation",
    "portfolios": "allocations enregistrées", "workspace": "portefeuille de travail", "snapshots": "historiques",
    "trading_accounts": "numéro du compte", "trades": "Votre journal de trading", "lesson_progress": "leçons terminées",
    "quiz_attempts": "réponses aux quiz", "journal_entries": "journal de réflexion", "trading_plans": "plan de trading",
    "trade_reviews": "demandes de revue", "market_sessions": "salle des marchés",
}


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def visible(app: AppTest) -> str:
    return unescape("\n".join(m.value for m in app.markdown if not m.value.lstrip().startswith("<style")))


def main() -> int:
    from sensitor.core import auth
    from sensitor.database.models import TABLES
    from sensitor.platform import legal, spaces
    from sensitor.platform.ui import runtime

    print("\nThe texts")
    for page, (filename, _title) in legal.PAGES.items():
        text = (legal.ROOT / filename).read_text(encoding="utf-8")
        check(f"{filename}: no long dash", not any(d in text for d in DASHES))
    data = legal.details()
    check("the publisher's details are empty until the founder fills them in: nothing is invented",
          not any(data["editeur"].values()) and not any(data["hebergement"].values()) and data["relu"] is False)
    check("so the pre-launch list names every one of them", {"editeur.raison_sociale", "editeur.siege",
          "editeur.directeur_publication", "hebergement.application"} <= set(legal.missing())
          and not legal.ready())

    policy = (legal.ROOT / "confidentialite.md").read_text(encoding="utf-8")
    check("the privacy policy names the one cookie the code sets", f"`{runtime.COOKIE}`" in policy)
    check("and the lifetimes the code applies", f"{auth.SESSION_DAYS} jours" in policy
          and "une heure" in policy and auth.RESET_MINUTES == 60
          and f"{auth.VERIFY_HOURS} heures" in policy)
    check("every table that holds a member's data is in the privacy policy",
          set(TABLE_WORDS) == set(TABLES) and all(word in policy for word in TABLE_WORDS.values()),
          str([t for t, w in TABLE_WORDS.items() if w not in policy] + sorted(set(TABLES) - set(TABLE_WORDS))))
    check("it says the seed phrase, the private key and the exchange password are never asked for",
          "phrase de récupération" in policy and "clé privée" in policy and "mot de passe d'exchange" in policy)

    print("\nThe pages")
    for page in legal.PAGES:
        check(f"« {page} » is a platform page with a renderer", page in spaces.PLATFORM_PAGES)
        app = AppTest.from_file(APP, default_timeout=120)
        app.session_state["ac_route"] = {"page": page}
        app.run()
        body = visible(app)
        doc = legal.document(page)
        check(f"« {page} » renders for a visitor, with the banner and the details to complete",
              not app.exception and doc.title in body and "Texte en cours de finalisation" in body
              and legal.TO_COMPLETE in body, str(app.exception[0].value)[:200] if app.exception else "")
    home = AppTest.from_file(APP, default_timeout=120)
    home.session_state["ac_route"] = {"page": "home"}
    home.run()
    links = "\n".join(m.value for m in home.markdown)
    check("the footer of every page links to the three texts, with plain links",
          all(f'href="?page={p}"' in links for p in legal.PAGES))

    print("\nOnce the founder has filled them in")
    root = Path(tempfile.mkdtemp(prefix="sensitor-legal-root-"))
    for item in legal.ROOT.iterdir():
        shutil.copy(item, root / item.name)
    filled = (root / "editeur.toml").read_text(encoding="utf-8").replace('relu = false', 'relu = true')
    filled = filled.replace('= ""', '= "valeur de test"')
    (root / "editeur.toml").write_text(filled, encoding="utf-8")
    doc = legal.document("mentions", root)
    check("no detail left to complete, the text reviewed: the pages are ready",
          legal.ready(root) and not doc.missing and legal.TO_COMPLETE not in doc.body and "valeur de test" in doc.body)

    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
