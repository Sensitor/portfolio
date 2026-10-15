"""
Check the content tree before publishing.

    python -m sensitor.academy.validate

Lists every structural problem (broken references, answer keys with no right
answer, missing files) and every published lesson that falls short of the
editorial standard. Exits non-zero if anything is found, so it can run in CI.
"""

from __future__ import annotations

import sys

from .content import CONTENT_ROOT, load_catalog, validate


def main() -> int:
    problems = validate(include_drafts=True)
    if problems:
        print(f"{len(problems)} problème(s) dans {CONTENT_ROOT} :")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    catalog = load_catalog()
    lessons = sum(len(c.lessons) for c in catalog.courses.values())
    questions = sum(len(q.questions) for q in catalog.quizzes.values())
    print(f"Contenu valide : {len(catalog.courses)} cours, {lessons} leçons publiées, "
          f"{len(catalog.quizzes)} quiz ({questions} questions), "
          f"{len(catalog.exercises)} exercice(s), {len(catalog.resources)} ressource(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
