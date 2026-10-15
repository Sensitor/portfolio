"""
The Sensitor mark: a hexagonal S, drawn as vector so it stays sharp at any size.

A redraw of the supplied logo. If an original vector file exists, replace
`MARK_PATHS` with its paths; every place the logo appears reads it from here.
"""

from __future__ import annotations

# A pointy-top hexagon centred on (24, 24). The S runs along its top edges,
# crosses the centre on the isometric diagonal, and returns along the bottom.
MARK_PATHS = "M35.3 17.5 L24 11 L12.7 17.5 L35.3 30.5 L24 37 L12.7 30.5"


def logo_svg(size: int = 36, *, tile: bool = True, uid: str = "m") -> str:
    """The mark as an inline SVG string. `uid` keeps gradient ids unique per page."""
    background = (
        f'<rect x="0.5" y="0.5" width="47" height="47" rx="11" fill="url(#{uid}bg)" '
        f'stroke="#3a3f45" stroke-width="1"/>' if tile else ""
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="{size}" '
        f'height="{size}" role="img" aria-label="Sensitor">'
        f'<defs>'
        f'<linearGradient id="{uid}bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#2b2f34"/><stop offset="1" stop-color="#17191c"/>'
        f'</linearGradient>'
        f'<linearGradient id="{uid}metal" x1="0.15" y1="0" x2="0.85" y2="1">'
        f'<stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="#d4d8dc"/>'
        f'<stop offset="1" stop-color="#8d949b"/>'
        f'</linearGradient>'
        f'</defs>'
        f'{background}'
        f'<path d="{MARK_PATHS}" fill="none" stroke="#50565c" stroke-width="5" '
        f'stroke-linejoin="miter" transform="translate(0.7 0.9)"/>'
        f'<path d="{MARK_PATHS}" fill="none" stroke="url(#{uid}metal)" stroke-width="4.6" '
        f'stroke-linejoin="miter"/>'
        f'</svg>'
    )
