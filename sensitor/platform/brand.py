"""
The Sensitor mark.

The reference is the supplied logo: a white, angular S monogram inscribed in a
hexagon, on a rounded anthracite square. `assets/brand/sensitor-mark.svg` is a
vector trace of that image — the two hooks of the S measured on the isometric
grid the logo is drawn on, the tile colour and the silver gradient sampled from
the pixels.

If the official vector file is supplied, save it as
`assets/brand/sensitor-mark-official.svg`: it takes precedence everywhere the
mark is shown, with no code change.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[2] / "assets" / "brand"
OFFICIAL = ASSETS / "sensitor-mark-official.svg"
TRACED = ASSETS / "sensitor-mark.svg"
MONOGRAM = ASSETS / "sensitor-monogram.svg"


@lru_cache(maxsize=None)
def _source(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<\?xml[^>]*\?>", "", text)
    return re.sub(r">\s+<", "><", text).strip()


def mark_source() -> Path:
    return OFFICIAL if OFFICIAL.exists() else TRACED


def mark_svg(size: int = 40, *, uid: str = "m") -> str:
    """The tile-and-monogram mark, sized, with ids made unique for this instance."""
    svg = _source(mark_source())
    svg = svg.replace('id="sensitor-metal"', f'id="{uid}-metal"').replace(
        "url(#sensitor-metal)", f"url(#{uid}-metal)")
    return re.sub(r"<svg\b", f'<svg width="{size}" height="{size}"', svg, count=1)


def monogram_svg(size: int = 40, *, color: str = "currentColor") -> str:
    """The S alone, one colour — for watermarks and small inline uses."""
    svg = _source(MONOGRAM).replace("currentColor", color)
    return re.sub(r"<svg\b", f'<svg width="{size}" height="{size * 88 // 80}"', svg, count=1)
