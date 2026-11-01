"""
The public site's articles: files, like the lessons.

    content/media/articles/<slug>.md

Markdown with a TOML front matter between `+++`, read by the Academy's own
helpers (`academy.content._split_front_matter`, `academy.markup.parse`), under
the same house rules, enforced here:

* no long dash (U+2014, U+2013) anywhere, front matter included;
* a published article names its `sources` and its `updated` date, so every
  figure in it can be traced (a constructed example says so in the text);
* an opinion goes in a `callout opinion`, an open question in a `callout debate`;
  only `callout` and `figure` blocks are allowed (no tool, quiz or chart outside
  the platform), and a figure must exist in `content/academy/figures`;
* the slug is the file name: lowercase letters, digits and hyphens.

A file whose name starts with `_` is a template and never published. A draft
(`status = "draft"`) is validated but not published.

No Streamlit.
"""

from __future__ import annotations

import datetime as _dt
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from ..academy import markup
from ..academy.content import CONTENT_ROOT, _split_front_matter

ROOT = CONTENT_ROOT.parent / "media" / "articles"
FIGURES = CONTENT_ROOT / "figures"
DRAFT, PUBLISHED = "draft", "published"
UNIVERSES = {"trading": "Trading", "crypto": "Monnaie et crypto"}
ALLOWED_BLOCKS = {"markdown", "callout", "figure"}
DASHES = (chr(0x2014), chr(0x2013))
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SUMMARY = 200            # the meta description search engines show


@dataclass(frozen=True)
class Article:
    slug: str
    title: str
    summary: str
    date: _dt.date
    updated: _dt.date | None
    universe: str
    author: str
    status: str
    sources: tuple[str, ...]
    tags: tuple[str, ...]
    blocks: tuple

    @property
    def is_published(self) -> bool:
        return self.status == PUBLISHED

    @property
    def universe_label(self) -> str:
        return UNIVERSES.get(self.universe, self.universe)

    @property
    def last_modified(self) -> _dt.date:
        return self.updated or self.date


def _date(value, where: str, field: str, problems: list[str]) -> _dt.date | None:
    if value is None:
        return None
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    try:
        return _dt.date.fromisoformat(str(value))
    except ValueError:
        problems.append(f"{where} : date « {field} » invalide (attendu AAAA-MM-JJ)")
        return None


def read(path: Path, problems: list[str]) -> Article | None:
    where = f"media/articles/{path.name}"
    text = path.read_text(encoding="utf-8")
    if any(d in text for d in DASHES):
        problems.append(f"{where} : tiret long interdit (U+2014 ou U+2013)")
    front, body = _split_front_matter(text)
    if front is None:
        problems.append(f"{where} : en-tête TOML (+++ … +++) manquant")
        return None
    try:
        meta = tomllib.loads(front)
    except tomllib.TOMLDecodeError as exc:
        problems.append(f"{where} : en-tête TOML invalide ({exc})")
        return None
    before = len(problems)
    slug = path.stem
    if not SLUG.match(slug):
        problems.append(f"{where} : nom de fichier attendu en minuscules, chiffres et tirets")
    title, summary = str(meta.get("title", "")).strip(), " ".join(str(meta.get("summary", "")).split())
    if not title:
        problems.append(f"{where} : titre manquant")
    if not summary:
        problems.append(f"{where} : résumé manquant (il sert de description pour les moteurs de recherche)")
    elif len(summary) > MAX_SUMMARY:
        problems.append(f"{where} : résumé trop long ({len(summary)} caractères, {MAX_SUMMARY} au plus)")
    status = str(meta.get("status", DRAFT))
    if status not in (DRAFT, PUBLISHED):
        problems.append(f"{where} : statut inconnu « {status} »")
    universe = str(meta.get("universe", ""))
    if universe not in UNIVERSES:
        problems.append(f"{where} : univers attendu parmi {', '.join(UNIVERSES)}")
    date = _date(meta.get("date"), where, "date", problems)
    if date is None and "date" not in meta:
        problems.append(f"{where} : date de publication manquante")
    updated = _date(meta.get("updated"), where, "updated", problems)
    sources = meta.get("sources", [])
    if not isinstance(sources, list) or not all(isinstance(s, str) and s.strip() for s in sources):
        problems.append(f"{where} : les sources doivent être une liste de textes non vides")
        sources = []
    if status == PUBLISHED:
        if not sources:
            problems.append(f"{where} : sources manquantes (obligatoires pour un article publié)")
        if updated is None:
            problems.append(f"{where} : date de mise à jour manquante (obligatoire pour un article publié)")
    tags = meta.get("tags", [])
    if not isinstance(tags, list):
        problems.append(f"{where} : les étiquettes doivent être une liste")
        tags = []
    try:
        blocks = markup.parse(body)
    except markup.MarkupError as exc:
        problems.append(f"{where} : {exc}")
        blocks = []
    for block in blocks:
        if block.kind not in ALLOWED_BLOCKS:
            problems.append(f"{where} : bloc « {block.kind} » réservé aux leçons de la plateforme")
        if block.kind == "figure" and not (FIGURES / block.target).is_file():
            problems.append(f"{where} : figure introuvable : figures/{block.target}")
    if not any(b.kind == "markdown" and b.text.strip() for b in blocks):
        problems.append(f"{where} : article vide")
    if len(problems) > before:
        return None
    return Article(slug=slug, title=title, summary=summary, date=date, updated=updated, universe=universe,
                   author=str(meta.get("author", "Sensitor")).strip() or "Sensitor", status=status,
                   sources=tuple(s.strip() for s in sources), tags=tuple(str(t) for t in tags), blocks=tuple(blocks))


def load(root: Path = ROOT) -> tuple[list[Article], list[str]]:
    """Every article (templates aside), newest first, and the problems found."""
    problems: list[str] = []
    articles = []
    if root.is_dir():
        for path in sorted(root.glob("*.md")):
            if path.name.startswith("_"):
                continue
            article = read(path, problems)
            if article is not None:
                articles.append(article)
    articles.sort(key=lambda a: (a.date, a.slug), reverse=True)
    return articles, problems


def published(root: Path = ROOT) -> list[Article]:
    articles, problems = load(root)
    if problems:
        raise ValueError("\n".join(problems))
    return [a for a in articles if a.is_published]
