"""
Plain-data views of Academy objects, for the API and for any other client.

Kept here rather than in the router so the router stays a thin layer of HTTP
concerns, as the API's own test requires, and so the shape a lesson is served in
is defined once.
"""

from __future__ import annotations

from dataclasses import asdict

from . import progress as P
from .content import Catalog, Course, LearningPath, Lesson, Resource
from .risk import RiskPlan


def path_view(path: LearningPath) -> dict:
    return {
        "id": path.id, "number": path.number, "title": path.title,
        "summary": path.summary, "status": path.status,
        "available": path.is_available, "topics": list(path.topics),
        "courses": [course_summary(c) for c in path.courses],
    }


def course_summary(course: Course) -> dict:
    return {
        "id": course.id, "title": course.title, "summary": course.summary,
        "level": course.level, "level_label": course.level_label,
        "lessons": len(course.lessons), "duration_minutes": course.duration_minutes,
        "final_quiz_id": course.final_quiz_id,
    }


def lesson_summary(lesson: Lesson) -> dict:
    return {
        "id": lesson.id, "number": lesson.number, "title": lesson.title,
        "summary": lesson.summary, "duration_minutes": lesson.duration_minutes,
        "access": lesson.access, "module_id": lesson.module_id,
        "quiz_id": lesson.quiz_id, "version": lesson.version,
    }


def course_view(course: Course, progress: P.CourseProgress | None = None) -> dict:
    data = course_summary(course)
    data.update({
        "path_id": course.path_id, "version": course.version,
        "objectives": list(course.objectives),
        "prerequisites": list(course.prerequisites),
        "modules": [{"id": m.id, "number": m.number, "title": m.title, "summary": m.summary,
                     "lessons": [lesson_summary(l) for l in m.lessons]}
                    for m in course.modules],
        "progress": progress_view(progress) if progress else None,
    })
    return data


def progress_view(progress: P.CourseProgress) -> dict:
    return {
        "course_id": progress.course_id, "done": progress.done,
        "total": progress.total, "fraction": progress.fraction,
        "completed": sorted(progress.completed),
        "next_lesson_id": progress.next_lesson.id if progress.next_lesson else None,
        "final_quiz_passed": progress.final_quiz_passed,
    }


def lesson_view(catalog: Catalog, lesson: Lesson) -> dict:
    course = catalog.course(lesson.course_id)
    previous, following = course.neighbours(lesson.id) if course else (None, None)
    blocks = []
    for block in lesson.blocks:
        item = {"kind": block.kind, "text": block.text}
        if block.kind == "callout":
            item.update(style=block.callout_kind, title=block.title)
        elif block.kind == "figure":
            item.update(src=block.target, svg=catalog.figures.get(block.target, ""))
        elif block.kind == "exercise":
            exercise = catalog.exercise(block.target)
            item.update(exercise_id=block.target,
                        title=exercise.title if exercise else "",
                        context=exercise.context if exercise else "",
                        steps=[{"id": s.id, "prompt": s.prompt, "unit": s.unit}
                               for s in exercise.steps] if exercise else [])
        elif block.kind == "tool":
            item.update(tool=block.target)
        blocks.append(item)
    data = lesson_summary(lesson)
    data.update({
        "course_id": lesson.course_id, "objectives": list(lesson.objectives),
        "sources": list(lesson.sources), "blocks": blocks,
        "resources": [resource_view(r) for r in
                      (catalog.resource(rid) for rid in lesson.resources) if r],
        "previous_id": previous.id if previous else None,
        "next_id": following.id if following else None,
    })
    return data


def resource_view(resource: Resource) -> dict:
    return {
        "id": resource.id, "title": resource.title,
        "description": resource.description, "kind": resource.kind,
        "kind_label": resource.kind_label, "category": resource.category,
        "level": resource.level, "filename": resource.filename,
        "lessons": list(resource.lessons), "access": resource.access,
        "author": resource.author,
    }


def risk_plan_view(plan: RiskPlan) -> dict:
    return asdict(plan)
