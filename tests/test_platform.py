"""
The platform registry and the brand asset — no Streamlit.

Run with:  python tests/test_platform.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules["streamlit"] = None

from sensitor.platform import brand, journal, spaces  # noqa: E402

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
    carnet = [p for p in pages if spaces.uses_carnet(p)]
    expected = set(spaces.space("journal").pages) | {"coach"}
    for sid in ("academy", "library", "progress"):
        expected |= set(spaces.space(sid).pages)
    check("the « Carnet de bord » direction is decided in one place: journal, coaching, Academy, library, progress",
          set(carnet) == expected, str(carnet))
    check("the pages one reads take the Bulletin edition, the working pages none",
          all(spaces.edition_of(p) == "bulletin" for s in ("academy", "library", "progress") for p in spaces.space(s).pages)
          and all(spaces.edition_of(p) == "" for p in spaces.space("journal").pages)
          and spaces.edition_of("coach") == "" and spaces.edition_of("lab") == "")
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

    check("Psychologie et discipline is open", spaces.space("psychology").is_live)
    check("and announces nothing it has not built", spaces.space("psychology").planned == ())
    check("it links to path 6", ("Parcours 6 : Décider sous incertitude", "course:decider-sous-incertitude")
          in spaces.space("psychology").related)
    check("course targets parse", spaces.parse_target("course:c") == ("course", {"course": "c"}))

    print("\nReflection journal")
    from datetime import datetime, timezone
    check("three entry kinds", [k.id for k in journal.KINDS] == ["pre", "post", "free"])
    check("every kind has guided questions", all(k.prompts for k in journal.KINDS))
    check("a clean entry is trimmed",
          journal.clean_entry("pre", "  Plan.  ", mood=3) == ("pre", "Plan.", 3, ""))
    check("a guided question of the same kind is accepted",
          journal.clean_entry("post", "x", prompt=journal.kind("post").prompts[0])[3]
          == journal.kind("post").prompts[0])
    for label, call in (
            ("an unknown kind", lambda: journal.clean_entry("diagnostic", "x")),
            ("an empty note", lambda: journal.clean_entry("pre", "   ")),
            ("a note over the limit", lambda: journal.clean_entry("pre", "x" * (journal.MAX_BODY + 1))),
            ("a mood of 0", lambda: journal.clean_entry("pre", "x", mood=0)),
            ("a mood of 6", lambda: journal.clean_entry("pre", "x", mood=6)),
            ("a mood that is not an integer", lambda: journal.clean_entry("pre", "x", mood=2.5)),
            ("a boolean mood", lambda: journal.clean_entry("pre", "x", mood=True)),
            ("a question from another kind",
             lambda: journal.clean_entry("pre", "x", prompt=journal.kind("post").prompts[0])),
            ("an invented question", lambda: journal.clean_entry("pre", "x", prompt="Êtes-vous anxieux ?"))):
        try:
            call()
            refused = False
        except ValueError:
            refused = True
        check(f"refuses {label}", refused)
    check("before and after a session carry a routine, a free note does not",
          bool(journal.kind("pre").routine) and bool(journal.kind("post").routine)
          and journal.kind("free").routine == ())
    ids = [item for item, _ in journal.kind("pre").routine]
    check("routine ids are unique", len(ids) == len(set(ids)))
    check("ticked items come back in the routine's order",
          journal.clean_checks("pre", [ids[2], ids[0]]) == [ids[0], ids[2]])
    check("nothing ticked is an answer, not an absence", journal.clean_checks("post", []) == [])
    check("a free note has no routine", journal.clean_checks("free", None) is None)
    check("a routine not presented is not « nothing ticked »", journal.clean_checks("pre", None) is None)
    for label, call in (("an item from another moment", lambda: journal.clean_checks("pre", ["regles"])),
                        ("an invented item", lambda: journal.clean_checks("post", ["diagnostic"])),
                        ("items on a free note", lambda: journal.clean_checks("free", ["etat"])),
                        ("an unknown kind", lambda: journal.clean_checks("autre", []))):
        try:
            call()
            refused = False
        except ValueError:
            refused = True
        check(f"routine refuses {label}", refused)
    routine_notes = [{"kind": "pre", "mood": None, "created_at": "x", "checks": ["etat", "limites"]},
                     {"kind": "pre", "mood": None, "created_at": "x", "checks": ["etat"]},
                     {"kind": "pre", "mood": None, "created_at": "x", "checks": []},
                     {"kind": "pre", "mood": None, "created_at": "x", "checks": None}]
    counted = {r.id: (r.ticked, r.n) for r in journal.summarize(routine_notes).routine}
    check("routine counts per item, over the notes that offered it",
          counted["etat"] == (2, 3) and counted["limites"] == (1, 3) and counted["contexte"] == (0, 3))
    check("no routine row for a moment with no routine note",
          all(r.kind == "pre" for r in journal.summarize(routine_notes).routine))
    now = datetime(2026, 10, 16, 12, tzinfo=timezone.utc)
    notes = [{"kind": "pre", "mood": 2, "created_at": "2026-10-15T08:00:00+00:00"},
             {"kind": "pre", "mood": 4, "created_at": "2026-10-01T08:00:00+00:00"},
             {"kind": "post", "mood": None, "created_at": "2026-08-01T08:00:00+00:00"},
             {"kind": "free", "mood": 5, "created_at": "pas une date"}]
    summary = journal.summarize(notes, now=now)
    check("counts by kind", summary.by_kind == {"pre": 2, "post": 1, "free": 1} and summary.total == 4)
    check("the last 30 days", summary.last_30_days == 2)
    check("averages only where the scale was filled, with their sample size",
          [(m.kind, m.average, m.n) for m in summary.moods] == [("pre", 3.0, 2), ("free", 5.0, 1)]
          and summary.rated == 3)
    check("an empty journal summarises to zeros",
          journal.summarize([], now=now).total == 0 and journal.summarize([], now=now).moods == ())

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
