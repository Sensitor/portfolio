"""
Accompaniment requests: an accompanied member's question to the team, and the
answer.

The frame is the one of the trade reviews (`trading.coaching`): the answer is
pedagogical, about the member's method, plan, routine or organisation, never a
recommendation to buy or sell an asset, an amount or a moment. Both forms say
so, and the coach sees a pseudonym, not the address.

No Streamlit, no database.
"""

from __future__ import annotations

TOPICS = {
    "methode": "Méthode et analyse",
    "plan": "Plan de trading et gestion du risque",
    "psychologie": "Psychologie et discipline",
    "organisation": "Organisation et routine",
    "academy": "Une leçon de l'Academy",
    "autre": "Autre",
}
MAX_QUESTION, MAX_ANSWER = 2000, 5000
DASHES = (chr(0x2014), chr(0x2013))
FRAME = ("Une réponse pédagogique sur votre méthode, votre plan ou votre organisation. Ce n'est jamais une "
         "recommandation d'acheter ou de vendre un actif, ni un conseil sur un montant ou un moment : Sensitor "
         "ne fournit pas de conseil en investissement personnalisé.")
COACH_FRAME = ("Répondez sur la méthode, le processus et les leçons à reprendre. Pas de recommandation sur un "
               "actif, un montant ou un moment d'entrée : c'est la limite entre la formation et le conseil en "
               "investissement.")


class SupportError(ValueError):
    """What is wrong with the form, in French."""


def _clean(text: str, limit: int, what: str) -> str:
    text = (text or "").strip()
    if len(text) < 20:
        raise SupportError(f"{what} est trop court : quelques phrases aident à bien répondre.")
    if len(text) > limit:
        raise SupportError(f"{what} dépasse {limit} caractères.")
    for dash in DASHES:
        text = text.replace(dash, ",")
    return text


def clean_request(topic: str, question: str) -> dict:
    if topic not in TOPICS:
        raise SupportError("Choisissez un thème.")
    return {"topic": topic, "question": _clean(question, MAX_QUESTION, "La question")}


def clean_answer(answer: str) -> str:
    return _clean(answer, MAX_ANSWER, "La réponse")
