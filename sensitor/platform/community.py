"""
The community: discussions between members, by theme and by course, under a
charter, with reporting and moderation.

What this module decides, with no Streamlit and no database:

* the themes, the charter and the report reasons;
* what a title and a message may contain (lengths, long dashes replaced);
* the refusal of a message that looks like a secret: a recovery phrase
  (twelve or more plain lowercase words in a row), a private key (64
  hexadecimal characters, a WIF key) or an extended private key (`xprv`). The
  house rule is never to ask for one; the community must not become the place
  where one is pasted;
* how an author is shown: their display name, or a stable pseudonym; never
  their address.

Hosting obligations: every message has a « Signaler » action open to every
member, each report is acknowledged and examined by an administrator, and a
hidden message keeps the reason shown to its author. The texts are in
`content/legal/conditions.md`.
"""

from __future__ import annotations

import re

from ..trading.coaching import pseudonym

THEMES = {
    "trading": "Trading",
    "crypto": "Monnaie et crypto",
    "methode": "Méthode et psychologie",
    "experience": "Retours d'expérience",
    "plateforme": "Questions sur Sensitor",
}
CHARTER = (
    ("Pédagogie, pas de signaux", "Pas de recommandation d'acheter ou de vendre, pas de promesse de gain, pas "
     "d'appel à suivre un trade. Une analyse partagée dit ce qui l'invaliderait."),
    ("Jamais de secret", "Ne publiez jamais de phrase de récupération, de clé privée ni de mot de passe. Personne "
     "chez Sensitor ne vous les demandera."),
    ("Pas de publicité", "Pas de parrainage, de lien d'affiliation ni de promotion d'un service ou d'un actif."),
    ("Des chiffres sourcés", "Un chiffre vient avec sa source ; un résultat personnel se présente comme tel, sans "
     "mise en scène."),
    ("Respect", "Pas d'injure, de harcèlement ni de propos discriminatoire. On discute des idées, pas des personnes."),
)
REPORT_REASONS = {
    "signal": "Signal d'achat ou de vente, promesse de gain",
    "secret": "Phrase de récupération, clé privée ou mot de passe",
    "promotion": "Publicité, parrainage ou affiliation",
    "respect": "Injure, harcèlement ou discrimination",
    "illegal": "Contenu illicite",
    "other": "Autre",
}
MAX_TITLE, MAX_BODY, MAX_DETAILS = 140, 5000, 600
DASHES = (chr(0x2014), chr(0x2013))

_WORD_RUN = re.compile(r"(?:\b[a-z]{3,8}\b[\s,]+){11,}\b[a-z]{3,8}\b")
_HEX_KEY = re.compile(r"\b(?:0x)?[0-9a-fA-F]{64}\b")
_WIF = re.compile(r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b")
_XPRV = re.compile(r"\b[xyzt]prv[1-9A-HJ-NP-Za-km-z]{100,}\b")


class CommunityError(ValueError):
    """What is wrong with the message, in French, for the page to show."""


def secret_in(text: str) -> str | None:
    """Why a text looks like it carries a secret, or None."""
    if _XPRV.search(text or ""):
        return "une clé privée étendue"
    if _HEX_KEY.search(text or "") or _WIF.search(text or ""):
        return "une clé privée"
    if _WORD_RUN.search(text or ""):
        return "une phrase de récupération"
    return None


def _clean(text: str, limit: int, what: str, *, minimum: int = 1) -> str:
    text = (text or "").strip()
    for dash in DASHES:
        text = text.replace(dash, ",")
    if len(text) < minimum:
        raise CommunityError(f"{what} est trop court.")
    if len(text) > limit:
        raise CommunityError(f"{what} dépasse {limit} caractères.")
    found = secret_in(text)
    if found:
        raise CommunityError(f"Ce message semble contenir {found}. Il n'est pas publié : ne partagez jamais ce "
                             "secret, avec personne. S'il a été exposé, considérez les fonds concernés comme à "
                             "risque et déplacez-les vers un nouveau portefeuille.")
    return text


def clean_thread(theme: str, title: str, body: str) -> dict:
    if theme not in THEMES:
        raise CommunityError("Choisissez un thème.")
    return {"theme": theme, "title": " ".join(_clean(title, MAX_TITLE, "Le titre", minimum=8).split()),
            "body": _clean(body, MAX_BODY, "Le message", minimum=20)}


def clean_post(body: str) -> str:
    return _clean(body, MAX_BODY, "Le message", minimum=2)


def clean_report(reason: str, details: str) -> dict:
    if reason not in REPORT_REASONS:
        raise CommunityError("Choisissez un motif.")
    details = (details or "").strip()[:MAX_DETAILS]
    for dash in DASHES:
        details = details.replace(dash, ",")
    return {"reason": reason, "details": details}


def author_label(display_name: str | None, email: str | None) -> str:
    """The name a member chose, or a stable pseudonym; never the address. « Ancien membre » once gone."""
    if not email:
        return "Ancien membre"
    name = " ".join((display_name or "").split())
    return name if name else pseudonym(email)
