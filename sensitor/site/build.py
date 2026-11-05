"""
The public site, generated from `content/`.

    python scripts/build_site.py --base-url https://sensitor.fr --app-url https://app.sensitor.fr

Writes a folder of static pages (`site/` by default) that any static host serves
(Cloudflare Pages, Netlify, GitHub Pages): the home page, the articles
(`content/media/articles`), the Academy's programme (tracks, paths, courses and
their free lessons, read from the same catalogue as the platform), the free
revision sheets with their PDFs, the newsletter, the legal pages
(`content/legal`), and what search engines need: a title, a description, a
canonical address and Open Graph tags on every page, `sitemap.xml`, `feed.xml`
(RSS 2.0) and `robots.txt`.

One source of truth: nothing is copied by hand. A lesson is read in the
platform (formulas, simulators and quizzes live there); the site lists it and
links to it. The fonts are the platform's own files, so a visitor's browser
contacts no third party. No JavaScript, no cookie, no measurement.

No Streamlit.
"""

from __future__ import annotations

import datetime as _dt
import html
import shutil
from dataclasses import dataclass
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from ..academy import printable
from ..academy.content import CONTENT_ROOT, MONNAIE, TRADING, Catalog, load_catalog
from ..platform import brand, legal
from . import articles as A

REPO = Path(__file__).resolve().parents[2]
ADDRESSES = REPO / "content" / "site.toml"


def addresses(path: Path = ADDRESSES) -> dict[str, str]:
    """The member area's and the public site's addresses, from `content/site.toml` (empty when absent)."""
    import tomllib
    data = {}
    if path.is_file():
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    return {key: str(data.get(key, "")).strip().rstrip("/") for key in ("app_url", "site_url")}
FONTS = REPO / "static" / "fonts"
MONTHS = legal.MONTHS
SITE_NAME = "Sensitor"
TAGLINE = "Apprendre le trading. Diversifier avec la crypto."
DISCLAIMER = ("Sensitor est un service de formation. Aucun contenu ne constitue un conseil en investissement ni "
              "une promesse de résultat. Le trading et les crypto-actifs comportent un risque de perte en capital.")
LEGAL_PATHS = {"mentions": "mentions-legales", "conditions": "conditions", "confidentialite": "confidentialite"}
NAV = (("academy/", "Academy"), ("articles/", "Articles"), ("ressources/", "Ressources"),
       ("a-propos/", "À propos"), ("lettre/", "La lettre"))


@dataclass(frozen=True)
class Page:
    path: str                 # « » for the home page, « articles/ » for a folder page
    title: str
    description: str
    body: str
    kind: str = "website"     # Open Graph type: « article » for an article
    modified: _dt.date | None = None


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def date_fr(day: _dt.date) -> str:
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


class Site:
    def __init__(self, base_url: str, app_url: str, *, catalog: Catalog | None = None,
                 articles_root: Path = A.ROOT, legal_root: Path = legal.ROOT, today: _dt.date | None = None):
        self.base = base_url.rstrip("/") + "/"
        self.app = app_url.rstrip("/")
        self.catalog = catalog or load_catalog()
        self.articles = A.published(articles_root)
        self.legal_root = legal_root
        self.today = today or _dt.date.today()

    # ── addresses ────────────────────────────────────────────────────────────

    def url(self, path: str) -> str:
        return self.base + path

    def app_link(self, page: str = "", **fields) -> str:
        """
        A link into the platform. It carries `utm_source=site`, so an account
        the site brings is counted as such in the statistics: the site itself
        measures nothing.
        """
        query = "&".join(f"{k}={v}" for k, v in (("page", page), *fields.items(), ("utm_source", "site")) if v)
        return f"{self.app}/?{query}"

    @staticmethod
    def rel(page_path: str, target: str) -> str:
        """A link from one page to another, relative, so the site works from any folder or host."""
        depth = page_path.count("/")
        return "../" * depth + target if target else ("../" * depth or "./")

    # ── layout ───────────────────────────────────────────────────────────────

    def render(self, page: Page) -> str:
        r = lambda target: self.rel(page.path, target)          # noqa: E731
        nav = "".join(f'<a href="{r(t)}"{" aria-current=page" if page.path.startswith(t) else ""}>{esc(l)}</a>'
                      for t, l in NAV)
        legal_links = " · ".join(f'<a href="{r(p + "/")}">{esc(legal.PAGES[k][1])}</a>' for k, p in LEGAL_PATHS.items())
        title = page.title if page.path == "" else f"{page.title} · {SITE_NAME}"
        modified = (f'<meta property="article:modified_time" content="{page.modified.isoformat()}">'
                    if page.modified else "")
        return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(page.description)}">
<link rel="canonical" href="{esc(self.url(page.path))}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:locale" content="fr_FR">
<meta property="og:type" content="{page.kind}">
<meta property="og:title" content="{esc(page.title)}">
<meta property="og:description" content="{esc(page.description)}">
<meta property="og:url" content="{esc(self.url(page.path))}">
{modified}
<link rel="alternate" type="application/rss+xml" title="Articles de Sensitor" href="{esc(self.url('feed.xml'))}">
<link rel="stylesheet" href="{r('assets/fonts/fonts.css')}">
<link rel="stylesheet" href="{r('assets/site.css')}">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="{r('')}">{brand.mark_svg(34, uid="top")}<span>SENSITOR</span></a>
<nav aria-label="Navigation principale">{nav}</nav>
<a class="cta" href="{esc(self.app_link('account'))}">Se connecter</a>
</div></header>
<main class="wrap">
{page.body}
</main>
<footer class="foot"><div class="wrap">
<p class="disclaimer">{esc(DISCLAIMER)}</p>
<p>{legal_links} · <a href="{esc(self.url('feed.xml'))}">Flux RSS</a></p>
<p class="small">© {self.today.year} Sensitor</p>
</div></footer>
</body>
</html>
"""

    # ── pages ────────────────────────────────────────────────────────────────

    def _universe_counts(self) -> dict[str, tuple[int, int]]:
        """(published lessons, free lessons) per universe, from the tracks' own universe."""
        counts: dict[str, list[int]] = {}
        for track in self.catalog.tracks:
            entry = counts.setdefault(track.universe, [0, 0])
            for path in self.catalog.paths_in(track.id):
                for course in path.courses:
                    entry[0] += len(course.lessons)
                    entry[1] += sum(1 for lesson in course.lessons if lesson.is_public)
        return {k: (v[0], v[1]) for k, v in counts.items()}

    def _article_cards(self, page_path: str, items) -> str:
        if not items:
            return '<p class="empty">Les premiers articles arrivent. Inscrivez-vous à la lettre pour les recevoir.</p>'
        return '<div class="cards">' + "".join(
            f'<a class="card {a.universe}" href="{self.rel(page_path, f"articles/{a.slug}/")}">'
            f'<span class="rub">{esc(a.universe_label)} · {esc(date_fr(a.date))}</span>'
            f'<h3>{esc(a.title)}</h3><p>{esc(a.summary)}</p></a>' for a in items) + "</div>"

    def home(self) -> Page:
        counts = self._universe_counts()
        trading, crypto = counts.get(TRADING, (0, 0)), counts.get(MONNAIE, (0, 0))
        free = [r for r in self.catalog.resources.values() if r.access == "public"]
        body = f"""
<section class="hero">
<p class="kicker">L'écosystème Sensitor</p>
<h1>Apprendre le <em>trading</em>.<br>Diversifier avec la <em class="cu">crypto</em>.</h1>
<p class="lead">Deux univers qui se complètent, sur un seul compte : le trading, pour lire un marché, mesurer
son risque et décider avec méthode ; la monnaie, Bitcoin et la crypto, pour comprendre ce qui fait la valeur de
l'argent et diversifier ses investissements dans le temps. Leçons sourcées, quiz corrigés, simulateurs et outils
d'analyse.</p>
<p class="actions"><a class="button primary" href="{esc(self.app_link('account'))}">Créer un compte gratuit</a>
<a class="button" href="academy/">Voir le programme</a></p>
</section>
<section class="universes">
<a class="universe trading" href="academy/#trading"><span class="rub">Trading</span>
<h2>Lire un marché, mesurer son risque</h2><p>{trading[0]} leçons publiées, dont {trading[1]} en accès libre.</p></a>
<a class="universe crypto" href="academy/#monnaie"><span class="rub">Monnaie et crypto</span>
<h2>Comprendre la monnaie, diversifier</h2><p>{crypto[0]} leçons publiées, dont {crypto[1]} en accès libre.</p></a>
</section>
<section><h2 class="section">Derniers articles</h2>{self._article_cards("", self.articles[:3])}</section>
<section><h2 class="section">Ressources gratuites</h2>
<p>{len(free)} fiche{"s" if len(free) > 1 else ""} de révision à télécharger, sans compte.
<a href="ressources/">Voir les ressources</a></p></section>
<section class="letter"><h2>La lettre de Sensitor</h2><p>Les nouveaux articles et les nouveautés de la plateforme,
par e-mail, avec votre accord. Désinscription en un clic.</p>
<p><a class="button primary" href="{esc(self.app_link('newsletter'))}">M'inscrire</a></p></section>
"""
        return Page("", f"Sensitor · {TAGLINE}",
                    "Formation au trading et à la crypto : leçons sourcées, quiz corrigés, simulateurs et outils "
                    "d'analyse. Un compte gratuit pour commencer.", body)

    def about(self) -> Page:
        body = f"""
<p class="kicker">À propos</p><h1>Ce qu'est <em>Sensitor</em>.</h1>
<p class="lead">Une plateforme française de formation au trading et à l'investissement, en deux univers qui se
complètent : le Trading, et la Monnaie et la crypto (la monnaie, l'inflation, Bitcoin, les crypto-actifs et
l'investissement).</p>
<h2>Les règles de la maison</h2>
<ul>
<li><strong>Chaque chiffre est sourcé ou calculé.</strong> Un chiffre dans une leçon vient d'un jeu de données
cité avec sa source, sa licence et sa date, ou d'un calcul expliqué. Un exemple construit le dit.</li>
<li><strong>Les faits, les opinions et les débats sont séparés.</strong> L'avis du fondateur est présenté comme
tel, les questions ouvertes aussi. Bitcoin n'est jamais présenté comme une protection garantie, aucun indicateur
comme un signal infaillible.</li>
<li><strong>Pas de conseil personnalisé, pas d'exécution d'ordre.</strong> Sensitor forme ; il ne recommande
ni n'achète rien pour vous.</li>
<li><strong>Jamais de phrase de récupération ni de clé privée.</strong> Sensitor ne vous les demandera
jamais.</li>
<li><strong>Vos données restent les vôtres.</strong> Votre journal, vos portefeuilles et votre progression ne
sont visibles que par vous ; vous pouvez tout télécharger ou tout supprimer depuis votre compte.</li>
</ul>
<h2>Ce que contient la plateforme</h2>
<p>L'Academy (leçons, quiz et exercices corrigés), une bibliothèque de fiches, un suivi de progression, un
espace de psychologie et de discipline, un journal de trading, un espace Portefeuille et risque et une salle
des marchés. <a href="{esc(self.app_link())}">Ouvrir la plateforme</a>.</p>
"""
        return Page("a-propos/", "À propos", "Ce qu'est Sensitor, ses règles : chiffres sourcés, opinions séparées "
                    "des faits, pas de conseil personnalisé, jamais de clé privée.", body)

    def academy(self) -> Page:
        parts = ['<p class="kicker">Academy</p><h1>Le <em>programme</em>.</h1><p class="lead">Les parcours, '
                 'leurs cours et leurs leçons. Les leçons en accès libre se lisent sans compte ; les autres '
                 'demandent un compte gratuit.</p>']
        seen: set[str] = set()
        for track in self.catalog.tracks:
            paths = self.catalog.paths_in(track.id)
            if not paths:
                continue
            css = "crypto" if track.universe == MONNAIE else "trading"
            anchor = f' id="{esc(track.universe)}"' if track.universe not in seen else ""
            seen.add(track.universe)
            parts.append(f'<h2 class="section {css}"{anchor}>{esc(track.title)}</h2>')
            if track.summary:
                parts.append(f"<p>{esc(track.summary)}</p>")
            for path in paths:
                parts.append(f'<h3>{esc(path.title)}</h3>')
                for course in path.courses:
                    free = [lesson for lesson in course.lessons if lesson.is_public]
                    lessons = "".join(
                        f'<li><a href="{esc(self.app_link("lesson", course=course.id, lesson=lesson.id))}">'
                        f'{esc(lesson.title)}</a></li>' for lesson in free)
                    parts.append(
                        f'<div class="course"><h4><a href="{esc(self.app_link("course", course=course.id))}">'
                        f'{esc(course.title)}</a></h4><p>{esc(course.summary)}</p>'
                        f'<p class="meta">{len(course.lessons)} leçons · {len(free)} en accès libre</p>'
                        + (f'<ul class="free">{lessons}</ul>' if lessons else "") + "</div>")
        return Page("academy/", "Le programme de l'Academy",
                    "Les parcours Trading et Monnaie et crypto de Sensitor : cours, leçons en accès libre, "
                    "quiz corrigés.", "\n".join(parts))

    def resources(self) -> Page:
        free = sorted((r for r in self.catalog.resources.values() if r.access == "public"), key=lambda r: r.title)
        items = "".join(
            f'<div class="course"><h4>{esc(r.title)}</h4><p>{esc(r.description)}</p>'
            f'<p class="meta">{esc(r.category)}'
            + (f' · <a href="../assets/fiches/{esc(r.pdf.name)}">Télécharger le PDF</a>' if r.pdf else "")
            + "</p></div>" for r in free)
        body = ('<p class="kicker">Ressources</p><h1>Les fiches <em>gratuites</em>.</h1><p class="lead">Des fiches '
                'de révision à télécharger, sans compte. Les autres fiches sont dans la bibliothèque de la '
                f'plateforme, avec un compte gratuit.</p>{items or "<p class=empty>Aucune fiche libre.</p>"}')
        return Page("ressources/", "Ressources gratuites", "Fiches de révision gratuites de Sensitor, en PDF, "
                    "sur le trading, la monnaie et la crypto.", body)

    def letter(self) -> Page:
        body = (f'<p class="kicker">La lettre</p><h1>Recevoir <em>la lettre</em>.</h1><p class="lead">Les nouveaux '
                'articles, les analyses pédagogiques et les nouveautés de la plateforme. Jamais de signal, jamais '
                'de recommandation d\'achat ou de vente.</p><ul><li>Inscription confirmée par un lien envoyé à '
                'votre adresse : rien n\'est envoyé sans cette confirmation.</li><li>Désinscription en un clic, '
                'depuis chaque message.</li><li>Votre adresse ne sert qu\'à la lettre.</li></ul>'
                f'<p><a class="button primary" href="{esc(self.app_link("newsletter"))}">M\'inscrire</a></p>')
        return Page("lettre/", "La lettre de Sensitor", "Inscription à la lettre de Sensitor : articles et "
                    "nouveautés, avec confirmation par e-mail et désinscription en un clic.", body)

    def article_index(self) -> Page:
        body = ('<p class="kicker">Articles</p><h1>Articles et <em>analyses</em>.</h1>'
                '<p class="lead">Pédagogiques et sourcés. Aucun n\'est un conseil en investissement.</p>'
                + self._article_cards("articles/", self.articles))
        return Page("articles/", "Articles", "Les articles de Sensitor sur le trading, la monnaie, Bitcoin et la "
                    "crypto : pédagogiques et sourcés.", body,
                    modified=max((a.last_modified for a in self.articles), default=None))

    def article(self, item: A.Article) -> Page:
        path = f"articles/{item.slug}/"
        parts = [f'<p class="kicker {item.universe}">{esc(item.universe_label)}</p><h1>{esc(item.title)}</h1>'
                 f'<p class="lead">{esc(item.summary)}</p><p class="meta">Par {esc(item.author)} · publié le '
                 f'{esc(date_fr(item.date))}' + (f' · relu le {esc(date_fr(item.updated))}' if item.updated else "")
                 + "</p>"]
        from ..academy.markup import CALLOUT_KINDS
        for block in item.blocks:
            if block.kind == "markdown":
                parts.append(printable.markdown_to_html(block.text))
            elif block.kind == "callout":
                kind = block.args[0]
                label = block.args[1] if len(block.args) > 1 else CALLOUT_KINDS[kind]
                parts.append(f'<aside class="callout {kind}"><p class="rub">{esc(label)}</p>'
                             f'{printable.markdown_to_html(block.text)}</aside>')
            elif block.kind == "figure":
                parts.append(f'<figure><img src="{self.rel(path, "assets/figures/" + block.target)}" alt="">'
                             f'<figcaption>{printable.markdown_to_html(block.text)}</figcaption></figure>')
        if item.sources:
            parts.append("<h2>Sources</h2><ul class=\"sources\">"
                         + "".join(f"<li>{esc(s)}</li>" for s in item.sources) + "</ul>")
        parts.append(f'<p class="meta"><a href="{self.rel(path, "articles/")}">Tous les articles</a></p>')
        return Page(path, item.title, item.summary, "\n".join(parts), kind="article", modified=item.last_modified)

    def legal_page(self, key: str) -> Page:
        doc = legal.document(key, self.legal_root)
        banner = ""
        if doc.missing or not doc.reviewed:
            banner = ('<aside class="callout warning"><p class="rub">Texte en cours de finalisation</p><p>'
                      + ("Certaines informations de l'éditeur restent à compléter. " if doc.missing else "")
                      + ("Ce texte n'a pas encore été relu par un juriste." if not doc.reviewed else "")
                      + "</p></aside>")
        body = (f'<p class="kicker">Informations légales</p><h1>{esc(doc.title)}</h1><p class="lead">'
                f'{esc(doc.summary)}</p>{banner}<div class="legal">{printable.markdown_to_html(doc.body)}</div>')
        return Page(f"{LEGAL_PATHS[key]}/", doc.title, doc.summary, body)

    def pages(self) -> list[Page]:
        return ([self.home(), self.academy(), self.article_index(), self.resources(), self.letter(), self.about()]
                + [self.article(a) for a in self.articles]
                + [self.legal_page(k) for k in LEGAL_PATHS])

    # ── feeds ────────────────────────────────────────────────────────────────

    def sitemap(self, pages: list[Page]) -> str:
        rows = "".join(f"<url><loc>{xml_escape(self.url(p.path))}</loc>"
                       + (f"<lastmod>{p.modified.isoformat()}</lastmod>" if p.modified else "") + "</url>"
                       for p in pages)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>\n')

    def feed(self) -> str:
        def when(day: _dt.date) -> str:
            return format_datetime(_dt.datetime(day.year, day.month, day.day, 8, 0, tzinfo=_dt.timezone.utc))
        items = "".join(
            f"<item><title>{xml_escape(a.title)}</title><link>{xml_escape(self.url(f'articles/{a.slug}/'))}</link>"
            f"<guid isPermaLink=\"true\">{xml_escape(self.url(f'articles/{a.slug}/'))}</guid>"
            f"<description>{xml_escape(a.summary)}</description><pubDate>{when(a.date)}</pubDate>"
            f"<category>{xml_escape(a.universe_label)}</category></item>" for a in self.articles)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
                f"<title>Articles de Sensitor</title><link>{xml_escape(self.base)}</link>"
                f"<description>{xml_escape(TAGLINE)}</description><language>fr-FR</language>{items}"
                "</channel></rss>\n")

    def robots(self) -> str:
        return f"User-agent: *\nAllow: /\nSitemap: {self.url('sitemap.xml')}\n"

    # ── writing ──────────────────────────────────────────────────────────────

    def write(self, out: Path) -> list[Page]:
        """Write the whole site into `out`, emptied first."""
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        pages = self.pages()
        for page in pages:
            target = out / page.path / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self.render(page), encoding="utf-8")
        (out / "sitemap.xml").write_text(self.sitemap(pages), encoding="utf-8")
        (out / "feed.xml").write_text(self.feed(), encoding="utf-8")
        (out / "robots.txt").write_text(self.robots(), encoding="utf-8")
        (out / "404.html").write_text(self.render(Page(
            "", "Page introuvable", "Cette page n'existe pas.",
            f'<h1>Page <em>introuvable</em>.</h1><p><a href="{esc(self.base)}">Revenir à l\'accueil</a></p>')),
            encoding="utf-8")
        assets = out / "assets"
        shutil.copytree(FONTS, assets / "fonts")
        (assets / "site.css").write_text(STYLE, encoding="utf-8")
        figures = {b.target for a in self.articles for b in a.blocks if b.kind == "figure"}
        if figures:
            (assets / "figures").mkdir()
            for name in figures:
                shutil.copy(CONTENT_ROOT / "figures" / name, assets / "figures" / name)
        (assets / "fiches").mkdir()
        for resource in self.catalog.resources.values():
            if resource.access == "public" and resource.pdf:
                shutil.copy(resource.pdf, assets / "fiches" / resource.pdf.name)
        return pages


STYLE = """
:root { --ink:#0f1b26; --ink-2:#18293a; --text:#23303a; --muted:#56616a; --paper:#f3f0e8; --white:#fffdf8;
  --line:#ddd8cb; --blue:#1f4a72; --blue-soft:#e0e8f0; --copper:#7e3c13; --copper-soft:#f4e2d4;
  --on-navy:#e9eef2; --on-navy-accent:#a9c6e2; --on-navy-copper:#e6b98e;
  --serif:'Playfair Display', Georgia, serif; --sans:'DM Sans', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
  --mono:'DM Mono', Consolas, monospace; }
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--paper); color: var(--text); font: 17px/1.65 var(--sans); }
.wrap { max-width: 1040px; margin: 0 auto; padding: 0 16px; }
a { color: var(--blue); }
h1, h2, h3, h4 { font-family: var(--serif); color: var(--ink); font-weight: 500; letter-spacing: -.015em; line-height: 1.15; }
h1 { font-size: clamp(2.1rem, 5vw, 3.2rem); margin: .3rem 0 1rem; }
h1 em, h2 em { color: var(--blue); } h1 em.cu { color: var(--copper); }
.kicker, .rub, .meta { font: 500 12.5px var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
.kicker.crypto { color: var(--copper); } .kicker.trading { color: var(--blue); }
.lead { font-size: 1.15rem; color: var(--ink-2); max-width: 720px; }
.top { background: var(--ink); color: var(--on-navy); }
.top .wrap { display: flex; align-items: center; gap: 1.2rem; flex-wrap: wrap; padding-top: .7rem; padding-bottom: .7rem; }
.brand { display: flex; align-items: center; gap: .6rem; color: #fff; text-decoration: none; font: 700 14px var(--sans); letter-spacing: .24em; }
.top nav { display: flex; gap: 1rem; flex-wrap: wrap; flex: 1; }
.top nav a { color: var(--on-navy); text-decoration: none; font-size: 15px; }
.top nav a[aria-current] { color: #fff; box-shadow: inset 0 -2px var(--on-navy-accent); }
.top .cta { color: var(--ink); background: var(--white); padding: .35rem .8rem; text-decoration: none; font-size: 14px; }
main { padding: 2.2rem 16px 3rem; }
.hero { background: var(--ink); color: var(--on-navy); margin: 0 0 2rem; padding: 2.6rem clamp(16px, 4vw, 2.6rem); }
.hero h1 { color: #fff; } .hero h1 em { color: var(--on-navy-accent); } .hero h1 em.cu { color: var(--on-navy-copper); }
.hero .lead { color: var(--on-navy); } .hero .kicker { color: var(--on-navy-accent); }
.button { display: inline-block; padding: .6rem 1.1rem; border: 1px solid currentColor; text-decoration: none; margin: .3rem .4rem .3rem 0; }
.button.primary { background: var(--blue); border-color: var(--blue); color: #fff; }
.hero .button { color: #fff; }
.universes, .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }
.universe, .card { display: block; background: var(--white); border: 1px solid var(--line); padding: 1.2rem; text-decoration: none; color: var(--text); }
.universe.trading, .card.trading { border-top: 3px solid var(--blue); }
.universe.crypto, .card.crypto { border-top: 3px solid var(--copper); }
.universe h2, .card h3 { margin: .3rem 0 .4rem; font-size: 1.35rem; }
h2.section { margin-top: 2.6rem; padding-top: 1rem; border-top: 1px solid var(--line); }
h2.section.crypto { border-top-color: var(--copper); } h2.section.trading { border-top-color: var(--blue); }
.course { background: var(--white); border: 1px solid var(--line); padding: 1rem 1.2rem; margin: .7rem 0; }
.course h4 { margin: 0 0 .3rem; font-size: 1.2rem; } .course p { margin: .3rem 0; }
.free { margin: .4rem 0 0; padding-left: 1.2rem; }
.letter { background: var(--blue-soft); padding: 1.4rem; margin-top: 2.6rem; }
.callout { background: var(--white); border-left: 3px solid var(--blue); padding: .8rem 1.1rem; margin: 1.2rem 0; }
.callout.opinion, .callout.debate { border-left-color: var(--copper); }
.callout.warning, .callout.mistake { border-left-color: #8c3a31; }
figure { margin: 1.5rem 0; } figure img { max-width: 100%; height: auto; }
figcaption { font-size: 15px; color: var(--muted); }
table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; margin: 1rem 0; display: block; overflow-x: auto; }
th { text-align: left; font: 500 12px var(--mono); letter-spacing: .08em; text-transform: uppercase; border-bottom: 1px solid var(--ink); padding: .4rem; }
td { border-bottom: 1px solid var(--line); padding: .4rem; vertical-align: top; }
code { font-family: var(--mono); font-size: .88em; background: var(--blue-soft); padding: 0 .25em; }
.empty { color: var(--muted); font-style: italic; }
.foot { background: var(--ink); color: var(--on-navy); padding: 2rem 0; font-size: 14.5px; }
.foot a { color: var(--on-navy); } .foot .small { color: #a9b7c4; }
.disclaimer { max-width: 760px; }
img, svg { max-width: 100%; }
@media (max-width: 720px) {
  .top .wrap { gap: .6rem 1rem; }
  .brand { flex: 1; }
  .top nav { order: 3; flex-basis: 100%; gap: .4rem 1rem; }
}
"""
