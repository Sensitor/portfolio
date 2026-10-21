"""
Requests for a coach's review of one trade, and the coach's answer.

The journal is private. A member can choose to send one closed trade to the
Sensitor coaches with a question; what is sent is a frozen copy of that trade
(with the member's notes on it), its automatic review against the plan, and the
plan itself. Nothing else of the journal leaves the member's account, and the
coach sees a pseudonym, not the address.

The answer is pedagogical: how the trade was read, executed and managed, and
whether the member's own plan was followed, with the lessons to work on. It is
about a closed trade, never a recommendation on a future one, which is the line
between education and personalised investment advice; the coach's form says so.

Quotas are per calendar month and per tier. There is no billing: the tier is set
by hand, like every other access level, and the numbers below are a starting
point for the founder to adjust.

No Streamlit, no database.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from .models import Trade

MONTHLY_QUOTA = {"free": 1, "member": 1, "pro": 8, "premium": 8}
MAX_QUESTION = 1500
MAX_TEXT = 4000
MAX_LESSONS = 4

AXES = (
    ("contexte", "Lecture du contexte"),
    ("execution", "Exécution"),
    ("risque", "Gestion du risque"),
    ("discipline", "Respect du plan"),
)
SCORE_LABELS = {1: "À reprendre", 2: "Fragile", 3: "Correct", 4: "Solide", 5: "Exemplaire"}

_LESSON = re.compile(r"^lesson:[a-z0-9-]+/[a-z0-9-]+$")


def monthly_quota(tier: str | None) -> int:
    return MONTHLY_QUOTA.get((tier or "free").strip().lower(), MONTHLY_QUOTA["free"])


def month_start(now: datetime | None = None) -> str:
    """The first instant of the current month, as the ISO text the store compares with."""
    now = now or datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def pseudonym(email: str) -> str:
    """
    A stable label for a member, so a coach can follow one person's requests
    without seeing who they are.
    """
    digest = hashlib.sha256(f"sensitor-review:{(email or '').strip().lower()}".encode()).hexdigest()
    return f"Membre {digest[:6].upper()}"


def snapshot(trade: Trade) -> dict:
    """What the coach receives of a trade: everything the member recorded, not the broker payload."""
    data = trade.to_dict()
    data.pop("raw", None)
    for key in ("image_pre", "image_post", "image_annotated"):
        data.pop(key, None)
    return data


def clean_question(text: str) -> str:
    question = (text or "").strip()
    if not question:
        raise ValueError("une question aide le coach : écrivez ce que vous voulez savoir")
    if len(question) > MAX_QUESTION:
        raise ValueError(f"la question est limitée à {MAX_QUESTION} caractères")
    return question


def can_request(trade: Trade, *, used: int, quota: int, already_open: bool) -> str | None:
    """None when the request may be sent; otherwise why not, in French."""
    if not trade.is_closed:
        return "seul un trade clôturé peut être revu"
    if trade.source == "demo":
        return "un trade de l'exemple ne peut pas être envoyé"
    if already_open:
        return "une demande est déjà en cours pour ce trade"
    if used >= quota:
        return (f"vous avez utilisé vos {quota} revue{'s' if quota > 1 else ''} de ce mois ; "
                "le compteur repart le 1er du mois")
    return None


def clean_feedback(data: dict) -> dict:
    """Check a coach's answer before it is stored. Raises ValueError in French."""
    texts = {}
    for key in ("strengths", "improve", "comment"):
        value = (data.get(key) or "").strip()
        if len(value) > MAX_TEXT:
            raise ValueError(f"un champ est limité à {MAX_TEXT} caractères")
        texts[key] = value
    if not (texts["improve"] or texts["comment"]):
        raise ValueError("écrivez au moins ce qui est à travailler ou un commentaire")
    scores = {}
    for axis, _ in AXES:
        value = (data.get("scores") or {}).get(axis)
        if value in (None, ""):
            continue
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError("une note va de 1 à 5")
        scores[axis] = value
    lessons = list(dict.fromkeys(data.get("lessons") or ()))
    if len(lessons) > MAX_LESSONS:
        raise ValueError(f"au plus {MAX_LESSONS} leçons recommandées")
    if any(not _LESSON.match(str(t)) for t in lessons):
        raise ValueError("une leçon recommandée n'est pas reconnue")
    return {**texts, "scores": scores, "lessons": lessons}
