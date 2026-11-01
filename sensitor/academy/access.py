"""
Who may read what.

Three levels, declared on each lesson, quiz-bearing lesson and resource:

* `public`  content is readable by anyone, signed in or not;
* `member`  content requires a signed-in account, any account;
* `premium` content requires a signed-in account whose tier includes premium.

The level comes from the member's active entitlements (`core.permissions`,
which decides every access of the platform); there is no payment flow behind it
yet, and no content is premium by default. These functions are the Academy's
words for that one rule, for the Streamlit app and the API alike; no content is
duplicated per level.

Publication is a separate question, answered by `content` (drafts are simply
not in the catalogue). A lesson can be published and member-only, or public and
still a draft; the two never stand in for each other.
"""

from __future__ import annotations

from ..core import permissions as P
from .content import Catalog, Lesson, Quiz, Resource

SIGN_IN = "sign-in"        # why something is locked: no account
UPGRADE = "premium"        # an account, without the premium level


def has_premium(tier: str | None) -> bool:
    """Kept for earlier callers; `core.permissions` decides."""
    return P.is_premium(tier)


def _member(user_email: str | None, tier: str | None) -> P.Member:
    return P.member(user_email, tier)


def lock_reason(level: str, user_email: str | None, tier: str | None = None) -> str | None:
    """None when readable; otherwise what would unlock it."""
    return P.lock_reason(_member(user_email, tier), level)


def can_read_lesson(lesson: Lesson, user_email: str | None, tier: str | None = None) -> bool:
    return P.can_read(_member(user_email, tier), lesson.access)


def can_take_quiz(catalog: Catalog, quiz: Quiz, user_email: str | None, tier: str | None = None) -> bool:
    """A quiz attached to a lesson follows that lesson; any other is member-only."""
    lesson = catalog.find_lesson(quiz.lesson_id) if quiz.lesson_id else None
    if lesson:
        return can_read_lesson(lesson, user_email, tier)
    return P.can_read(_member(user_email, tier), "member")


def can_download(resource: Resource, user_email: str | None, tier: str | None = None) -> bool:
    return P.can_read(_member(user_email, tier), resource.access)
