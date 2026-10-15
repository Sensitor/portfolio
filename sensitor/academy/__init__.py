"""
Sensitor Academy — the educational domain.

Pure Python: no Streamlit, no FastAPI. The Streamlit app (`academy_app.py`) and
the HTTP API (`sensitor.api.routers.academy`) both read through these modules,
so a lesson, a quiz score or a position size cannot differ between the two.

    content   lessons, courses, paths, quizzes and resources, loaded from
              version-controlled files under `content/academy/`
    markup    the lesson body format (Markdown plus a few block directives)
    quiz      scoring and explained feedback
    exercise  numeric practical exercises with worked solutions
    risk      the risk-management calculations behind the lab and the lessons
    progress  course completion and "what next", from stored progress rows
"""

from .content import Catalog, ContentError, load_catalog  # noqa: F401
