"""
Course completion and "what next", from stored progress rows.

Pure functions over a `Course` and the set of lesson ids a member has finished.
The store holds the rows; this module decides what they mean, so the dashboard,
the course page and the API all agree on "3 / 6 lessons" and on which lesson
comes next.

Progress is counted against the lessons currently published. A completion
recorded for a lesson that has since been withdrawn is kept in the database but
does not count, so a course can never read as more than 100 % done.
"""

from __future__ import annotations

from dataclasses import dataclass

from .content import Catalog, Course, Lesson


@dataclass(frozen=True)
class CourseProgress:
    course_id: str
    done: int
    total: int
    completed: frozenset[str]
    next_lesson: Lesson | None
    final_quiz_passed: bool | None      # None when the course has no final quiz

    @property
    def fraction(self) -> float:
        return self.done / self.total if self.total else 0.0

    @property
    def started(self) -> bool:
        return self.done > 0

    @property
    def lessons_finished(self) -> bool:
        return self.total > 0 and self.done == self.total


def course_progress(course: Course, completed_ids, *,
                    passed_quizzes=frozenset()) -> CourseProgress:
    published = [lesson.id for lesson in course.lessons]
    done_ids = frozenset(set(completed_ids) & set(published))
    upcoming = next((l for l in course.lessons if l.id not in done_ids), None)
    final = None
    if course.final_quiz_id:
        final = course.final_quiz_id in set(passed_quizzes)
    return CourseProgress(course_id=course.id, done=len(done_ids), total=len(published),
                          completed=done_ids, next_lesson=upcoming,
                          final_quiz_passed=final)


def completed_by_course(rows) -> dict[str, set[str]]:
    """Group stored progress rows ({course_id, lesson_id, …}) by course."""
    grouped: dict[str, set[str]] = {}
    for row in rows:
        grouped.setdefault(row["course_id"], set()).add(row["lesson_id"])
    return grouped


def passed_quiz_ids(attempts) -> set[str]:
    return {a["quiz_id"] for a in attempts if a["passed"]}


@dataclass(frozen=True)
class NextStep:
    kind: str                   # lesson | final_quiz | explore
    course: Course | None
    lesson: Lesson | None = None


def next_step(catalog: Catalog, completed: dict[str, set[str]],
              passed: set[str]) -> NextStep:
    """
    Where to send a member who opens the dashboard.

    The most recently *started* course is not tracked separately: the first
    available course with unfinished work wins, in curriculum order, which is the
    order the programme is designed to be followed in.
    """
    courses = catalog.available_courses()
    for course in courses:
        progress = course_progress(course, completed.get(course.id, set()),
                                   passed_quizzes=passed)
        if progress.next_lesson is not None and progress.started:
            return NextStep("lesson", course, progress.next_lesson)
        if progress.lessons_finished and progress.final_quiz_passed is False:
            return NextStep("final_quiz", course)
    for course in courses:
        progress = course_progress(course, completed.get(course.id, set()),
                                   passed_quizzes=passed)
        if progress.next_lesson is not None:
            return NextStep("lesson", course, progress.next_lesson)
    return NextStep("explore", None)
