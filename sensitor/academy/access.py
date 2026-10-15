"""
Who may read what.

The development policy, until access tiers are decided:

* `public` content is readable by anyone, signed in or not;
* `member` content requires a signed-in account — any account.

There is deliberately no paid tier, no VIP list and no per-user exception here.
When the access model is agreed it is added in this module, which both the
Streamlit app and the API call; nothing else decides access.

Publication is a separate question, answered by `content` (drafts are simply
not in the catalogue). A lesson can be published and member-only, or public and
still a draft; the two never stand in for each other.
"""

from __future__ import annotations

from .content import PUBLIC, Catalog, Lesson, Quiz, Resource


def can_read_lesson(lesson: Lesson, user_email: str | None) -> bool:
    return lesson.access == PUBLIC or bool(user_email)


def can_take_quiz(catalog: Catalog, quiz: Quiz, user_email: str | None) -> bool:
    """A quiz attached to a lesson follows that lesson; any other is member-only."""
    if user_email:
        return True
    lesson = catalog.find_lesson(quiz.lesson_id) if quiz.lesson_id else None
    return bool(lesson and lesson.access == PUBLIC)


def can_download(resource: Resource, user_email: str | None) -> bool:
    return resource.access == PUBLIC or bool(user_email)
