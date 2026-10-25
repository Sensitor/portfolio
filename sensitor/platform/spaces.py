"""
The spaces of the Sensitor platform.

Pure data, no Streamlit: the shell builds its navigation from this registry, the
tests check it, and a future web client can serve it as-is.

Status is stated, never implied:

* `live`      — the space works and its pages render real content;
* `preparing` — announced, with one honest page saying what it will contain and
                what already exists elsewhere. It has no other page and no
                imitation feature;
* `separate`  — exists as a separate application (the portfolio and trading
                analytics), reachable by link when its address is configured.
"""

from __future__ import annotations

from dataclasses import dataclass

LIVE = "live"
PREPARING = "preparing"
SEPARATE = "separate"
STATUS_LABELS = {LIVE: "Ouvert", PREPARING: "En préparation", SEPARATE: "Application séparée"}

GROUPS = (
    ("apprendre", "Apprendre"),
    ("trader", "Trader"),
    ("investir", "Investir"),
    ("echanger", "Échanger"),
)


@dataclass(frozen=True)
class Space:
    id: str
    label: str
    group: str
    status: str
    summary: str
    entry: str                                  # the page the navigation opens
    pages: tuple[str, ...]
    planned: tuple[str, ...] = ()               # what is announced, for preparing spaces
    related: tuple[tuple[str, str], ...] = ()   # (label, page) of real features related to it
    numeral: str = ""
    edition: str = ""                           # "" (working pages) or "bulletin" (pages that are read)

    @property
    def status_label(self) -> str:
        return STATUS_LABELS[self.status]

    @property
    def is_live(self) -> bool:
        return self.status == LIVE


SPACES: tuple[Space, ...] = (
    Space("academy", "Academy", "apprendre", LIVE,
          "Deux univers qui se complètent : le trading, de la première bougie au processus discipliné, "
          "et la monnaie, Bitcoin et la crypto, pour comprendre la valeur de l'argent et diversifier. "
          "Des parcours sourcés, des quiz corrigés et des exercices chiffrés.",
          entry="academy", pages=("academy", "course", "lesson", "quiz"), numeral="I",
          planned=("La méthode Sensitor et la méthode du fondateur, rédigées par le fondateur",
                   "Les cycles et les indicateurs de Bitcoin, dès qu'une licence de prix sera obtenue",
                   "Vidéos intégrées aux leçons", "Ebooks"),
          edition="bulletin"),
    Space("library", "Bibliothèque", "apprendre", LIVE,
          "Fiches de révision et checklists, liées aux leçons qui les utilisent.",
          entry="library", pages=("library", "resource"), numeral="II",
          edition="bulletin"),
    Space("psychology", "Psychologie et discipline", "apprendre", LIVE,
          "Un journal de réflexion privé avec sa routine de séance, et le parcours 6 sur les biais "
          "et les routines.",
          entry="psychology", pages=("psychology",), numeral="III",
          related=(("Parcours 6 : Décider sous incertitude", "course:decider-sous-incertitude"),
                   ("La routine de séance", "resource:routine-de-seance"),
                   ("La checklist avant chaque trade", "resource:checklist-avant-trade"))),
    Space("progress", "Progression", "apprendre", LIVE,
          "Leçons terminées, historique des quiz et notions à revoir.",
          entry="progress", pages=("progress",), numeral="IV",
          edition="bulletin"),
    Space("lab", "Trading Lab", "trader", LIVE,
          "Le calculateur de risque, le simulateur de ruine, le simulateur de challenge prop firm et les "
          "exercices, sans capital réel.",
          entry="lab", pages=("lab",), numeral="V",
          planned=("Études de cas sur graphiques annotés", "Simulations de scénarios")),
    Space("journal", "Journal de trading", "trader", LIVE,
          "Chaque trade jugé sur votre propre plan : revue automatique règle par règle, coût des "
          "écarts en R, calendrier de régularité, et revue d'un trade par un coach.",
          entry="journal",
          pages=("journal", "journal_trades", "journal_trade", "journal_add", "journal_plan",
                 "journal_reviews"),
          numeral="VI",
          planned=("Synchronisation MetaTrader 5 dans cet espace (aujourd'hui dans l'application "
                   "d'analyse, sur le même compte)",
                   "Captures de graphique jointes à un trade"),
          related=(("Parcours 10 : Construire son processus de trading", "course:processus-de-trading"),
                   ("Parcours 11 : Réussir un challenge prop firm", "course:reussir-un-challenge"),
                   ("Le modèle de plan de trading", "resource:modele-plan-de-trading"))),
    Space("market", "Salle des marchés", "trader", LIVE,
          "La séance préparée avant l'ouverture, contexte, calendrier et scénarios avec leur invalidation, "
          "puis son bilan pédagogique après la clôture. Sans signaux.",
          entry="market", pages=("market", "market_session", "market_edit"), numeral="VII",
          planned=("Être prévenu à la publication d'une séance",),
          related=(("Préparer sa séance", "lesson:processus-de-trading/preparer-seance"),
                   ("Construire un scénario de liquidité", "lesson:liquidite-et-scenarios/scenario-liquidite"),
                   ("Lire le calendrier économique", "lesson:trader-l-actualite/calendrier-economique"))),
    Space("tools", "Portefeuille et risque", "investir", LIVE,
          "Simuler une allocation ou suivre son portefeuille réel au prix du jour, puis le lire : performance, "
          "santé, radiographie, risque, stress tests, optimisation, simulation et Monte Carlo.",
          entry="portfolio",
          pages=("portfolio", "pf_overview", "pf_performance", "pf_health", "pf_xray", "pf_risk", "pf_stress",
                 "pf_optimize", "pf_simulator", "pf_copilot", "pf_reports", "pf_portfolios"),
          numeral="VIII",
          planned=("Les portefeuilles modèles et la bibliothèque d'actifs",),
          related=(("Investir dans la crypto avec méthode", "course:investir-avec-methode"),)),
    Space("community", "Communauté", "echanger", PREPARING,
          "Questions, analyses partagées et retours d'expérience entre membres.",
          entry="community", pages=("community",), numeral="IX",
          planned=("Discussions par thème et par parcours",
                   "Partage d'analyses avec leur invalidation",
                   "Retours d'expérience authentiques, sans résultats mis en scène")),
)

PLATFORM_PAGES = ("home", "account", "reset", "verify", "coach")
LEGACY_PAGES = {"paths": "academy",       # URLs from the first Academy release
                "tools": "portfolio"}     # the link page of the analyzer, before it joined the space


def all_pages() -> tuple[str, ...]:
    return PLATFORM_PAGES + tuple(p for s in SPACES for p in s.pages)


def resolve_page(page: str | None) -> str:
    page = LEGACY_PAGES.get(page or "", page or "home")
    return page if page in all_pages() else "home"


def space(space_id: str) -> Space | None:
    return next((s for s in SPACES if s.id == space_id), None)


def space_of(page: str) -> Space | None:
    return next((s for s in SPACES if page in s.pages), None)


def edition_of(page: str) -> str:
    """
    The « Carnet de bord » edition of a page: "bulletin" where one reads, "" where
    one works. Every page is drawn in the direction (docs/DIRECTION_ARTISTIQUE.md);
    a space chooses its edition here, and nothing else has to change.
    """
    space_ = space_of(page)
    return space_.edition if space_ else ""


def by_group() -> list[tuple[str, list[Space]]]:
    return [(label, [s for s in SPACES if s.group == gid]) for gid, label in GROUPS]


def parse_target(target: str) -> tuple[str, dict]:
    """
    Read a `related` target: "resource:<id>", "course:<id>", "lesson:<course>/<lesson>",
    or a page id. Returns (page, route fields).
    """
    kind, _, rest = target.partition(":")
    if kind == "resource" and rest:
        return "resource", {"resource": rest}
    if kind == "course" and rest:
        return "course", {"course": rest}
    if kind == "lesson" and "/" in rest:
        course, lesson = rest.split("/", 1)
        return "lesson", {"course": course, "lesson": lesson}
    return target, {}
