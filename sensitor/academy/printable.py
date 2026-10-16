"""
Printable versions of library resources.

`to_html` turns a resource's Markdown into a styled, self-contained HTML page —
the Sensitor mark, editorial type, A4 margins — which `scripts/build_resource_pdfs.py`
prints to PDF. The PDFs are committed next to their source, so the deployed app
serves real files and needs no PDF library.

`pdf-manifest.toml` records the SHA-256 of the Markdown each PDF was built
from. The test suite compares it with the current source: editing a sheet
without rebuilding its PDF fails the tests instead of shipping a stale file.

The Markdown subset is the one the library uses: headings, paragraphs, bold and
italic, bullet, numbered and task lists, tables and horizontal rules.
"""

from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

MANIFEST = "pdf-manifest.toml"


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_manifest(folder: Path) -> dict[str, str]:
    import tomllib
    path = folder / MANIFEST
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return {k: str(v) for k, v in tomllib.load(handle).get("built", {}).items()}


def write_manifest(folder: Path, entries: dict[str, str]) -> None:
    lines = ["# Written by scripts/build_resource_pdfs.py: SHA-256 of each PDF's Markdown source.",
             "[built]"]
    lines += [f'"{name}" = "{digest}"' for name, digest in sorted(entries.items())]
    (folder / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Markdown subset → HTML ───────────────────────────────────────────────────

def _inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", out)
    return out


def markdown_to_html(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            out.append(f"<h{level}>{_inline(line[level:].strip())}</h{level}>")
            i += 1
        elif line.strip() == "---":
            out.append("<hr>")
            i += 1
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(set(c) <= {"-", ":"} for c in cells):
                    rows.append(cells)
                i += 1
            head, body = rows[0], rows[1:]
            out.append("<table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>" + "".join(
                           "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>"
                           for row in body) + "</tbody></table>")
        elif re.match(r"^(- |\d+\. )", line):
            ordered = bool(re.match(r"^\d+\. ", line))
            items = []
            while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i]):
                item = re.sub(r"^(- |\d+\. )", "", lines[i].rstrip())
                if item.startswith("[ ] "):
                    items.append(f'<li class="task"><span class="box"></span>{_inline(item[4:])}</li>')
                else:
                    items.append(f"<li>{_inline(item)}</li>")
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>{''.join(items)}</{tag}>")
        else:
            paragraph = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||- |\d+\. |---)", lines[i]):
                paragraph.append(lines[i].strip())
                i += 1
            out.append(f"<p>{_inline(' '.join(paragraph))}</p>")
    return "\n".join(out)


STYLE = """
@page { size: A4; margin: 20mm 18mm 22mm; }
* { box-sizing: border-box; }
body { margin: 0; color: #23303a; font: 10.5pt/1.6 'DM Sans', Helvetica, Arial, sans-serif; }
header { display: flex; align-items: center; gap: 10px; padding-bottom: 10px; margin-bottom: 18px;
  border-bottom: 1px solid #0f1b26; }
header .name { font: 700 9pt 'DM Sans', sans-serif; letter-spacing: .24em; color: #0f1b26; }
header .sub { font: 400 7.5pt 'DM Mono', monospace; letter-spacing: .16em; color: #56616a; margin-top: 2px; }
header .kind { margin-left: auto; font: 500 7.5pt 'DM Mono', monospace; letter-spacing: .14em;
  text-transform: uppercase; color: #3a6993; }
h1 { font: 600 24pt/1.1 'Playfair Display', Georgia, serif; color: #0f1b26; letter-spacing: -.02em; margin: 0 0 4px; }
h1 + p { color: #56616a; margin-top: 2px; }
h2 { font: 600 13.5pt/1.25 'Playfair Display', Georgia, serif; color: #0f1b26; margin: 18px 0 6px;
  padding-top: 10px; border-top: 1px solid #ddd8cb; break-after: avoid; }
p { margin: 6px 0; }
strong { color: #0f1b26; }
ul, ol { margin: 6px 0; padding-left: 16px; }
li { margin: 3px 0; }
li.task { list-style: none; margin-left: -16px; display: flex; gap: 8px; align-items: flex-start; }
li.task .box { flex: 0 0 10px; height: 10px; border: 1px solid #3a6993; margin-top: 4px; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 10px; font-size: 9.5pt; break-inside: avoid; }
th { font: 500 7.5pt 'DM Mono', monospace; letter-spacing: .1em; text-transform: uppercase; color: #56616a;
  text-align: left; padding: 6px 8px; border-bottom: 1px solid #0f1b26; background: #f3f0e8; }
td { padding: 6px 8px; border-bottom: 1px solid #ddd8cb; vertical-align: top; }
hr { border: 0; border-top: 1px solid #ddd8cb; margin: 16px 0 8px; }
hr + p { font-size: 8.5pt; color: #56616a; }
"""


def to_html(markdown: str, *, kind_label: str, mark_svg: str) -> str:
    fonts = ("https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500"
             "&family=DM+Sans:opsz,wght@9..40,400;9..40,600;9..40,700"
             "&family=Playfair+Display:wght@600&display=swap")
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<link rel="stylesheet" href="{fonts}"><style>{STYLE}</style></head><body>'
            f'<header>{mark_svg}<div><div class="name">SENSITOR</div>'
            f'<div class="sub">ACADEMY</div></div><div class="kind">{html.escape(kind_label)}</div></header>'
            f'{markdown_to_html(markdown)}</body></html>')
