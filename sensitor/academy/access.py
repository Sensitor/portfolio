"""
Who may read what.

Three levels, declared on each lesson, quiz-bearing lesson and resource:

* `public`  content is readable by anyone, signed in or not;
* `member`  content requires a signed-in account, any account;
* `premium` content requires a signed-in account whose tier includes premium.

The tier is the `users.tier` column. There is no payment flow behind it yet:
it is set by hand until there is demand for an offer, and no content is
premium by default. One rule decides, here, for the Streamlit app and the API
alike; nothing else decides access, and no content is duplicated per tier.

Publication is a separate question, answered by `content` (drafts are simply
not in the catalogue). A lesson can be published and member-only, or public and
still a draft; the two never stand in for each other.
"""

from __future__ import annotations

from .content import MEMBER, PREMIUM, PUBLIC, Catalog, Lesson, Quiz, Resource

PREMIUM_TIERS = frozenset({"pro", "premium"})

SIGN_IN = "sign-in"        # why something is locked: no account
UPGRADE = "premium"        # an account, without the premium tier


def has_premium(tier: str | None) -> bool:
    return (tier or "").strip().lower() in PREMIUM_TIERS


def _allowed(level: str, user_email: str | None, tier: str | None) -> bool:
    if level == PUBLIC:
        return True
    if level == MEMBER:
        return bool(user_email)
    if level == PREMIUM:
        return bool(user_email) and has_premium(tier)
    return False


def lock_reason(level: str, user_email: str | None, tier: str | None = None) -> str | None:
    """None when readable; otherwise what would unlock it."""
    if _allowed(level, user_email, tier):
        return None
    return UPGRADE if user_email and level == PREMIUM else SIGN_IN


def can_read_lesson(lesson: Lesson, user_email: str | None, tier: str | None = None) -> bool:
    return _allowed(lesson.access, user_email, tier)


def can_take_quiz(catalog: Catalog, quiz: Quiz, user_email: str | None, tier: str | None = None) -> bool:
    """A quiz attached to a lesson follows that lesson; any other is member-only."""
    lesson = catalog.find_lesson(quiz.lesson_id) if quiz.lesson_id else None
    if lesson:
        return can_read_lesson(lesson, user_email, tier)
    return bool(user_email)


def can_download(resource: Resource, user_email: str | None, tier: str | None = None) -> bool:
    return _allowed(resource.access, user_email, tier)
