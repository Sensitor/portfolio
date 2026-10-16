"""
Build the PDF of every library resource that declares one.

    python scripts/build_resource_pdfs.py

A development tool, not a runtime dependency: it needs Playwright and a
Chromium (PLAYWRIGHT_CHROMIUM may point at a specific binary) and network
access for the web fonts. The PDFs and `pdf-manifest.toml` it writes are
committed; the deployed app only serves them.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tomllib  # noqa: E402

from sensitor.academy import printable  # noqa: E402
from sensitor.academy.content import CONTENT_ROOT, RESOURCE_KINDS  # noqa: E402
from sensitor.platform.brand import mark_svg  # noqa: E402


def main() -> int:
    from playwright.sync_api import sync_playwright

    folder = CONTENT_ROOT / "resources"
    # Read the list directly: the catalogue refuses to load while a declared
    # PDF is missing, which is exactly the state this script exists to fix.
    with (folder / "resources.toml").open("rb") as handle:
        targets = [r for r in tomllib.load(handle).get("resource", []) if r.get("pdf")]
    if not targets:
        print("Aucune ressource ne déclare de PDF.")
        return 0
    manifest = printable.read_manifest(folder)
    launch = {}
    if os.getenv("PLAYWRIGHT_CHROMIUM"):
        launch["executable_path"] = os.environ["PLAYWRIGHT_CHROMIUM"]
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        page = browser.new_context(ignore_https_errors=True).new_page()
        for resource in targets:
            source = folder / resource["file"]
            kind = RESOURCE_KINDS.get(resource.get("kind", ""), "")
            page.set_content(printable.to_html(source.read_text(encoding="utf-8"), kind_label=kind,
                                               mark_svg=mark_svg(30, uid="pdf")),
                             wait_until="networkidle")
            page.pdf(path=str(folder / resource["pdf"]), format="A4", print_background=True,
                     display_header_footer=True, header_template="<span></span>",
                     footer_template=(
                         '<div style="width:100%;font:7pt DM Mono,monospace;color:#56616a;'
                         'padding:0 18mm;display:flex;justify-content:space-between">'
                         f'<span>Sensitor Academy · {resource["title"]}</span>'
                         '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'),
                     margin={"top": "20mm", "bottom": "22mm", "left": "18mm", "right": "18mm"})
            manifest[resource["pdf"]] = printable.source_hash(source)
            print(f"  {resource['pdf']}")
        browser.close()
    printable.write_manifest(folder, manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
