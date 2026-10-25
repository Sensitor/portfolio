"""
The « Portefeuille et risque » space: the portfolio analyzer inside the member
space, on the same account and the same working portfolio as the separate app.

Nothing of the analysis is rewritten. The eleven analysis pages are the
`sensitor.pages` renderers, given the same context the separate app builds
(`investment.context.build_context`) and styled by the analyzer's component
stylesheet (`ui.themes.inject_components`), which carries no page, sidebar or
widget rule of its own. What this module adds is the platform side: a page to
build and analyse a portfolio, the space's navigation, and the bridge to the
working portfolio stored per member (`pages._workspace`), so a portfolio built
here is the one the separate app opens, and the other way round.

What stays in the separate app for now, and says so on the building page: the
real portfolio in quantities, prices entered by hand, model portfolios, the
asset library and the MetaTrader 5 analytics.

The analyzer itself is kept in session state, as in the separate app: it belongs
to this browser session only, and only the allocation is written to the store,
under the verified email.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

from ...academy import access as A
from ...core import config as core_config
from ...investment import assets
from ...investment.context import build_context
from ...investment.currency import BASE_CURRENCIES, currency_symbol
from ...investment.portfolio import UltimatePortfolioAnalyzer
from ...pages import (render_copilot, render_health, render_optimize, render_overview, render_performance,
                      render_portfolios, render_reports, render_risk, render_simulator, render_stress,
                      render_xray)
from ...pages import _workspace
from ...pages._shared import get_store as analysis_store
from ...ui import themes as analysis_theme
from .. import spaces
from . import runtime as rt
from .components import crumbs, esc, footer, html, note, notice, page_header, section

BUILD = "portfolio"
TABS = (
    ("pf_overview", "Vue d'ensemble", render_overview),
    ("pf_performance", "Performance", render_performance),
    ("pf_health", "Santé", render_health),
    ("pf_xray", "Radiographie", render_xray),
    ("pf_risk", "Risque", render_risk),
    ("pf_stress", "Stress tests", render_stress),
    ("pf_optimize", "Optimiser", render_optimize),
    ("pf_simulator", "Simulateur", render_simulator),
    ("pf_copilot", "Copilote", render_copilot),
    ("pf_reports", "Rapports", render_reports),
    ("pf_portfolios", "Portefeuilles", render_portfolios),
)
PAGES = (BUILD,) + tuple(page for page, _label, _render in TABS)
PROFILES = {"safe": "Prudent", "balanced": "Équilibré", "aggressive": "Dynamique"}
HISTORY_DAYS = 730
ELSEWHERE = ("le portefeuille réel en quantités, avec sa valeur du jour", "les prix saisis à la main pour une ligne "
             "non cotée", "les portefeuilles modèles et la bibliothèque d'actifs", "l'analytique des trades "
             "synchronisés depuis MetaTrader 5")


# =============================================================================
# Session
# =============================================================================

def _prepare(email: str | None) -> None:
    """
    The analysis pages read the separate app's session keys; set them for a
    French, simulation-mode session, then bring back the member's working
    portfolio and price it once, as the separate app does after a restart.
    """
    state = st.session_state
    state["language"] = "fr"
    state.setdefault("analysis_mode", "simulation")
    state.setdefault("user_profile", "balanced")
    state.setdefault("base_currency", "USD")
    state.setdefault("sensitor_period", "MAX")
    state.setdefault("current_portfolio", None)
    state.setdefault("selected_tickers", [])
    state.setdefault("weights", {})
    state["user_tier"] = "pro" if A.has_premium(rt.tier(email)) else "free"
    store = analysis_store()
    if email and _workspace.restore(store, email) and state["analysis_mode"] != "simulation":
        # A real portfolio, in quantities, is analysed in the separate app.
        state["analysis_mode"] = "simulation"
    if _workspace.take_resume_flag() and state["selected_tickers"] and state["current_portfolio"] is None:
        _analyse(list(state["selected_tickers"]), dict(state["weights"]), quiet=True)


def _persist(email: str | None) -> None:
    if email:
        _workspace.persist(analysis_store(), email)


def _analyse(tickers: list[str], weights: dict, *, quiet: bool = False) -> bool:
    """Price the allocation over the last two years, in the chosen currency, behind a progress bar."""
    state = st.session_state
    analyzer = UltimatePortfolioAnalyzer(
        tickers, weights, (datetime.now() - timedelta(days=HISTORY_DAYS)).strftime("%Y-%m-%d"),
        base_currency=state.get("base_currency", "USD"), user_profile=state.get("user_profile", "balanced"))
    bar, status = st.progress(0), st.empty()

    def progress(fraction, label):
        status.text(label)
        bar.progress(min(max(fraction, 0.0), 1.0))

    def on_error(ticker, message):
        if not quiet:
            st.warning(f"{ticker} : {message}")

    try:
        ok = analyzer.fetch_data(progress=progress, on_error=on_error)
    finally:
        bar.empty()
        status.empty()
    if ok:
        state["current_portfolio"] = analyzer
    elif not quiet:
        st.error("Les prix n'ont pas pu être chargés. Vérifiez les lignes, ou réessayez dans un instant.")
    return bool(ok)


def _context():
    analyzer = st.session_state.get("current_portfolio")
    if analyzer is None:
        return None
    return build_context(
        analyzer, lang="fr", profile=st.session_state.get("user_profile", "balanced"),
        period=st.session_state.get("sensitor_period", "MAX"), asset_info=assets.ASSET_INFO,
        sector_map=assets.SECTOR_MAPPING, geo_map=assets.GEOGRAPHY_MAPPING, is_real=False, current_value=None,
        currency=currency_symbol(getattr(analyzer, "base_currency", "USD")))


def _nav(page: str) -> None:
    with st.container(key="jnav_portfolio", horizontal=True):
        rt.link("Construire", BUILD, key="pfnav_build", kind="primary" if page == BUILD else "secondary")
        for target, label, _render in TABS:
            rt.link(label, target, key=f"pfnav_{target}", kind="primary" if page == target else "secondary")


def _space():
    return spaces.space("tools")


# =============================================================================
# Building a portfolio
# =============================================================================

def build_page(catalog, email, route) -> None:
    space = _space()
    _prepare(email)
    crumbs("Sensitor", space.label)
    page_header(f"Espace {space.numeral} · {esc(space.label)}", "Analyser son portefeuille, <em>sur le même compte</em>.",
                "Choisir ses lignes et leur poids, puis lire la performance, le risque, la santé, les stress tests "
                "et la simulation, avec la marge « Lecture » de chaque écran.")
    _nav(BUILD)
    state = st.session_state
    analyzer = state.get("current_portfolio")
    if analyzer is not None:
        _current(analyzer)
    if not email:
        notice("Sans compte", "L'analyse reste dans cette session et disparaît en fermant la page. Avec un compte, le "
               "portefeuille de travail est gardé, ici comme dans l'application complète.", "info")
    section(1, "Composer le portefeuille" if analyzer is None else "Modifier le portefeuille",
            "Les lignes, leur poids, la devise et votre profil de risque. Les prix couvrent les deux dernières années.")
    _form(state)
    section(2, "Dans l'application complète", "Ce qui n'a pas encore rejoint l'espace membre.")
    html('<ul class="sx-c-facts">' + "".join(f"<li>{esc(x[:1].upper() + x[1:])}.</li>" for x in ELSEWHERE) + "</ul>")
    url = rt.tools_url()
    if url:
        st.link_button("Ouvrir l'application complète", f"{url.rstrip('/')}/?page=overview")
    else:
        note("L'adresse de l'application complète n'est pas renseignée pour ce déploiement (variable SENSITOR_TOOLS_URL).")
    _persist(email)
    footer()


def _current(analyzer) -> None:
    weights = dict(getattr(analyzer, "weights", {}) or {})
    rows = "".join(f"<tr><td><b>{esc(t)}</b></td><td>{esc(_name(t))}</td><td>{w * 100:.1f} %</td></tr>"
                   for t, w in sorted(weights.items(), key=lambda kv: -kv[1]))
    state = st.session_state
    html(f'<div class="sx-c-blank"><div class="rub">Portefeuille analysé · {esc(state.get("base_currency", "USD"))} · '
         f'profil {esc(PROFILES.get(state.get("user_profile", "balanced"), ""))}</div>'
         f'<h3>{len(weights)} ligne{"s" if len(weights) > 1 else ""}, prêtes à lire.</h3>'
         f'<table><thead><tr><th>Ligne</th><th>Nom</th><th>Poids</th></tr></thead><tbody>{rows}</tbody></table></div>')
    rt.link("Lire la vue d'ensemble", "pf_overview", key="pf_go_overview", kind="primary")


def _name(ticker: str) -> str:
    return str((assets.ASSET_INFO.get(ticker) or {}).get("name") or ticker)


def _form(state) -> None:
    allowed = core_config.tier_limits(state.get("user_tier", "free"))["max_assets"]
    universe = sorted(assets.ASSET_INFO)
    current = [t for t in state.get("selected_tickers") or [] if t in assets.ASSET_INFO]
    # A portfolio built elsewhere with more lines stays whole: it can be edited, not grown.
    limit = max(allowed, len(current))
    with st.container(key="panel_pf_build"):
        if len(current) > allowed:
            note(f"Ce portefeuille compte {len(current)} lignes ; un compte gratuit en compose {allowed} au plus. "
                 "Vous pouvez le modifier, pas l'agrandir.")
        chosen = st.multiselect(f"Lignes (au plus {limit})", universe, default=current, key="pf_tickers",
                                format_func=lambda t: f"{t} · {_name(t)}", max_selections=limit,
                                placeholder="Chercher une action, un ETF, une cryptomonnaie")
        weights = {}
        if chosen:
            html('<div class="sx-kicker" style="margin-top:.6rem">Poids, en %</div>')
            cols = st.columns(min(len(chosen), 4))
            saved = state.get("weights") or {}
            for i, ticker in enumerate(chosen):
                with cols[i % len(cols)]:
                    default = round(float(saved.get(ticker, 1 / len(chosen))) * 100, 1)
                    weights[ticker] = st.number_input(ticker, min_value=0.0, max_value=100.0, value=default, step=1.0,
                                                      format="%.1f", key=f"pf_w_{ticker}")
        c1, c2 = st.columns(2)
        with c1:
            options = list(BASE_CURRENCIES)
            base = st.selectbox("Devise du portefeuille", options, key="pf_currency",
                                index=options.index(state.get("base_currency", "USD"))
                                if state.get("base_currency", "USD") in options else 0)
        with c2:
            keys = list(PROFILES)
            profile = st.selectbox("Profil de risque", keys, format_func=PROFILES.get, key="pf_profile",
                                   index=keys.index(state.get("user_profile", "balanced"))
                                   if state.get("user_profile", "balanced") in keys else 1)
        total = sum(weights.values())
        if chosen and abs(total - 100) > 0.05:
            note(f"Les poids font {total:.1f} % : ils seront ramenés à 100 % en gardant leurs proportions.")
        if st.button("Analyser le portefeuille", type="primary", key="pf_analyse", disabled=not chosen or total <= 0):
            fractions = {t: w / total for t, w in weights.items() if w > 0}
            state["selected_tickers"] = list(fractions)
            state["weights"] = fractions
            state["base_currency"] = base
            state["user_profile"] = profile
            state["analysis_mode"] = "simulation"
            state["current_portfolio"] = None
            if _analyse(list(fractions), fractions):
                rt.go("pf_overview")
                st.rerun()


# =============================================================================
# The analysis pages
# =============================================================================

# The analysis pages navigate the separate app's way, by setting `page`: the
# copilot sends a change to the simulator, the portfolios page asks for a new
# analysis of a saved allocation. Here those become the platform's pages.
_HOPS = {**{page[3:]: page for page, _label, _render in TABS}, "new_analysis": BUILD}


def _hop(email: str | None) -> None:
    target = _HOPS.get(st.session_state.pop("page", None))
    if not target:
        return
    if target == BUILD:
        st.session_state["current_portfolio"] = None
        for key in [k for k in st.session_state if str(k) == "pf_tickers" or str(k).startswith("pf_w_")]:
            del st.session_state[key]           # the form opens on the loaded allocation
        _persist(email)
    rt.go(target)
    st.rerun()

def _page(page: str, render):
    def renderer(catalog, email, route) -> None:
        space = _space()
        _prepare(email)
        _hop(email)
        crumbs("Sensitor", space.label, dict((p, l) for p, l, _r in TABS)[page])
        _nav(page)
        analysis_theme.inject_components()
        ctx = _context()
        if ctx is None:
            html('<div class="sx-c-blank"><div class="rub">Aucun portefeuille analysé</div>'
                 '<h3>Composez d\'abord un portefeuille.</h3><p>Choisissez vos lignes et leur poids : chaque écran de '
                 'l\'espace lit ensuite la même analyse.</p></div>')
            rt.link("Composer un portefeuille", BUILD, key="pf_empty_build", kind="primary")
            footer()
            return
        render(ctx)
        st.session_state["sensitor_period"] = ctx.period
        _hop(email)
        _persist(email)
        footer()
    renderer.__name__ = f"render_{page}"
    return renderer


RENDERERS = {BUILD: build_page, **{page: _page(page, render) for page, _label, render in TABS}}
