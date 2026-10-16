"""
Academy content: paths, courses, lessons, quizzes, exercises and resources.

Where content lives
-------------------
In version-controlled files under `content/academy/`, not in the database:

    curriculum.toml                 the learning paths, in order
    courses/<course>/course.toml    a course: objectives, modules, lesson order
    courses/<course>/lessons/*.md   one lesson each — TOML front matter between
                                    `+++` lines, then the body (see `markup`)
    quizzes/*.toml                  quizzes and knowledge checks
    exercises/*.toml                numeric practical exercises
    resources/resources.toml        the library, pointing at real files
    figures/*.svg                   original diagrams used by lessons

Files rather than tables because the first authoring workflow is an editor and a
pull request: every change to a lesson or an answer key is reviewed, versioned
and revertible, and nothing about it depends on an admin screen that does not
exist yet. User data — progress and quiz attempts — is what goes in the
database.

Publication is not authorisation
--------------------------------
`status` (draft / published / planned) says whether a piece of content is
finished. `access` (public / member) says who may read it. The two are separate
fields so that unpublishing a lesson and restricting it can never be confused.
Drafts are left out of the catalogue unless `include_drafts=True`, which the app
only passes when `SENSITOR_ACADEMY_PREVIEW=1` — a development setting.

Everything is validated on load. A broken reference — a lesson pointing at a
quiz that does not exist, a figure that is not on disk, a question with no
correct answer — raises `ContentError` listing every problem, so a mistake in
an answer key is caught by the test suite rather than by a member.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import markup

CONTENT_ROOT = Path(__file__).resolve().parents[2] / "content" / "academy"

PUBLISHED = "published"
DRAFT = "draft"
PLANNED = "planned"            # paths only: announced in the curriculum, not readable
STATUSES = {PUBLISHED, DRAFT}
PATH_STATUSES = {PUBLISHED, PLANNED}

PUBLIC = "public"
MEMBER = "member"
ACCESS = {PUBLIC, MEMBER}

LEVELS = {"debutant": "Débutant", "intermediaire": "Intermédiaire", "avance": "Avancé"}
FEEDBACK = {"immediate", "deferred"}
QUESTION_KINDS = {"single", "multiple"}
RESOURCE_KINDS = {"fiche": "Fiche de révision", "checklist": "Checklist",
                  "guide": "Guide", "ebook": "Ebook"}


class ContentError(ValueError):
    """The content tree is invalid. `problems` lists every issue found."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("contenu Academy invalide :\n  - " + "\n  - ".join(problems))


# =============================================================================
# MODELS
# =============================================================================

@dataclass(frozen=True)
class Option:
    id: str
    text: str
    correct: bool
    explanation: str


@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    kind: str
    options: tuple[Option, ...]
    explanation: str = ""
    lesson_id: str | None = None

    @property
    def correct_ids(self) -> frozenset[str]:
        return frozenset(o.id for o in self.options if o.correct)

    def option(self, option_id: str) -> Option | None:
        return next((o for o in self.options if o.id == option_id), None)


@dataclass(frozen=True)
class Quiz:
    id: str
    title: str
    course_id: str | None
    lesson_id: str | None
    pass_threshold: float
    feedback: str
    version: int
    status: str
    questions: tuple[Question, ...]
    intro: str = ""

    def question(self, question_id: str) -> Question | None:
        return next((q for q in self.questions if q.id == question_id), None)


@dataclass(frozen=True)
class ExerciseStep:
    id: str
    prompt: str
    unit: str
    answer: float
    tolerance: float
    solution: str


@dataclass(frozen=True)
class Exercise:
    id: str
    title: str
    context: str
    steps: tuple[ExerciseStep, ...]
    conclusion: str = ""


@dataclass(frozen=True)
class Lesson:
    id: str
    course_id: str
    module_id: str
    number: int                    # 1-based position within the course
    title: str
    summary: str
    duration_minutes: int | None
    access: str
    status: str
    version: int
    objectives: tuple[str, ...]
    blocks: tuple[markup.Block, ...]
    quiz_id: str | None = None
    resources: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()

    @property
    def is_public(self) -> bool:
        return self.access == PUBLIC


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    lessons: tuple[Lesson, ...]
    summary: str = ""
    number: int = 0                # 1-based chapter number within the course

    @property
    def duration_minutes(self) -> int | None:
        durations = [l.duration_minutes for l in self.lessons]
        return None if not durations or None in durations else sum(durations)


@dataclass(frozen=True)
class Course:
    id: str
    path_id: str
    title: str
    summary: str
    level: str
    status: str
    version: int
    objectives: tuple[str, ...]
    prerequisites: tuple[str, ...]
    modules: tuple[Module, ...]
    final_quiz_id: str | None = None

    @property
    def lessons(self) -> tuple[Lesson, ...]:
        return tuple(lesson for module in self.modules for lesson in module.lessons)

    @property
    def level_label(self) -> str:
        return LEVELS.get(self.level, self.level)

    @property
    def duration_minutes(self) -> int | None:
        """Sum of lesson durations, or None if any lesson has no estimate."""
        durations = [lesson.duration_minutes for lesson in self.lessons]
        if not durations or any(d is None for d in durations):
            return None
        return sum(durations)

    def lesson(self, lesson_id: str) -> Lesson | None:
        return next((l for l in self.lessons if l.id == lesson_id), None)

    def module_of(self, lesson: Lesson) -> Module | None:
        return next((m for m in self.modules if m.id == lesson.module_id), None)

    def neighbours(self, lesson_id: str) -> tuple[Lesson | None, Lesson | None]:
        lessons = self.lessons
        for index, lesson in enumerate(lessons):
            if lesson.id == lesson_id:
                previous = lessons[index - 1] if index > 0 else None
                following = lessons[index + 1] if index + 1 < len(lessons) else None
                return previous, following
        return None, None


@dataclass(frozen=True)
class LearningPath:
    id: str
    number: int
    title: str
    summary: str
    status: str
    courses: tuple[Course, ...]
    topics: tuple[str, ...] = ()

    @property
    def is_available(self) -> bool:
        return self.status == PUBLISHED and bool(self.courses)


@dataclass(frozen=True)
class Resource:
    id: str
    title: str
    description: str
    kind: str
    category: str
    level: str
    file: Path
    lessons: tuple[str, ...] = ()
    author: str = "Sensitor"
    access: str = MEMBER
    pdf: Path | None = None

    @property
    def kind_label(self) -> str:
        return RESOURCE_KINDS.get(self.kind, self.kind)

    @property
    def pdf_name(self) -> str | None:
        return self.pdf.name if self.pdf else None

    def read_pdf(self) -> bytes:
        return self.pdf.read_bytes()

    @property
    def filename(self) -> str:
        return self.file.name

    def read_text(self) -> str:
        return self.file.read_text(encoding="utf-8")


@dataclass
class Catalog:
    paths: tuple[LearningPath, ...]
    courses: dict[str, Course]
    quizzes: dict[str, Quiz]
    exercises: dict[str, Exercise]
    resources: dict[str, Resource]
    figures: dict[str, str]
    root: Path
    include_drafts: bool = False

    def course(self, course_id: str) -> Course | None:
        return self.courses.get(course_id)

    def lesson(self, course_id: str, lesson_id: str) -> Lesson | None:
        course = self.course(course_id)
        return course.lesson(lesson_id) if course else None

    def quiz(self, quiz_id: str | None) -> Quiz | None:
        return self.quizzes.get(quiz_id) if quiz_id else None

    def exercise(self, exercise_id: str) -> Exercise | None:
        return self.exercises.get(exercise_id)

    def resource(self, resource_id: str) -> Resource | None:
        return self.resources.get(resource_id)

    def path(self, path_id: str) -> LearningPath | None:
        return next((p for p in self.paths if p.id == path_id), None)

    def available_courses(self) -> list[Course]:
        return [c for p in self.paths if p.is_available for c in p.courses]

    def public_lessons(self) -> list[Lesson]:
        return [l for c in self.available_courses() for l in c.lessons if l.is_public]

    def resources_for_lesson(self, lesson_id: str) -> list[Resource]:
        return [r for r in self.resources.values() if lesson_id in r.lessons]

    def find_lesson(self, lesson_id: str) -> Lesson | None:
        for course in self.courses.values():
            lesson = course.lesson(lesson_id)
            if lesson:
                return lesson
        return None


# =============================================================================
# LOADING
# =============================================================================

def preview_enabled() -> bool:
    """Whether drafts are shown. A development setting, read on every call."""
    return os.getenv("SENSITOR_ACADEMY_PREVIEW", "").strip() == "1"


def fingerprint(root: Path | str | None = None) -> str:
    """Cheap change marker for caches: newest modification time in the tree."""
    root = Path(root or CONTENT_ROOT)
    newest = 0.0
    count = 0
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            count += 1
            newest = max(newest, os.path.getmtime(os.path.join(dirpath, name)))
    return f"{count}:{newest:.6f}"


_CACHE: dict[tuple, Catalog] = {}


def cached_catalog(root: Path | str | None = None, *,
                   include_drafts: bool | None = None) -> Catalog:
    """
    The catalogue, reloaded only when a content file changes.

    Content is the same for every visitor, so sharing one parsed copy across
    sessions leaks nothing. Nothing user-specific is ever cached here.
    """
    root = Path(root or CONTENT_ROOT)
    drafts = preview_enabled() if include_drafts is None else include_drafts
    key = (str(root), drafts, fingerprint(root))
    catalog = _CACHE.get(key)
    if catalog is None:
        catalog = load_catalog(root, include_drafts=drafts)
        _CACHE.clear()
        _CACHE[key] = catalog
    return catalog


def load_catalog(root: Path | str | None = None, *,
                 include_drafts: bool = False) -> Catalog:
    """Load and validate the whole content tree. Raises `ContentError`."""
    loader = _Loader(Path(root or CONTENT_ROOT), include_drafts=include_drafts)
    catalog = loader.load()
    if loader.problems:
        raise ContentError(loader.problems)
    return catalog


def validate(root: Path | str | None = None, *, include_drafts: bool = True) -> list[str]:
    """Every problem in the tree, without raising. Used by the CLI."""
    loader = _Loader(Path(root or CONTENT_ROOT), include_drafts=include_drafts)
    catalog = loader.load()
    problems = list(loader.problems)
    if not problems:
        from .printable import read_manifest, source_hash
        built = read_manifest(catalog.root / "resources")
        for resource in catalog.resources.values():
            if resource.pdf and built.get(resource.pdf_name) != source_hash(resource.file):
                problems.append(f"resources/{resource.pdf_name} : PDF à reconstruire, sa source a "
                                "changé (python scripts/build_resource_pdfs.py)")
        for course in catalog.courses.values():
            for lesson in course.lessons:
                if lesson.status == PUBLISHED:
                    problems += [f"{course.id}/{lesson.id} : {m}"
                                 for m in completeness(lesson, catalog)]
    return problems


def completeness(lesson: Lesson, catalog: Catalog) -> list[str]:
    """
    What a published lesson is missing against the editorial standard.

    Objectives, a summary, a recap and either a knowledge check or a practical
    exercise. The standard asks for more (worked example, common mistakes,
    sources) but those depend on the subject, so they are left to review rather
    than enforced mechanically.
    """
    missing = []
    if not lesson.objectives:
        missing.append("objectifs pédagogiques manquants")
    if not lesson.summary.strip():
        missing.append("résumé manquant")
    kinds = {(b.kind, b.callout_kind if b.kind == "callout" else "") for b in lesson.blocks}
    if ("callout", "recap") not in kinds:
        missing.append("encadré récapitulatif (« ::: callout recap ») manquant")
    has_practice = lesson.quiz_id or any(b.kind in ("exercise", "tool") for b in lesson.blocks)
    if not has_practice:
        missing.append("ni contrôle de compréhension ni exercice pratique")
    return missing


class _Loader:
    def __init__(self, root: Path, *, include_drafts: bool):
        self.root = root
        self.include_drafts = include_drafts
        self.problems: list[str] = []
        # Lessons that exist on disk but were left out because they are drafts.
        # References to them are not errors: they resolve once the lesson is
        # published, and until then they are simply not shown.
        self.hidden_lessons: set[str] = set()

    def problem(self, where: str, message: str) -> None:
        self.problems.append(f"{where} : {message}")

    def visible(self, status: str) -> bool:
        return status == PUBLISHED or (self.include_drafts and status == DRAFT)

    def read_toml(self, path: Path) -> dict:
        try:
            with path.open("rb") as handle:
                return tomllib.load(handle)
        except FileNotFoundError:
            self.problem(self.rel(path), "fichier introuvable")
        except tomllib.TOMLDecodeError as exc:
            self.problem(self.rel(path), f"TOML invalide ({exc})")
        return {}

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    # ── entry point ──────────────────────────────────────────────────────────

    def load(self) -> Catalog:
        figures = self.load_figures()
        exercises = self.load_exercises()
        quizzes = self.load_quizzes()
        courses = self.load_courses(figures, exercises, quizzes)
        paths = self.load_paths(courses)
        resources = self.load_resources(courses)
        self.check_quiz_links(quizzes, courses)
        return Catalog(paths=paths, courses=courses, quizzes=quizzes,
                       exercises=exercises, resources=resources, figures=figures,
                       root=self.root, include_drafts=self.include_drafts)

    # ── figures ──────────────────────────────────────────────────────────────

    def load_figures(self) -> dict[str, str]:
        folder = self.root / "figures"
        figures = {}
        if folder.is_dir():
            for path in sorted(folder.glob("*.svg")):
                text = path.read_text(encoding="utf-8")
                if "<script" in text.lower():
                    self.problem(self.rel(path), "les figures ne doivent pas contenir de script")
                    continue
                figures[path.name] = text
        return figures

    # ── exercises ────────────────────────────────────────────────────────────

    def load_exercises(self) -> dict[str, Exercise]:
        exercises = {}
        for path in sorted((self.root / "exercises").glob("*.toml")):
            where = self.rel(path)
            data = self.read_toml(path)
            if not data:
                continue
            steps = []
            for raw in data.get("step", []):
                try:
                    step = ExerciseStep(
                        id=str(raw["id"]), prompt=str(raw["prompt"]),
                        unit=str(raw.get("unit", "")), answer=float(raw["answer"]),
                        tolerance=float(raw.get("tolerance", 0)),
                        solution=str(raw["solution"]).strip())
                except (KeyError, TypeError, ValueError) as exc:
                    self.problem(where, f"étape invalide ({exc})")
                    continue
                if step.tolerance < 0:
                    self.problem(where, f"étape {step.id} : tolérance négative")
                steps.append(step)
            if not steps:
                self.problem(where, "aucune étape")
            ids = [s.id for s in steps]
            if len(ids) != len(set(ids)):
                self.problem(where, "identifiants d'étape en double")
            exercise_id = str(data.get("id", path.stem))
            exercises[exercise_id] = Exercise(
                id=exercise_id, title=str(data.get("title", "")),
                context=str(data.get("context", "")).strip(), steps=tuple(steps),
                conclusion=str(data.get("conclusion", "")).strip())
        return exercises

    # ── quizzes ──────────────────────────────────────────────────────────────

    def load_quizzes(self) -> dict[str, Quiz]:
        quizzes = {}
        for path in sorted((self.root / "quizzes").glob("*.toml")):
            where = self.rel(path)
            data = self.read_toml(path)
            if not data:
                continue
            quiz = self.build_quiz(data, where, path.stem)
            if quiz is None:
                continue
            if quiz.id in quizzes:
                self.problem(where, f"identifiant de quiz en double « {quiz.id} »")
            if self.visible(quiz.status):
                quizzes[quiz.id] = quiz
        return quizzes

    def build_quiz(self, data: dict, where: str, default_id: str) -> Quiz | None:
        quiz_id = str(data.get("id", default_id))
        status = str(data.get("status", PUBLISHED))
        if status not in STATUSES:
            self.problem(where, f"statut inconnu « {status} »")
        feedback = str(data.get("feedback", "deferred"))
        if feedback not in FEEDBACK:
            self.problem(where, f"mode de correction inconnu « {feedback} »")
        try:
            threshold = float(data.get("pass_threshold", 0.7))
        except (TypeError, ValueError):
            threshold = -1
        if not 0 < threshold <= 1:
            self.problem(where, "pass_threshold doit être compris entre 0 (exclu) et 1")

        questions = []
        for raw in data.get("question", []):
            question = self.build_question(raw, where)
            if question:
                questions.append(question)
        if not questions:
            self.problem(where, "aucune question")
        ids = [q.id for q in questions]
        if len(ids) != len(set(ids)):
            self.problem(where, "identifiants de question en double")

        return Quiz(id=quiz_id, title=str(data.get("title", "")),
                    course_id=data.get("course"), lesson_id=data.get("lesson"),
                    pass_threshold=threshold, feedback=feedback,
                    version=int(data.get("version", 1)), status=status,
                    questions=tuple(questions),
                    intro=str(data.get("intro", "")).strip())

    def build_question(self, raw: dict, where: str) -> Question | None:
        qid = str(raw.get("id", ""))
        here = f"{where} · {qid or '?'}"
        if not qid or not raw.get("prompt"):
            self.problem(here, "identifiant et énoncé obligatoires")
            return None
        kind = str(raw.get("kind", "single"))
        if kind not in QUESTION_KINDS:
            self.problem(here, f"type de question inconnu « {kind} »")
        options = []
        for opt in raw.get("option", []):
            if not opt.get("id") or not opt.get("text"):
                self.problem(here, "chaque proposition a un identifiant et un texte")
                continue
            if not str(opt.get("explanation", "")).strip():
                self.problem(here, f"proposition {opt['id']} sans explication")
            options.append(Option(id=str(opt["id"]), text=str(opt["text"]),
                                  correct=bool(opt.get("correct", False)),
                                  explanation=str(opt.get("explanation", "")).strip()))
        if len(options) < 2:
            self.problem(here, "au moins deux propositions")
        option_ids = [o.id for o in options]
        if len(option_ids) != len(set(option_ids)):
            self.problem(here, "identifiants de proposition en double")
        correct = sum(o.correct for o in options)
        if correct == 0:
            self.problem(here, "aucune bonne réponse")
        if kind == "single" and correct > 1:
            self.problem(here, "question à choix unique avec plusieurs bonnes réponses")
        if kind == "multiple" and correct == len(options):
            self.problem(here, "toutes les propositions sont justes : la question ne teste rien")
        return Question(id=qid, prompt=str(raw["prompt"]).strip(), kind=kind,
                        options=tuple(options),
                        explanation=str(raw.get("explanation", "")).strip(),
                        lesson_id=raw.get("lesson"))

    # ── courses ──────────────────────────────────────────────────────────────

    def load_courses(self, figures, exercises, quizzes) -> dict[str, Course]:
        courses = {}
        folder = self.root / "courses"
        if not folder.is_dir():
            return courses
        for course_dir in sorted(p for p in folder.iterdir() if p.is_dir()):
            course = self.build_course(course_dir, figures, exercises, quizzes)
            if course is None:
                continue
            if course.id in courses:
                self.problem(self.rel(course_dir), f"identifiant de cours en double « {course.id} »")
            courses[course.id] = course
        return courses

    def build_course(self, course_dir: Path, figures, exercises, quizzes) -> Course | None:
        meta_path = course_dir / "course.toml"
        where = self.rel(meta_path)
        data = self.read_toml(meta_path)
        if not data:
            return None
        course_id = str(data.get("id", course_dir.name))
        status = str(data.get("status", PUBLISHED))
        if status not in STATUSES:
            self.problem(where, f"statut inconnu « {status} »")
        if not self.visible(status):
            return None
        level = str(data.get("level", "debutant"))
        if level not in LEVELS:
            self.problem(where, f"niveau inconnu « {level} »")

        lesson_files = {p.stem: p for p in (course_dir / "lessons").glob("*.md")}
        used: set[str] = set()
        modules = []
        number = 0
        for raw in data.get("module", []):
            lessons = []
            for lesson_id in raw.get("lessons", []):
                if lesson_id in used:
                    self.problem(where, f"leçon « {lesson_id} » listée deux fois")
                    continue
                used.add(lesson_id)
                path = lesson_files.get(lesson_id)
                if path is None:
                    self.problem(where, f"fichier de leçon introuvable : lessons/{lesson_id}.md")
                    continue
                lesson = self.build_lesson(path, course_id, str(raw.get("id", "")),
                                           number + 1, figures, exercises, quizzes)
                if lesson is not None:
                    number += 1
                    lessons.append(lesson)
            if lessons:
                modules.append(Module(id=str(raw.get("id", "")),
                                      title=str(raw.get("title", "")),
                                      lessons=tuple(lessons),
                                      summary=str(raw.get("summary", "")).strip(),
                                      number=len(modules) + 1))
        for orphan in sorted(set(lesson_files) - used):
            self.problem(where, f"leçon lessons/{orphan}.md présente mais absente du plan du cours")
        if not modules:
            self.problem(where, "aucune leçon publiée")

        final_quiz = data.get("final_quiz")
        if final_quiz and final_quiz not in quizzes:
            self.problem(where, f"quiz final « {final_quiz} » introuvable ou non publié")

        return Course(id=course_id, path_id=str(data.get("path", "")),
                      title=str(data.get("title", "")),
                      summary=str(data.get("summary", "")).strip(),
                      level=level, status=status, version=int(data.get("version", 1)),
                      objectives=tuple(data.get("objectives", [])),
                      prerequisites=tuple(data.get("prerequisites", [])),
                      modules=tuple(modules),
                      final_quiz_id=final_quiz if final_quiz in quizzes else None)

    def build_lesson(self, path: Path, course_id: str, module_id: str, number: int,
                     figures, exercises, quizzes) -> Lesson | None:
        where = self.rel(path)
        text = path.read_text(encoding="utf-8")
        front, body = _split_front_matter(text)
        if front is None:
            self.problem(where, "en-tête TOML (+++ … +++) manquant")
            return None
        try:
            meta = tomllib.loads(front)
        except tomllib.TOMLDecodeError as exc:
            self.problem(where, f"en-tête TOML invalide ({exc})")
            return None

        lesson_id = str(meta.get("id", path.stem))
        if lesson_id != path.stem:
            self.problem(where, f"l'identifiant « {lesson_id} » doit correspondre au nom du fichier")
        status = str(meta.get("status", PUBLISHED))
        if status not in STATUSES:
            self.problem(where, f"statut inconnu « {status} »")
        if not self.visible(status):
            self.hidden_lessons.add(lesson_id)
            return None
        access = str(meta.get("access", MEMBER))
        if access not in ACCESS:
            self.problem(where, f"accès inconnu « {access} »")

        try:
            blocks = markup.parse(body)
        except markup.MarkupError as exc:
            self.problem(where, str(exc))
            blocks = []
        for block in blocks:
            if block.kind == "figure" and block.target not in figures:
                self.problem(where, f"figure introuvable : figures/{block.target}")
            if block.kind == "exercise" and block.target not in exercises:
                self.problem(where, f"exercice introuvable : {block.target}")

        quiz_id = meta.get("quiz")
        if quiz_id and quiz_id not in quizzes:
            self.problem(where, f"quiz « {quiz_id} » introuvable ou non publié")

        duration = meta.get("duration_minutes")
        return Lesson(id=lesson_id, course_id=course_id, module_id=module_id,
                      number=number, title=str(meta.get("title", "")),
                      summary=str(meta.get("summary", "")).strip(),
                      duration_minutes=int(duration) if duration is not None else None,
                      access=access, status=status, version=int(meta.get("version", 1)),
                      objectives=tuple(meta.get("objectives", [])),
                      blocks=tuple(blocks),
                      quiz_id=quiz_id if quiz_id in quizzes else None,
                      resources=tuple(meta.get("resources", [])),
                      sources=tuple(meta.get("sources", [])))

    # ── paths ────────────────────────────────────────────────────────────────

    def load_paths(self, courses: dict[str, Course]) -> tuple[LearningPath, ...]:
        meta_path = self.root / "curriculum.toml"
        data = self.read_toml(meta_path)
        paths = []
        claimed: set[str] = set()
        for raw in data.get("path", []):
            where = f"curriculum.toml · {raw.get('id', '?')}"
            status = str(raw.get("status", PLANNED))
            if status not in PATH_STATUSES:
                self.problem(where, f"statut inconnu « {status} »")
            members = []
            for course_id in raw.get("courses", []):
                course = courses.get(course_id)
                if course is None:
                    if status == PUBLISHED and not self.include_drafts:
                        self.problem(where, f"cours « {course_id} » introuvable ou non publié")
                    continue
                if course.path_id != raw.get("id"):
                    self.problem(where, f"le cours « {course_id} » déclare le parcours "
                                        f"« {course.path_id} »")
                claimed.add(course_id)
                members.append(course)
            if status == PUBLISHED and not members:
                self.problem(where, "parcours publié sans cours disponible")
            paths.append(LearningPath(id=str(raw["id"]), number=int(raw.get("number", 0)),
                                      title=str(raw.get("title", "")),
                                      summary=str(raw.get("summary", "")).strip(),
                                      status=status, courses=tuple(members),
                                      topics=tuple(raw.get("topics", []))))
        for course_id in sorted(set(courses) - claimed):
            self.problem("curriculum.toml", f"le cours « {course_id} » n'appartient à aucun parcours")
        numbers = [p.number for p in paths]
        if len(numbers) != len(set(numbers)):
            self.problem("curriculum.toml", "numéros de parcours en double")
        return tuple(sorted(paths, key=lambda p: p.number))

    # ── resources ────────────────────────────────────────────────────────────

    def load_resources(self, courses: dict[str, Course]) -> dict[str, Resource]:
        folder = self.root / "resources"
        meta_path = folder / "resources.toml"
        if not meta_path.exists():
            return {}
        data = self.read_toml(meta_path)
        known_lessons = {l.id for c in courses.values() for l in c.lessons}
        resources = {}
        for raw in data.get("resource", []):
            rid = str(raw.get("id", ""))
            where = f"resources.toml · {rid or '?'}"
            status = str(raw.get("status", PUBLISHED))
            if not self.visible(status):
                continue
            kind = str(raw.get("kind", ""))
            if kind not in RESOURCE_KINDS:
                self.problem(where, f"type de ressource inconnu « {kind} »")
            file_name = str(raw.get("file", ""))
            file_path = (folder / file_name).resolve()
            # A resource is only listed when its file is really there, and only
            # files inside the resources folder can be served.
            if folder.resolve() not in file_path.parents:
                self.problem(where, "le fichier doit se trouver dans resources/")
                continue
            if not file_path.is_file():
                self.problem(where, f"fichier introuvable : resources/{file_name}")
                continue
            lessons = tuple(raw.get("lessons", []))
            for lesson_id in lessons:
                if lesson_id not in known_lessons | self.hidden_lessons:
                    self.problem(where, f"leçon liée inconnue « {lesson_id} »")
            lessons = tuple(l for l in lessons if l in known_lessons)
            access = str(raw.get("access", MEMBER))
            if access not in ACCESS:
                self.problem(where, f"accès inconnu « {access} »")
            pdf_path = None
            if raw.get("pdf"):
                pdf_path = (folder / str(raw["pdf"])).resolve()
                if folder.resolve() not in pdf_path.parents or pdf_path.suffix.lower() != ".pdf":
                    self.problem(where, "le PDF doit être un fichier .pdf dans resources/")
                    pdf_path = None
                elif not pdf_path.is_file():
                    self.problem(where, f"PDF introuvable : resources/{raw['pdf']} "
                                        "(python scripts/build_resource_pdfs.py)")
                    pdf_path = None
            resources[rid] = Resource(id=rid, title=str(raw.get("title", "")),
                                      description=str(raw.get("description", "")).strip(),
                                      kind=kind, category=str(raw.get("category", "")),
                                      level=str(raw.get("level", "debutant")),
                                      file=file_path, lessons=lessons,
                                      author=str(raw.get("author", "Sensitor")),
                                      access=access, pdf=pdf_path)
        for course in courses.values():
            for lesson in course.lessons:
                for rid in lesson.resources:
                    if rid not in resources:
                        self.problem(f"{course.id}/{lesson.id}", f"ressource « {rid} » introuvable")
        return resources

    def check_quiz_links(self, quizzes: dict[str, Quiz], courses: dict[str, Course]) -> None:
        lessons = {l.id for c in courses.values() for l in c.lessons} | self.hidden_lessons
        for quiz in quizzes.values():
            if quiz.lesson_id and quiz.lesson_id not in lessons:
                self.problem(f"quiz {quiz.id}", f"leçon de rattachement inconnue « {quiz.lesson_id} »")
            if quiz.course_id and quiz.course_id not in courses:
                self.problem(f"quiz {quiz.id}", f"cours de rattachement inconnu « {quiz.course_id} »")
            for question in quiz.questions:
                if question.lesson_id and question.lesson_id not in lessons:
                    self.problem(f"quiz {quiz.id} · {question.id}",
                                 f"leçon de référence inconnue « {question.lesson_id} »")


def _split_front_matter(text: str) -> tuple[str | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "+++":
        return None, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "+++":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1:])
    return None, text
