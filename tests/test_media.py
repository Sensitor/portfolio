"""
Videos in lessons, and ebooks in the library.

    python tests/test_media.py

A video is declared with a transcript and an https YouTube or Vimeo address;
the lesson shows a card and loads the player only when the reader asks, so a
page view sends nothing to the host; the transcript is always there. An ebook
is a library resource like the others. Runs on a copy of the content tree: the
repository ships no video yet.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WORK = tempfile.mkdtemp(prefix="sensitor-media-")
os.environ["SENSITOR_DB_PATH"] = os.path.join(WORK, "app.db")
os.environ["SENSITOR_AUTH"] = "multi"
os.environ.pop("SENSITOR_DB_URL", None)

CHECKS: list[tuple[str, bool, str]] = []
DASHES = (chr(0x2014), chr(0x2013))
VIDEO = '''[[video]]
id = "lire-une-bougie"
title = "Lire une bougie, en cinq minutes"
url = "https://www.youtube.com/watch?v=abcdefghijk"
duration_minutes = 5
transcript = "videos/lire-une-bougie.md"
'''


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def tree(videos: str, transcript: str | None = "Une bougie a un corps et deux mèches.") -> Path:
    from sensitor.academy.content import CONTENT_ROOT
    root = Path(tempfile.mkdtemp(prefix="sensitor-media-tree-")) / "academy"
    shutil.copytree(CONTENT_ROOT, root)
    (root / "videos.toml").write_text(videos, encoding="utf-8")
    if transcript is not None:
        (root / "videos").mkdir(exist_ok=True)
        (root / "videos" / "lire-une-bougie.md").write_text(transcript, encoding="utf-8")
    lesson = root / "courses" / "premiers-pas" / "lessons" / "fonctionnement-marche.md"
    lesson.write_text(lesson.read_text(encoding="utf-8") + "\n\n::: video lire-une-bougie\nLa bougie en vidéo.\n:::\n",
                      encoding="utf-8")
    return root


def test_loader() -> None:
    print("\nThe declared videos")
    from sensitor.academy.content import load_catalog, validate
    root = tree(VIDEO)
    check("a declared video with its transcript is valid", validate(root) == [], str(validate(root)[:3]))
    video = load_catalog(root).video("lire-une-bougie")
    check("it is in the catalogue, with its host", video is not None and video.host == "YouTube"
          and video.duration_minutes == 5 and "corps" in video.transcript)
    problems = validate(tree(VIDEO, transcript=None))
    check("a video without transcript is refused", any("transcription" in p for p in problems), str(problems[:3]))
    problems = validate(tree(VIDEO.replace("https://www.youtube.com", "http://exemple.com")))
    check("an address that is not https YouTube or Vimeo is refused", any("https YouTube ou Vimeo" in p for p in problems))
    problems = validate(tree(VIDEO, transcript="Un tiret " + DASHES[0] + " interdit."))
    check("a long dash in the transcript is refused", any("tiret long" in p for p in problems))
    problems = validate(tree(""))
    check("a lesson naming an undeclared video is refused", any("vidéo introuvable" in p for p in problems))
    check("the real content declares no video yet and stays valid", validate() == [])


def test_page() -> None:
    print("\nThe lesson page")
    from streamlit.testing.v1 import AppTest
    os.environ["SENSITOR_ACADEMY_CONTENT"] = str(tree(VIDEO))
    try:
        app = AppTest.from_file(str(ROOT / "sensitor_app.py"), default_timeout=120)
        app.session_state["ac_route"] = {"page": "lesson", "course": "premiers-pas", "lesson": "fonctionnement-marche"}
        app.run()
        text = "\n".join(m.value for m in app.markdown)
        check("the lesson shows the video's card and its transcript", not app.exception
              and "hébergée par YouTube" in text and "corps et deux mèches" in text,
              str(app.exception[0].value)[:300] if app.exception else "")
        check("before the click, no player: nothing is sent to the host", not app.get("video"))
        button = [b for b in app.button if b.key and b.key.startswith("video_btn_")]
        check("a button names the host", button and "YouTube" in button[0].label)
        button[0].click().run()
        check("after the click, the player is there", len(app.get("video")) == 1 and not app.exception)
        check("no long dash on the card", not any(d in text for d in DASHES))
    finally:
        os.environ.pop("SENSITOR_ACADEMY_CONTENT", None)


def test_ebook() -> None:
    print("\nEbooks in the library")
    from sensitor.academy.content import RESOURCE_KINDS, load_catalog, validate
    from sensitor.academy.content import CONTENT_ROOT
    root = Path(tempfile.mkdtemp(prefix="sensitor-ebook-")) / "academy"
    shutil.copytree(CONTENT_ROOT, root)
    source = root / "resources" / "fiche-la-monnaie.md"
    shutil.copy(source, root / "resources" / "ebook-essai.md")
    shutil.copy(root / "resources" / "fiche-la-monnaie.pdf", root / "resources" / "ebook-essai.pdf")
    with (root / "resources" / "resources.toml").open("a", encoding="utf-8") as handle:
        handle.write('\n[[resource]]\nid = "ebook-essai"\ntitle = "Un ebook d\'essai"\n'
                     'description = "Un ebook pour le test."\nkind = "ebook"\ncategory = "Monnaie"\n'
                     'level = "debutant"\nfile = "ebook-essai.md"\npdf = "ebook-essai.pdf"\naccess = "public"\n'
                     'lessons = []\n')
    problems = [p for p in validate(root) if "manifest" not in p.lower()]
    resource = load_catalog(root).resource("ebook-essai")
    check("an ebook is a library resource with its PDF", resource is not None and resource.kind_label == "Ebook"
          and resource.pdf is not None and RESOURCE_KINDS["ebook"] == "Ebook", str(problems[:3]))


def main() -> int:
    test_loader()
    test_page()
    test_ebook()
    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
