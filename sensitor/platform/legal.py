"""
The legal pages: legal notice, terms of use, privacy policy.

The texts are content, in `content/legal/*.md` (Markdown with a TOML front
matter, like the lessons), and the publisher's details are in
`content/legal/editeur.toml`, filled in by the founder. A text names a detail
with `{section.field}` (`{editeur.raison_sociale}`) or `{field}` for a top-level
one (`{mise_a_jour}`). Nothing is invented: a detail left empty reads
« [à compléter] », and `missing()` lists them for the pre-launch check and for
the banner the pages show until every detail is in and `relu` is true.

No Streamlit.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "content" / "legal"
PAGES = {
    "mentions": ("mentions-legales.md", "Mentions légales"),
    "conditions": ("conditions.md", "Conditions d'utilisation"),
    "confidentialite": ("confidentialite.md", "Politique de confidentialité"),
}
TO_COMPLETE = "[à compléter]"
FIELD = re.compile(r"\{([a-z_]+(?:\.[a-z_]+)?)\}")


@dataclass(frozen=True)
class Document:
    page: str
    title: str
    summary: str
    body: str                       # Markdown, details filled in
    missing: tuple[str, ...]        # details still empty in this text
    reviewed: bool


def details(root: Path = ROOT) -> dict:
    with (root / "editeur.toml").open("rb") as handle:
        return tomllib.load(handle)


MONTHS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
          "novembre", "décembre")


def _value(data: dict, name: str) -> str:
    section, _, field = name.partition(".")
    value = data.get(section, {}).get(field) if field else data.get(section)
    text = str(value).strip() if value not in (None, "") else ""
    date = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if date:                                             # « 2026-10-30 » reads « 30 octobre 2026 »
        year, month, day = (int(x) for x in date.groups())
        return f"{day} {MONTHS[month - 1]} {year}"
    return text


def _split(text: str) -> tuple[dict, str]:
    if not text.startswith("+++"):
        return {}, text
    _, front, body = text.split("+++", 2)
    return tomllib.loads(front), body.strip()


def document(page: str, root: Path = ROOT) -> Document:
    filename, title = PAGES[page]
    meta, body = _split((root / filename).read_text(encoding="utf-8"))
    data = details(root)
    missing = []

    def fill(match):
        value = _value(data, match.group(1))
        if not value:
            missing.append(match.group(1))
            return f"**{TO_COMPLETE}**"
        return value

    filled = FIELD.sub(fill, body)
    return Document(page, meta.get("title", title), meta.get("summary", ""), filled,
                    tuple(dict.fromkeys(missing)), bool(data.get("relu")))


def missing(root: Path = ROOT) -> list[str]:
    """Every detail a legal text uses and the founder has not filled in yet."""
    return list(dict.fromkeys(name for page in PAGES for name in document(page, root).missing))


def ready(root: Path = ROOT) -> bool:
    """Whether the legal pages can go live as they are: every detail filled, the texts reviewed."""
    return not missing(root) and bool(details(root).get("relu"))
