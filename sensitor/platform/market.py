"""
The trading room (« Salle des marchés »): a session prepared before the open,
and its review after the close.

A session is pedagogical analysis, never a signal. What it holds:

* the **context**: what matters this week and why, in a few paragraphs;
* the **calendar**: the publications of the day, with their time and weight;
* up to four **scenarios**, each written as a condition (« si … »), what it
  would teach to watch, and its **invalidation**, which is mandatory: a scenario
  without the condition that proves it wrong is an opinion, not a scenario;
* the lessons that explain what the session uses;
* optionally the address of a live, on YouTube or Vimeo only.

After the close, the **review** says what each scenario did (played out,
invalidated, never triggered), what the session teaches, and links the replay.

What a session must not contain is checked before publication: no instruction
to buy or sell, no « signal », no profit target or promise. `signal_phrases`
lists what it finds; the store refuses to publish a session that has any. The
line it draws is the one between education and personalised investment
advice, the same as the coach's review of a trade.

Only coaches write sessions; members read the published ones at the access
level the author chose. No Streamlit, no database.
"""

from __future__ import annotations

import datetime as _dt
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlparse

MAX_TITLE = 120
MAX_CONTEXT = 4000
MAX_FIELD = 600
MAX_INSTRUMENT = 24
MAX_SCENARIOS = 4
MAX_CALENDAR = 12
MAX_LESSONS = 6
MAX_TAKEAWAY = 2000

ACCESS = ("public", "member", "premium")
ACCESS_LABELS = {"public": "Accès libre", "member": "Membres", "premium": "Premium"}
WEIGHTS = ("faible", "moyenne", "forte")
OUTCOMES = {
    "joue": "Joué",
    "invalide": "Invalidé",
    "non-declenche": "Non déclenché",
}
VIDEO_HOSTS = ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "vimeo.com", "player.vimeo.com")

_LESSON = re.compile(r"^lesson:[a-z0-9-]+/[a-z0-9-]+$")
_TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

# Phrases that turn analysis into a signal or a promise. Matched on words, after
# accents and case are removed; the author rephrases before publishing.
_SIGNAL_PATTERNS = (
    (r"\b(achetez|achetons|j'achete|on achete)\b", "« achetez » : une instruction d'achat"),
    (r"\b(vendez|vendons|je vends|on vend)\b", "« vendez » : une instruction de vente"),
    (r"\bprenez (une )?position\b", "« prenez position » : une instruction"),
    (r"\bentrez (a l'achat|a la vente|long|short)\b", "« entrez » : une instruction"),
    (r"\bsignal(aux)? (d'achat|de vente|d'entree)\b", "un signal d'achat ou de vente"),
    (r"\b(take profit|objectif de (cours|prix|gain)|prise de profit a)\b", "un objectif de gain"),
    (r"\b(gain|profit|resultat|rendement)s? garanti(e|s|es)?\b|\bsans risque\b|\ba coup sur\b",
     "une promesse de résultat"),
    (r"\b(buy|sell) (now|signal)\b|\bcopy ?trading\b", "une instruction d'achat ou de vente"),
)


def _fold(text: str) -> str:
    """Lowercase, accents removed: « Achetez » and « ACHETEZ » read the same."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def signal_phrases(*texts: str) -> list[str]:
    """What would make a session read as a signal or a promise, once each."""
    folded = " ".join(_fold(t) for t in texts if t)
    return [label for pattern, label in _SIGNAL_PATTERNS if re.search(pattern, folded)]


def _text(value, limit: int, name: str, *, required: bool = False) -> str:
    text = (value or "").strip()
    if required and not text:
        raise ValueError(f"{name} est obligatoire")
    if len(text) > limit:
        raise ValueError(f"{name} est limité à {limit} caractères")
    return text


def clean_video_url(url: str) -> str:
    """An https address on YouTube or Vimeo, or an empty string. Anything else is refused."""
    url = (url or "").strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in VIDEO_HOSTS:
        raise ValueError("le lien du live ou du replay doit être une adresse https YouTube ou Vimeo")
    return url


def clean_lessons(lessons) -> list[str]:
    out = []
    for item in lessons or []:
        if not _LESSON.match(str(item)):
            raise ValueError("une leçon liée doit être désignée par « lesson:cours/leçon »")
        if item not in out:
            out.append(str(item))
    if len(out) > MAX_LESSONS:
        raise ValueError(f"au plus {MAX_LESSONS} leçons liées")
    return out


def parse_calendar(text: str) -> list[dict]:
    """
    One publication per line: « 14:30 | Emploi américain | forte ». The time is
    Paris time; the weight is faible, moyenne or forte (moyenne when left out).
    """
    items = []
    for number, line in enumerate((text or "").splitlines(), start=1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2 or not _TIME.match(parts[0]) or not parts[1]:
            raise ValueError(f"ligne {number} du calendrier : écrivez « HH:MM | publication | poids »")
        weight = _fold(parts[2]) if len(parts) > 2 and parts[2] else "moyenne"
        if weight not in WEIGHTS:
            raise ValueError(f"ligne {number} du calendrier : le poids est faible, moyenne ou forte")
        items.append({"time": parts[0], "event": _text(parts[1], 160, "une publication"), "weight": weight})
    if len(items) > MAX_CALENDAR:
        raise ValueError(f"au plus {MAX_CALENDAR} publications au calendrier")
    return sorted(items, key=lambda i: i["time"])


def calendar_text(items: list[dict]) -> str:
    """The calendar back in its one-line-per-publication form, for editing."""
    return "\n".join(f"{i['time']} | {i['event']} | {i['weight']}" for i in items or [])


def clean_scenario(raw: dict) -> dict | None:
    """A scenario, or None when every field is empty (an unused slot of the form)."""
    fields = {k: (raw.get(k) or "").strip() for k in ("instrument", "title", "condition", "observe", "invalidation")}
    if not any(fields.values()):
        return None
    return {
        "instrument": _text(fields["instrument"], MAX_INSTRUMENT, "l'instrument", required=True).upper(),
        "title": _text(fields["title"], MAX_TITLE, "le titre du scénario", required=True),
        "condition": _text(fields["condition"], MAX_FIELD, "la condition", required=True),
        "observe": _text(fields["observe"], MAX_FIELD, "ce que l'on observe"),
        "invalidation": _text(fields["invalidation"], MAX_FIELD,
                              "l'invalidation (un scénario sans invalidation n'en est pas un)", required=True),
        "lessons": clean_lessons(raw.get("lessons")),
    }


def clean_session(raw: dict) -> dict:
    """The fields of a session, checked. Raises ValueError with a sentence for the author."""
    try:
        day = _dt.date.fromisoformat(str(raw.get("session_date") or ""))
    except ValueError:
        raise ValueError("la date de la séance est obligatoire") from None
    access = raw.get("access") or "member"
    if access not in ACCESS:
        raise ValueError("niveau d'accès inconnu")
    scenarios = [s for s in (clean_scenario(r) for r in raw.get("scenarios") or []) if s]
    if len(scenarios) > MAX_SCENARIOS:
        raise ValueError(f"au plus {MAX_SCENARIOS} scénarios")
    return {
        "session_date": day.isoformat(),
        "title": _text(raw.get("title"), MAX_TITLE, "le titre") or default_title(day),
        "access": access,
        "content": {
            "context": _text(raw.get("context"), MAX_CONTEXT, "le contexte", required=True),
            "calendar": raw["calendar"] if isinstance(raw.get("calendar"), list) else parse_calendar(raw.get("calendar", "")),
            "scenarios": scenarios,
            "live_url": clean_video_url(raw.get("live_url", "")),
            "lessons": clean_lessons(raw.get("lessons")),
        },
    }


def publishable(session: dict) -> list[str]:
    """Why a cleaned session cannot be published yet; empty when it can."""
    content = session["content"]
    problems = []
    if not content["scenarios"]:
        problems.append("au moins un scénario, avec son invalidation")
    texts = [session["title"], content["context"]]
    for s in content["scenarios"]:
        texts += [s["title"], s["condition"], s["observe"], s["invalidation"]]
    problems += signal_phrases(*texts)
    return problems


def clean_review(raw: dict, scenarios: list[dict]) -> dict:
    """The review after the close: one outcome per scenario, the takeaway, the replay."""
    given = raw.get("outcomes") or []
    outcomes = []
    for index in range(len(scenarios)):
        item = given[index] if index < len(given) else {}
        outcome = item.get("outcome") or ""
        if outcome not in OUTCOMES:
            raise ValueError(f"le scénario {index + 1} attend son issue : joué, invalidé ou non déclenché")
        outcomes.append({"outcome": outcome, "comment": _text(item.get("comment"), MAX_FIELD, "le commentaire")})
    takeaway = _text(raw.get("takeaway"), MAX_TAKEAWAY, "ce que la séance enseigne", required=True)
    problems = signal_phrases(takeaway, *(o["comment"] for o in outcomes))
    if problems:
        raise ValueError("le bilan contient " + ", ".join(problems) + " : reformulez avant de l'enregistrer")
    return {"outcomes": outcomes, "takeaway": takeaway,
            "replay_url": clean_video_url(raw.get("replay_url", "")),
            "lessons": clean_lessons(raw.get("lessons"))}


MONTHS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre",
          "octobre", "novembre", "décembre")
DAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")


def date_label(day: _dt.date | str, *, with_day: bool = True) -> str:
    day = _dt.date.fromisoformat(day) if isinstance(day, str) else day
    head = f"{DAYS[day.weekday()]} " if with_day else ""
    return f"{head}{day.day} {MONTHS[day.month - 1]} {day.year}"


def default_title(day: _dt.date) -> str:
    return f"Séance du {date_label(day)}"


@dataclass(frozen=True)
class Tally:
    played: int
    invalidated: int
    untriggered: int

    @property
    def total(self) -> int:
        return self.played + self.invalidated + self.untriggered


def tally(reviews: list[dict]) -> Tally:
    """Outcomes over many reviewed sessions: how often scenarios played, failed or never started."""
    counts = {k: 0 for k in OUTCOMES}
    for review in reviews:
        for item in (review or {}).get("outcomes", []):
            if item.get("outcome") in counts:
                counts[item["outcome"]] += 1
    return Tally(counts["joue"], counts["invalide"], counts["non-declenche"])
