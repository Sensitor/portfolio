"""
The platform registry and the brand asset — no Streamlit.

Run with:  python tests/test_platform.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules["streamlit"] = None

from sensitor.platform import brand, spaces  # noqa: E402

FAILURES: list[str] = []
COUNT = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global COUNT
    COUNT += 1
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"  {detail}" if not condition else ""))
    if not condition:
        FAILURES.append(f"{name}: {detail}")


def main() -> int:
    print("\nRegistry")
    ids = [s.id for s in spaces.SPACES]
    check("space ids are unique", len(ids) == len(set(ids)))
    pages = spaces.all_pages()
    check("page ids are unique across spaces", len(pages) == len(set(pages)), str(pages))
    check("every entry page belongs to its space", all(s.entry in s.pages for s in spaces.SPACES))
    check("every group is known", all(s.group in dict(spaces.GROUPS) for s in spaces.SPACES))
    check("the Academy is live", spaces.space("academy").is_live)
    for space in spaces.SPACES:
        if space.status == spaces.PREPARING:
            check(f"{space.id}: a preparing space has exactly one page", space.pages == (space.entry,))
            check(f"{space.id}: and says what is planned", bool(space.planned))
    for space in spaces.SPACES:
        for _, target in space.related:
            page, _ = spaces.parse_target(target)
            check(f"{space.id}: related link {target} resolves", page in pages)
    check("legacy « paths » resolves to the Academy", spaces.resolve_page("paths") == "academy")
    check("unknown pages resolve home", spaces.resolve_page("nope") == "home")
    check("no page resolves home", spaces.resolve_page(None) == "home")
    check("lesson targets parse", spaces.parse_target("lesson:c/l") == ("lesson", {"course": "c", "lesson": "l"}))

    print("\nRenderers")
    import importlib.util
    shell = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "sensitor", "platform", "ui", "shell.py"), encoding="utf-8").read()
    for page in pages:
        check(f"page « {page} » has a renderer", f'"{page}":' in shell)

    print("\nBrand")
    check("the traced mark is shipped", brand.TRACED.is_file())
    svg = brand.mark_svg(40, uid="x")
    check("the mark is sized", 'width="40"' in svg and 'height="40"' in svg)
    check("gradient ids are made unique", 'id="x-metal"' in svg and "url(#x-metal)" in svg
          and "sensitor-metal" not in svg)
    check("two instances do not share ids", brand.mark_svg(20, uid="a") != brand.mark_svg(20, uid="b"))
    check("the mark is the two-hook S on the rounded tile",
          svg.count("<path") == 2 and 'rx="21"' in svg and "#262626" in svg)
    check("the official file wins when present", brand.mark_source() in (brand.OFFICIAL, brand.TRACED))
    check("the monogram takes a colour", 'fill="#fff"' in brand.monogram_svg(10, color="#fff"))

    print(f"\n{COUNT} checks, {len(FAILURES)} failures")
    for failure in FAILURES:
        print(f"  - {failure}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
