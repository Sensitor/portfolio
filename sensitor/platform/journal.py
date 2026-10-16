"""
The reflection journal of the « Psychologie et discipline » space.

Pure data and rules, no Streamlit and no database: the page, the API and the
tests all read the same entry types, prompts and limits from here.

What the journal does not do is deliberate. It stores what a member writes and
counts it. It does not read the text, score it, label the person or suggest a
diagnosis: the only figures it produces are counts and averages of the scale
the member filled in, each shown with the number of notes behind it.

Notes before and after a session carry a short routine to tick, taken from
the « Routine de séance » checklist of path 6. What is ticked is counted per
item, over the notes that offered the routine, and reported with that number.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

PRE = "pre"
POST = "post"
FREE = "free"

MAX_BODY = 4000
MOOD_MIN, MOOD_MAX = 1, 5


@dataclass(frozen=True)
class Kind:
    id: str
    label: str
    hint: str
    prompts: tuple[str, ...]
    routine: tuple[tuple[str, str], ...] = ()   # (id, label) of the items to tick


KINDS: tuple[Kind, ...] = (
    Kind(PRE, "Avant la séance", "Préparer son état et son plan avant de regarder les graphiques.",
         ("Dans quel état suis-je avant de commencer, et qu'est-ce qui l'explique ?",
          "Quel est mon plan pour cette séance, et qu'est-ce qui l'invaliderait ?",
          "Quelle est ma limite de perte aujourd'hui, et que ferai-je si je l'atteins ?"),
         (("etat", "J'ai noté mon état et ce qui pèse sur mon jugement"),
          ("contexte", "J'ai lu le contexte : structure, liquidité, annonces"),
          ("scenarios", "Chaque scénario a son invalidation écrite"),
          ("limites", "Mes limites du jour sont écrites"),
          ("risque", "Mon risque par trade est celui de ma dernière revue"))),
    Kind(POST, "Après la séance", "Revenir sur ce qui a été fait, sans refaire le marché.",
         ("Ai-je suivi mon plan ? Où m'en suis-je écarté, et à quel moment ?",
          "Quelle décision referais-je à l'identique, et laquelle non ?",
          "Qu'est-ce que je retiens pour la prochaine séance ?"),
         (("regles", "Chaque trade respectait toutes mes règles"),
          ("arret", "J'ai appliqué mes règles d'arrêt sans les renégocier"),
          ("poursuite", "Aucune entrée poursuivie, aucun trade pour me refaire"),
          ("manques", "Mes trades manqués sont notés comme tels"))),
    Kind(FREE, "Note libre", "Une pensée, une situation, une question sur sa pratique.",
         ("Ce qui me préoccupe en ce moment dans ma pratique.",
          "Une situation qui m'a fait réagir, décrite sans me juger.")),
)

MOODS = {1: "Très agité", 2: "Agité", 3: "Neutre", 4: "Calme", 5: "Très calme"}


def kind(kind_id: str) -> Kind | None:
    return next((k for k in KINDS if k.id == kind_id), None)


def kind_label(kind_id: str) -> str:
    found = kind(kind_id)
    return found.label if found else kind_id


def clean_entry(kind_id: str, body: str, *, mood: int | None = None,
                prompt: str = "") -> tuple[str, str, int | None, str]:
    """
    Check one entry before it is stored. Returns (kind, body, mood, prompt).

    The prompt must be one of the kind's own questions, or empty: it is stored
    as text so an old note keeps the question it answered if the list changes.
    """
    found = kind(kind_id)
    if found is None:
        raise ValueError("unknown entry kind")
    text = (body or "").strip()
    if not text:
        raise ValueError("an entry needs some text")
    if len(text) > MAX_BODY:
        raise ValueError(f"an entry is limited to {MAX_BODY} characters")
    if mood is not None:
        if isinstance(mood, bool) or not isinstance(mood, int) or not MOOD_MIN <= mood <= MOOD_MAX:
            raise ValueError("mood must be an integer from 1 to 5")
    question = (prompt or "").strip()
    if question and question not in found.prompts:
        raise ValueError("the prompt does not belong to this entry kind")
    return found.id, text, mood, question


def clean_checks(kind_id: str, checks) -> list[str] | None:
    """
    Check the routine items ticked on one entry. Returns them in the routine's
    order, or None when no routine was offered: a kind without one, or a
    caller that did not present it (`checks` is None).

    An empty list is a real answer, « nothing ticked », and is kept as such:
    it counts in the denominator of every item.
    """
    found = kind(kind_id)
    if found is None:
        raise ValueError("unknown entry kind")
    if checks is None:
        return None
    if not found.routine:
        if checks:
            raise ValueError("this entry kind has no routine")
        return None
    known = [item for item, _ in found.routine]
    ticked = set(checks or ())
    if not ticked <= set(known):
        raise ValueError("a routine item does not belong to this entry kind")
    return [item for item in known if item in ticked]


@dataclass(frozen=True)
class RoutineItem:
    kind: str
    id: str
    label: str
    ticked: int
    n: int          # notes of this kind that offered the routine


@dataclass(frozen=True)
class MoodAverage:
    kind: str
    average: float
    n: int


@dataclass(frozen=True)
class Summary:
    total: int
    by_kind: dict[str, int]
    last_30_days: int
    moods: tuple[MoodAverage, ...]      # one per kind with at least one rated note
    rated: int
    routine: tuple[RoutineItem, ...] = ()   # one per item, for kinds with routine notes


def summarize(entries: list[dict], *, now: datetime | None = None) -> Summary:
    """
    Counts of a member's own notes, and the average of the scale they filled in.

    Nothing here interprets the text. An average is only reported for a kind
    with at least one rated note, and always with its sample size.
    """
    now = now or datetime.now(timezone.utc)
    by_kind = {k.id: 0 for k in KINDS}
    recent = 0
    scores: dict[str, list[int]] = {k.id: [] for k in KINDS}
    for entry in entries:
        by_kind[entry["kind"]] = by_kind.get(entry["kind"], 0) + 1
        try:
            if now - datetime.fromisoformat(entry["created_at"]) <= timedelta(days=30):
                recent += 1
        except (TypeError, ValueError):
            pass
        if entry.get("mood") is not None:
            scores.setdefault(entry["kind"], []).append(int(entry["mood"]))
    moods = tuple(MoodAverage(k, sum(v) / len(v), len(v)) for k, v in scores.items() if v)
    routine = []
    for k in KINDS:
        offered = [e for e in entries if e["kind"] == k.id and e.get("checks") is not None]
        if not offered:
            continue
        for item, label in k.routine:
            routine.append(RoutineItem(k.id, item, label,
                                       sum(1 for e in offered if item in e["checks"]), len(offered)))
    return Summary(total=len(entries), by_kind=by_kind, last_30_days=recent, moods=moods,
                   rated=sum(m.n for m in moods), routine=tuple(routine))
