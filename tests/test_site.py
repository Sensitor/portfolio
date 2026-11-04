"""
The public site: articles as files, the static generator, and what search
engines need.

    python tests/test_site.py

Builds the site from the real content plus fixture articles in a temporary
folder (the repository ships no published article), and checks: the validator
refuses an article that breaks the house rules; drafts and templates are not
published; every page has its title, description, canonical address and Open
Graph tags; the sitemap and the RSS feed list what they should; no page calls a
third party; only free revision sheets are copied.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CHECKS: list[tuple[str, bool, str]] = []
DASHES = (chr(0x2014), chr(0x2013))
BASE, APP = "https://sensitor.example", "https://app.sensitor.example"

GOOD = """+++
title = "Lire un spread avant d'entrer"
summary = "Ce que coûte l'écart entre l'achat et la vente, et pourquoi il compte plus sur une petite unité de temps."
date = 2026-10-20
updated = 2026-10-28
universe = "trading"
author = "Sensitor"
status = "published"
tags = ["coûts"]
sources = ["Exemple construit : chiffres choisis pour le calcul, pas des cotations réelles"]
+++

Un **exemple construit** : un spread de 1 pip sur un objectif de 10 pips coûte 10 % du gain visé.

::: callout opinion "Avis du fondateur"
Sur une petite unité de temps, le coût pèse plus lourd.
:::

::: figure structure-tendance.svg
La structure d'une tendance.
:::
"""


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}" + (f"   {detail}" if detail and not condition else ""))


def article(folder: Path, name: str, text: str) -> None:
    (folder / name).write_text(text, encoding="utf-8")


def test_validator() -> None:
    print("\nThe articles' validator")
    from sensitor.site import articles as A
    folder = Path(tempfile.mkdtemp(prefix="sensitor-articles-"))
    figures = sorted(p.name for p in A.FIGURES.glob("*.svg"))
    good = GOOD.replace("structure-tendance.svg", figures[0])
    article(folder, "lire-un-spread.md", good)
    loaded, problems = A.load(folder)
    check("a valid article loads", not problems and [a.slug for a in loaded] == ["lire-un-spread"], str(problems))
    cases = {
        "tiret.md": good.replace("Un **exemple", "Un " + chr(0x2014) + " **exemple"),
        "sans-sources.md": good.replace('sources = ["Exemple construit : chiffres choisis pour le calcul, '
                                        'pas des cotations réelles"]', "sources = []"),
        "sans-relecture.md": good.replace("updated = 2026-10-28\n", ""),
        "outil.md": good + "\n::: tool risk-calculator\n:::\n",
        "figure-absente.md": good.replace(figures[0], "nexiste-pas.svg"),
        "Majuscules.md": good,
        "sans-titre.md": good.replace('title = "Lire un spread avant d\'entrer"', 'title = ""'),
        "univers.md": good.replace('universe = "trading"', 'universe = "meteo"'),
        "resume-long.md": good.replace('summary = "Ce que', 'summary = "' + "x" * 210 + ' Ce que'),
    }
    expected = {"tiret.md": "tiret long", "sans-sources.md": "sources manquantes",
                "sans-relecture.md": "mise à jour manquante", "outil.md": "réservé aux leçons",
                "figure-absente.md": "figure introuvable", "Majuscules.md": "minuscules",
                "sans-titre.md": "titre manquant", "univers.md": "univers", "resume-long.md": "trop long"}
    for name, text in cases.items():
        one = Path(tempfile.mkdtemp(prefix="sensitor-article-"))
        article(one, name, text)
        _, found = A.load(one)
        check(f"refused: {name}", any(expected[name] in p for p in found), str(found))
    draft = Path(tempfile.mkdtemp(prefix="sensitor-draft-"))
    article(draft, "brouillon.md", good.replace('status = "published"', 'status = "draft"')
            .replace('sources = ["Exemple construit : chiffres choisis pour le calcul, pas des cotations réelles"]',
                     "sources = []"))
    article(draft, "_modele.md", "pas même un en-tête")
    loaded, found = A.load(draft)
    check("a draft may lack its sources; a template is not even read", not found and len(loaded) == 1
          and A.published(draft) == [])
    check("the repository's own articles are valid (the template included in the check)",
          not A.load()[1] and (A.ROOT / "_modele.md").is_file())
    shutil.rmtree(folder)


def test_build() -> None:
    print("\nThe generated site")
    from sensitor.site import articles as A
    from sensitor.site.build import LEGAL_PATHS, Site
    folder = Path(tempfile.mkdtemp(prefix="sensitor-site-articles-"))
    figure = sorted(p.name for p in A.FIGURES.glob("*.svg"))[0]
    article(folder, "lire-un-spread.md", GOOD.replace("structure-tendance.svg", figure))
    article(folder, "brouillon.md", GOOD.replace('status = "published"', 'status = "draft"'))
    out = Path(tempfile.mkdtemp(prefix="sensitor-site-")) / "site"
    site = Site(BASE, APP, articles_root=folder)
    pages = site.write(out)
    paths = {p.path for p in pages}
    check("the pages are written", {"", "academy/", "articles/", "ressources/", "lettre/", "a-propos/",
                                    "articles/lire-un-spread/"} | {f"{p}/" for p in LEGAL_PATHS.values()} <= paths
          and all((out / p / "index.html").is_file() for p in paths))
    check("a draft is not published", not (out / "articles" / "brouillon").exists()
          and "brouillon" not in (out / "sitemap.xml").read_text())
    missing = []
    for page in paths:
        text = (out / page / "index.html").read_text(encoding="utf-8")
        for needle in ("<title>", '<meta name="description" content="', f'<link rel="canonical" href="{BASE}/{page}"',
                       '<meta property="og:title"', '<meta property="og:description"',
                       f'<meta property="og:url" content="{BASE}/{page}"', '<html lang="fr">'):
            if needle not in text:
                missing.append(f"{page or 'accueil'}: {needle}")
        if any(d in text for d in DASHES):
            missing.append(f"{page}: long dash")
    check("every page has its title, description, canonical address, Open Graph tags, and no long dash",
          not missing, str(missing[:5]))
    descriptions = [re.search(r'name="description" content="([^"]*)"', (out / p / "index.html").read_text()).group(1)
                    for p in paths]
    check("descriptions are distinct and not empty", len(set(descriptions)) == len(descriptions) and all(descriptions))
    page = (out / "articles" / "lire-un-spread" / "index.html").read_text(encoding="utf-8")
    check("an article page: type article, its dates, its opinion framed, its figure, its sources",
          'og:type" content="article"' in page and "article:modified_time\" content=\"2026-10-28\"" in page
          and 'class="callout opinion"' in page and f"assets/figures/{figure}" in page
          and (out / "assets" / "figures" / figure).is_file() and "<h2>Sources</h2>" in page)
    sitemap = (out / "sitemap.xml").read_text()
    check("the sitemap lists every page, with the article's last review",
          all(f"<loc>{BASE}/{p}</loc>" in sitemap for p in paths)
          and "<lastmod>2026-10-28</lastmod>" in sitemap)
    feed = (out / "feed.xml").read_text()
    check("the RSS feed carries the article", "<rss version=\"2.0\">" in feed
          and f"<link>{BASE}/articles/lire-un-spread/</link>" in feed and "Lire un spread avant d'entrer" in feed
          and "<language>fr-FR</language>" in feed)
    check("robots.txt points at the sitemap", f"Sitemap: {BASE}/sitemap.xml" in (out / "robots.txt").read_text())
    hosts = set()
    for path in out.rglob("*"):
        if path.suffix in (".html", ".css"):
            hosts |= set(re.findall(r"(?:src|href)=\"(https?://[^/\"]+)", path.read_text(encoding="utf-8")))
            hosts |= set(re.findall(r"url\((https?://[^/)]+)", path.read_text(encoding="utf-8")))
    check("no page calls a third party: only the site and the member area",
          hosts <= {BASE, APP} and not any("google" in h for h in hosts), str(hosts))
    check("no script and no cookie on the public site",
          not any("<script" in p.read_text(encoding="utf-8") for p in out.rglob("*.html")))
    check("the fonts are the platform's own files", (out / "assets" / "fonts" / "fonts.css").is_file()
          and len(list((out / "assets" / "fonts").glob("*.woff2"))) >= 10)
    free = {r.pdf.name for r in site.catalog.resources.values() if r.access == "public" and r.pdf}
    copied = {p.name for p in (out / "assets" / "fiches").iterdir()}
    check("only the free revision sheets are copied", copied == free and len(free) >= 1, str(copied ^ free))
    academy = (out / "academy" / "index.html").read_text(encoding="utf-8")
    public = [lesson for course in site.catalog.courses.values() for lesson in course.lessons if lesson.is_public]
    check("the programme links every free lesson to the member area",
          all(f"page=lesson&amp;course={lesson.course_id}&amp;lesson={lesson.id}" in academy for lesson in public))
    home = (out / "index.html").read_text(encoding="utf-8")
    counts = site._universe_counts()
    check("the home page states the lesson counts the catalogue computes",
          f"{counts['trading'][0]} leçons publiées, dont {counts['trading'][1]} en accès libre" in home
          and f"{counts['monnaie'][0]} leçons publiées, dont {counts['monnaie'][1]} en accès libre" in home
          and counts["monnaie"][0] > 0)
    legal = (out / "mentions-legales" / "index.html").read_text(encoding="utf-8")
    check("the legal pages name Sensitor, with no gap, and keep the banner until the texts are reviewed",
          "Texte en cours de finalisation" in legal and "[à compléter]" not in legal and "Sensitor" in legal)
    check("the newsletter button opens the member area's form", f'{APP}/?page=newsletter' in home)
    check("the template article is never published", not (out / "articles" / "_modele").exists())


def main() -> int:
    test_validator()
    test_build()
    failures = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS)} checks, {len(failures)} failures")
    for name, _, detail in failures:
        print(f"  FAIL  {name}   {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
