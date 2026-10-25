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

The model allocations and the asset library read the analyzer's catalogue
(`investment.assets`) but not all of it. A model's hand-written expected return
and volatility are left out, as are an asset's market cap, dividend yield and
allocation ranges: none of them is sourced, and a figure the platform shows is
sourced or computed. A model's composition by kind of asset is computed from its
weights, and its figures come from the analysis, once it is loaded. An asset's
prose is the platform's own sheet (`platform.asset_sheets`, from
`content/portfolio/fiches.toml`): what it is, the role usually given to it, and
the limit of that role.

The analyzer itself is kept in session state, as in the separate app: it belongs
to this browser session only, and only the allocation is written to the store,
under the verified email.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import re

import streamlit as st

from ...academy import access as A
from ...core import config as core_config
from ...investment import assets
from ...investment.context import build_context
from ...investment import holdings as H
from ...investment.currency import BASE_CURRENCIES, currency_symbol
from ...investment.portfolio import UltimatePortfolioAnalyzer, latest_prices
from ...pages import (render_copilot, render_health, render_optimize, render_overview, render_performance,
                      render_portfolios, render_reports, render_risk, render_simulator, render_stress,
                      render_xray)
from ...pages import _workspace
from ...pages._shared import get_store as analysis_store
from ...ui import themes as analysis_theme
from .. import asset_sheets, spaces
from . import runtime as rt
from .components import crumbs, esc, footer, html, icon, note, notice, page_header, section, tap

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
MODELS, ASSETS = "pf_models", "pf_assets"
PAGES = (BUILD, MODELS, ASSETS) + tuple(page for page, _label, _render in TABS)
PROFILES = {"safe": "Prudent", "balanced": "Équilibré", "aggressive": "Dynamique"}
HISTORY_DAYS = 730
MODEL_NAMES = {"Capital Preservation": "Préservation du capital", "Defensive Income": "Revenu défensif",
               "Classic 60/40": "Le classique 60/40", "Global Growth": "Croissance mondiale",
               "Tech Leaders": "Leaders de la tech", "Crypto & Innovation": "Crypto et innovation",
               "Dividend Champion": "Champions du dividende", "All-Weather": "Toutes saisons"}
# Written for the platform, without a figure or a promise; the composition line is computed.
MODEL_TEXTS = {
    "Capital Preservation": "Surtout des obligations, de l'or et une petite part d'actions américaines : une "
                            "composition qui cherche d'abord à moins baisser, au prix d'une croissance faible.",
    "Defensive Income": "Des actions à dividendes, des obligations, de l'immobilier coté et de l'or, avec peu "
                        "d'actions de croissance.",
    "Classic 60/40": "Inspiré du « 60/40 » des gestionnaires : une majorité d'actions, et un reste réparti ici entre "
                     "obligations, or et immobilier coté, pas seulement en obligations.",
    "Global Growth": "Des actions américaines, des pays développés hors États-Unis et des pays émergents, avec une "
                     "part d'obligations, d'or et d'immobilier coté.",
    "Tech Leaders": "Six grandes valeurs technologiques américaines et rien d'autre : un seul secteur, un seul pays.",
    "Crypto & Innovation": "Bitcoin, Ether et des valeurs technologiques : la composition la plus risquée de la "
                           "liste, sans aucune poche défensive.",
    "Dividend Champion": "Des actions à dividendes de secteurs réputés défensifs (santé, banque, énergie), de "
                         "l'immobilier coté et de l'or.",
    "All-Weather": "Inspiré de l'idée de Ray Dalio : répartir le risque entre actions, obligations longues et "
                   "matières premières. Aucune allocation ne traverse tous les environnements sans perte.",
}
KINDS = {"Fixed Income": "obligations", "Commodities": "or et matières premières", "Real Estate": "immobilier coté",
         "Cryptocurrency": "cryptomonnaies", "Crypto": "cryptomonnaies"}
CLASSES = {"Stock": "Action", "ETF": "ETF", "Crypto": "Cryptomonnaie"}
RISKS = {"Low": "faible", "Low-Medium": "faible à moyen", "Medium": "moyen", "Medium-High": "moyen à élevé",
         "High": "élevé", "Very High": "très élevé"}
SECTORS = {"Automotive": "Automobile", "Commodities": "Matières premières", "Consumer": "Consommation",
           "Crypto": "Crypto", "Cryptocurrency": "Cryptomonnaie", "Disruptive Tech": "Technologies de rupture",
           "Diversified": "Diversifié", "Dividend/Income": "Dividendes", "Emerging Markets": "Marchés émergents",
           "Energy": "Énergie", "Financials": "Finance", "Fixed Income": "Obligations", "Healthcare": "Santé",
           "Industrials": "Industrie", "International Developed": "Pays développés hors États-Unis",
           "International Diversified": "International diversifié", "Materials": "Matériaux",
           "Real Estate": "Immobilier", "Technology": "Technologie", "Technology-Heavy": "Dominante technologique",
           "Telecom": "Télécoms", "Utilities": "Services publics"}
GEOGRAPHIES = {"Developed Ex-US": "Pays développés hors États-Unis", "Emerging Markets": "Marchés émergents",
               "Ex-US Global": "Monde hors États-Unis", "France": "France", "Global": "Monde", "USA": "États-Unis"}
MODES = {"simulation": "Simulation, en poids", "real": "Portefeuille réel, en quantités"}
MAX_CUSTOM = 24


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
    state.setdefault("real_portfolio_holdings", {})
    state.setdefault("manual_prices", {})
    state["user_tier"] = "pro" if A.has_premium(rt.tier(email)) else "free"
    if email:
        _workspace.restore(analysis_store(), email)
    if _workspace.take_resume_flag() and state["current_portfolio"] is None:
        if state["analysis_mode"] == "real" and state["real_portfolio_holdings"]:
            _value_and_analyse(quiet=True)
        elif state["selected_tickers"]:
            _analyse(list(state["selected_tickers"]), dict(state["weights"]), quiet=True)


def _persist(email: str | None) -> None:
    if email:
        _workspace.persist(analysis_store(), email)


def _analyse(tickers: list[str], weights: dict, *, quiet: bool = False, initial_value: float | None = None):
    """
    Price the allocation over the last two years, in the chosen currency, behind a
    progress bar. Returns the analyzer, also kept in the session, or None.
    """
    state = st.session_state
    extra = {} if initial_value is None else {"initial_value": initial_value}
    analyzer = UltimatePortfolioAnalyzer(
        tickers, weights, (datetime.now() - timedelta(days=HISTORY_DAYS)).strftime("%Y-%m-%d"),
        base_currency=state.get("base_currency", "USD"), user_profile=state.get("user_profile", "balanced"), **extra)
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
    return analyzer if ok else None


def _value_and_analyse(*, quiet: bool = False) -> bool:
    """
    Value the real portfolio at today's prices, then analyse the part of it that
    has a price history. The valuation is the platform's and the separate app's
    alike (`investment.holdings`); a line priced by hand is valued, named, and
    left out of the analysis with its money.
    """
    state = st.session_state
    quantities = {t: float(q) for t, q in (state.get("real_portfolio_holdings") or {}).items() if q and q > 0}
    base = state.get("base_currency", "USD")
    prices, report = latest_prices(list(quantities), base, manual=state.get("manual_prices") or {},
                                   on_error=lambda *_: None)
    valuation = H.value(quantities, prices)
    state["last_price_report"] = report
    state["real_portfolio_prices"] = prices
    state["pf_valuation"] = {"values": valuation.values, "total": valuation.total, "unpriced": list(valuation.unpriced),
                             "at": date.today().isoformat(), "base": base}
    state["current_portfolio"] = None
    if valuation.total <= 0:
        if not quiet:
            st.error("Aucune ligne n'a de prix : saisissez un prix à la main pour les lignes qu'aucun fournisseur ne couvre.")
        return False
    state["selected_tickers"] = list(valuation.weights)
    state["weights"] = dict(valuation.weights)
    state["real_portfolio_total_value"] = valuation.total
    state["analysis_mode"] = "real"
    analyzer = _analyse(list(valuation.weights), dict(valuation.weights), quiet=True, initial_value=valuation.total)
    if analyzer is None:
        state["unanalysed_holdings"] = dict(valuation.values)
        if not quiet:
            st.warning("Le portefeuille est valorisé, mais aucune ligne n'a d'historique de prix à analyser.")
        return False
    analysed, excluded = H.split_analysed(valuation.values, analyzer.tickers)
    if excluded and analysed > 0:
        analyzer.initial_value = analysed
        analyzer.portfolio_values = analysed * (1 + analyzer.portfolio_returns).cumprod()
    state["real_portfolio_total_value"] = analysed if excluded else valuation.total
    state["unanalysed_holdings"] = excluded
    return True


def _context():
    analyzer = st.session_state.get("current_portfolio")
    if analyzer is None:
        return None
    is_real = st.session_state.get("analysis_mode") == "real"
    return build_context(
        analyzer, lang="fr", profile=st.session_state.get("user_profile", "balanced"),
        period=st.session_state.get("sensitor_period", "MAX"), asset_info=assets.ASSET_INFO,
        sector_map=assets.SECTOR_MAPPING, geo_map=assets.GEOGRAPHY_MAPPING, is_real=is_real,
        current_value=st.session_state.get("real_portfolio_total_value") if is_real else None,
        currency=currency_symbol(getattr(analyzer, "base_currency", "USD")))


def _nav(page: str) -> None:
    with st.container(key="jnav_portfolio", horizontal=True):
        rt.link("Construire", BUILD, key="pfnav_build", kind="primary" if page == BUILD else "secondary")
        rt.link("Allocations types", MODELS, key="pfnav_models", kind="primary" if page == MODELS else "secondary")
        rt.link("Actifs", ASSETS, key="pfnav_assets", kind="primary" if page == ASSETS else "secondary")
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
                "En poids pour simuler une allocation, ou en quantités pour suivre son portefeuille réel au prix du "
                "jour ; puis lire la performance, le risque, la santé, les stress tests et la simulation, avec la "
                "marge « Lecture » de chaque écran.")
    _nav(BUILD)
    state = st.session_state
    analyzer = state.get("current_portfolio")
    if state.get("analysis_mode") == "real" and state.get("pf_valuation"):
        _wealth(state)
    elif analyzer is not None:
        _current(analyzer)
    if not email:
        notice("Sans compte", "L'analyse reste dans cette session et disparaît en fermant la page. Avec un compte, le "
               "portefeuille de travail est gardé, ici comme dans l'application complète.", "info")
    section(1, "Composer le portefeuille" if analyzer is None else "Modifier le portefeuille",
            "Les lignes, la devise et votre profil de risque. Les prix couvrent les deux dernières années.")
    modes = list(MODES)
    mode = st.radio("Mode", modes, format_func=MODES.get, horizontal=True, key="pf_mode",
                    index=modes.index(state.get("analysis_mode", "simulation"))
                    if state.get("analysis_mode") in modes else 0, label_visibility="collapsed")
    if mode == "real":
        _real_form(state)
    else:
        _form(state)
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


def _wealth(state) -> None:
    """The real portfolio at today's prices: each line, where its price comes from, its value and share."""
    v = state["pf_valuation"]
    report = state.get("last_price_report") or {}
    quantities = state.get("real_portfolio_holdings") or {}
    prices = state.get("real_portfolio_prices") or {}
    base, total = v["base"], v["total"]
    symbol = currency_symbol(base)
    excluded = state.get("unanalysed_holdings") or {}

    def source(t: str) -> str:
        if t in (report.get("manual") or {}):
            return f"saisi le {esc(_date(report['manual'][t]))}"
        if t in (report.get("converted") or {}):
            return f"cours converti en {esc(base)}"
        return "cours du marché"

    rows = "".join(
        f"<tr><td><b>{esc(t)}</b>{'' if _name(t) == t else ' · ' + esc(_name(t))}</td>"
        f"<td>{_num(quantities.get(t, 0), 4)}</td><td>{_num(prices.get(t, 0), 2)} {esc(symbol)}</td>"
        f"<td>{source(t)}{' · non analysé' if t in excluded else ''}</td>"
        f"<td>{_num(value, 0)} {esc(symbol)}</td><td>{value / total * 100:.1f} %</td></tr>"
        for t, value in sorted(v["values"].items(), key=lambda kv: -kv[1]))
    missing = list(v.get("unpriced") or []) + list((report.get("dropped") or {}).keys())
    analysed = state.get("real_portfolio_total_value")
    lines = [f"Valorisé le {esc(_date(v['at']))}, en {esc(base)}."]
    if excluded and analysed:
        lines.append(f"L'analyse couvre {_num(analysed, 0)} {esc(symbol)} : les lignes à prix saisi n'ont pas "
                     "d'historique, donc ni volatilité, ni corrélation, ni drawdown.")
    if missing:
        lines.append("Sans prix, donc hors du total : " + esc(", ".join(sorted(set(missing)))) + ".")
    html(f'<div class="sx-c-blank"><div class="rub">Portefeuille réel · {esc(base)} · profil '
         f'{esc(PROFILES.get(state.get("user_profile", "balanced"), ""))}</div>'
         f'<h3>{_num(total, 0)} {esc(symbol)} aujourd\'hui.</h3>'
         f'<div style="overflow-x:auto"><table><thead><tr><th>Ligne</th><th>Quantité</th><th>Prix</th><th>Source</th>'
         f'<th>Valeur</th><th>Part</th></tr></thead><tbody>{rows}</tbody></table></div>'
         f'<ul class="sx-c-facts">{"".join(f"<li>{x}</li>" for x in lines)}</ul></div>')
    if state.get("current_portfolio") is not None:
        rt.link("Lire la vue d'ensemble", "pf_overview", key="pf_go_overview", kind="primary")


def _num(value: float, decimals: int) -> str:
    text = f"{value:,.{decimals}f}".replace(",", "\u202f").replace(".", ",")
    return text.rstrip("0").rstrip(",") if decimals > 2 and "," in text else text


def _date(stamp) -> str:
    try:
        day = date.fromisoformat(str(stamp)[:10])
    except ValueError:
        return str(stamp or "")
    months = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
              "novembre", "décembre")
    return f"{day.day} {months[day.month - 1]} {day.year}"


def _custom_symbol(text: str) -> str:
    """A line outside the library: upper-case letters, digits and . - _ only, as the separate app accepts it."""
    symbol = "".join(c for c in (text or "").strip().upper().replace(" ", "-") if c.isalnum() or c in ".-_")
    return symbol[:MAX_CUSTOM]


def _real_form(state) -> None:
    holdings = dict(state.get("real_portfolio_holdings") or {})
    manual = dict(state.get("manual_prices") or {})
    with st.container(key="panel_pf_real"):
        if holdings:
            html('<div class="sx-kicker">Vos lignes</div>')
            for ticker in list(holdings):
                c1, c2, c3 = st.columns([3, 2, 1], vertical_alignment="bottom")
                with c1:
                    html(f'<p class="sx-body"><b>{esc(ticker)}</b>'
                         f'{"" if _name(ticker) == ticker else " · " + esc(_name(ticker))}</p>')
                with c2:
                    holdings[ticker] = st.number_input("Quantité", min_value=0.0, value=float(holdings[ticker]),
                                                       step=0.1, format="%.4f", key=f"pf_q_{ticker}")
                with c3:
                    if st.button("Retirer", key=f"pf_rm_{ticker}", type="tertiary"):
                        holdings.pop(ticker)
                        manual.pop(ticker, None)
                        state["real_portfolio_holdings"] = holdings
                        state["manual_prices"] = manual
                        st.rerun()
        else:
            note("Aucune ligne pour l'instant : ajoutez-en une depuis la bibliothèque, ou une ligne hors bibliothèque.")
        a1, a2, a3 = st.columns([3, 2, 1], vertical_alignment="bottom")
        with a1:
            pick = st.selectbox("Ajouter une ligne de la bibliothèque", sorted(assets.ASSET_INFO), index=None,
                                format_func=lambda t: f"{t} · {_name(t)}", key="pf_add_pick",
                                placeholder="Chercher une action, un ETF, une cryptomonnaie")
        with a2:
            qty = st.number_input("Quantité", min_value=0.0001, value=1.0, step=0.1, format="%.4f", key="pf_add_qty")
        with a3:
            if st.button("Ajouter", key="pf_add", disabled=pick is None):
                holdings[pick] = holdings.get(pick, 0.0) + float(qty)
                state["real_portfolio_holdings"] = holdings
                st.rerun()
        b1, b2 = st.columns([4, 1], vertical_alignment="bottom")
        with b1:
            custom = st.text_input("Ou une ligne hors bibliothèque (un symbole, ou un nom court : APPARTEMENT, "
                                   "ASSURANCE-VIE)", key="pf_add_custom", max_chars=40)
        with b2:
            if st.button("Ajouter", key="pf_add_custom_btn", disabled=not _custom_symbol(custom)):
                symbol = _custom_symbol(custom)
                holdings[symbol] = holdings.get(symbol, 0.0) + 1.0
                state["real_portfolio_holdings"] = holdings
                st.rerun()
        state["real_portfolio_holdings"] = holdings

        if holdings:
            report = state.get("last_price_report") or {}
            unpriced = set(report.get("missing") or []) & set(holdings)
            with st.expander("Prix saisis à la main", expanded=bool(unpriced)):
                html('<p class="sx-note">Pour une ligne qu\'aucun fournisseur ne couvre : une action non cotée, un '
                     'bien immobilier, un contrat. Un prix saisi n\'est utilisé que si aucun cours n\'existe, et '
                     'reste signalé comme votre estimation. Laissez zéro pour le retirer.</p>')
                if unpriced:
                    notice("Sans prix", "Aucun cours trouvé pour " + ", ".join(sorted(unpriced))
                           + " : saisissez un prix, sinon la ligne reste hors du total.", "info")
                for ticker in holdings:
                    entry = manual.get(ticker) or {}
                    m1, m2, m3 = st.columns([2, 2, 2], vertical_alignment="bottom")
                    with m1:
                        html(f'<p class="sx-body"><b>{esc(ticker)}</b></p>')
                    with m2:
                        price = st.number_input("Prix unitaire", min_value=0.0, value=float(entry.get("price") or 0.0),
                                                step=0.01, format="%.2f", key=f"pf_mp_{ticker}")
                    with m3:
                        options = list(BASE_CURRENCIES)
                        cur = str(entry.get("currency") or state.get("base_currency", "USD")).upper()
                        currency = st.selectbox("Devise", options, key=f"pf_mpc_{ticker}",
                                                index=options.index(cur) if cur in options else 0)
                    if price > 0:
                        new = {"price": float(price), "currency": currency,
                               "at": entry.get("at") if entry.get("price") == price and entry.get("currency") == currency
                               else date.today().isoformat()}
                        manual[ticker] = new
                    else:
                        manual.pop(ticker, None)
                state["manual_prices"] = {t: m for t, m in manual.items() if t in holdings}

        c1, c2 = st.columns(2)
        with c1:
            options = list(BASE_CURRENCIES)
            base = st.selectbox("Devise du portefeuille", options, key="pf_currency_real",
                                index=options.index(state.get("base_currency", "USD"))
                                if state.get("base_currency", "USD") in options else 0)
        with c2:
            keys = list(PROFILES)
            profile = st.selectbox("Profil de risque", keys, format_func=PROFILES.get, key="pf_profile_real",
                                   index=keys.index(state.get("user_profile", "balanced"))
                                   if state.get("user_profile", "balanced") in keys else 1)
        if st.button("Valoriser et analyser", type="primary", key="pf_value",
                     disabled=not any(q > 0 for q in holdings.values())):
            state["base_currency"] = base
            state["user_profile"] = profile
            if _value_and_analyse():
                rt.go("pf_overview")
                st.rerun()


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
        _reset_form(st.session_state)           # the form opens on the loaded allocation
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
        excluded = st.session_state.get("unanalysed_holdings") or {}
        if st.session_state.get("analysis_mode") == "real" and excluded:
            symbol = currency_symbol(st.session_state.get("base_currency", "USD"))
            notice("Lignes valorisées, non analysées",
                   f"Les chiffres ci-dessous ne couvrent que vos lignes cotées. {', '.join(sorted(excluded))} "
                   f"({_num(sum(excluded.values()), 0)} {symbol}) est valorisé mais pas analysé : un prix saisi à la "
                   "main n'a pas d'historique, donc ni volatilité, ni corrélation, ni drawdown. Votre patrimoine "
                   "complet est sur la page Construire.", "info")
        render(ctx)
        st.session_state["sensitor_period"] = ctx.period
        _hop(email)
        _persist(email)
        footer()
    renderer.__name__ = f"render_{page}"
    return renderer


# =============================================================================
# Model allocations
# =============================================================================

MODELS_NOTE = ("Des allocations types, construites pour l'étude : comparer une composition prudente, équilibrée ou "
               "dynamique, voir ce qu'elle porte et comment elle se comporte. Aucune n'est une recommandation adaptée à "
               "votre situation, et aucune ne promet un rendement : leurs chiffres sont ceux que l'analyse calcule sur "
               "les deux dernières années, une fois l'allocation chargée.")


def composition(allocation: dict[str, float]) -> list[tuple[str, float]]:
    """The share of each kind of asset, from the weights and the library's sectors, largest first."""
    shares: dict[str, float] = {}
    for ticker, weight in allocation.items():
        kind = KINDS.get((assets.ASSET_INFO.get(ticker) or {}).get("sector"), "actions")
        shares[kind] = shares.get(kind, 0.0) + float(weight)
    total = sum(shares.values()) or 1.0
    return sorted(((k, v / total) for k, v in shares.items()), key=lambda kv: (-kv[1], kv[0]))


def ordered_models() -> list[tuple[str, dict]]:
    order = {"safe": 0, "balanced": 1, "aggressive": 2}
    return sorted(assets.MODEL_PORTFOLIOS.items(), key=lambda kv: order.get(kv[1].get("profile"), 1))


def models_page(catalog, email, route) -> None:
    space = _space()
    _prepare(email)
    crumbs("Sensitor", space.label, "Allocations types")
    page_header(f"Espace {space.numeral} · {esc(space.label)}", "Des allocations types, <em>pour les étudier</em>.",
                f"{len(assets.MODEL_PORTFOLIOS)} compositions, de la plus prudente à la plus risquée. Chargez-en une "
                "pour la lire avec tous les écrans de l'espace, ou pour vous en servir de point de départ.")
    _nav(MODELS)
    notice("Pour l'étude, pas un conseil", MODELS_NOTE, "info")
    for index, (key, model) in enumerate(ordered_models(), start=1):
        allocation = model["allocation"]
        mix = " · ".join(f"{kind} {share * 100:.0f}\u202f%" for kind, share in composition(allocation))
        mix = mix[:1].upper() + mix[1:]
        rows = "".join(f"<tr><td><b>{esc(t)}</b></td><td>{esc(_name(t))}</td>"
                       f"<td>{esc(CLASSES.get((assets.ASSET_INFO.get(t) or {}).get('asset_class'), ''))}</td>"
                       f"<td>{w * 100:.0f}\u202f%</td></tr>"
                       for t, w in sorted(allocation.items(), key=lambda kv: (-kv[1], kv[0])))
        html(f'<div class="sx-c-blank sx-c-model"><div class="rub">Allocation {index:02d} · profil '
             f'{esc(PROFILES.get(model.get("profile"), ""))} · {len(allocation)} lignes</div>'
             f'<h3>{esc(MODEL_NAMES.get(key, key))}</h3><p>{esc(MODEL_TEXTS.get(key, ""))}</p>'
             f'<p class="sx-c-mix">{esc(mix)}</p>'
             f'<div class="sx-c-scroll"><table><thead><tr><th>Ligne</th><th>Nom</th><th>Classe</th><th>Poids</th>'
             f'</tr></thead><tbody>{rows}</tbody></table></div></div>')
        if st.button("Étudier cette allocation", key=f"pf_model_{index}"):
            state = st.session_state
            state["analysis_mode"] = "simulation"
            state["selected_tickers"] = list(allocation)
            state["weights"] = dict(allocation)
            state["user_profile"] = model.get("profile", "balanced")
            state["current_portfolio"] = None
            _reset_form(state)
            if _analyse(list(allocation), dict(allocation)):
                _persist(email)
                rt.go("pf_overview")
                st.rerun()
    _persist(email)
    footer()


def _reset_form(state) -> None:
    """Drop the building form's widget state, so it opens on the allocation just set."""
    for key in [k for k in state if str(k) == "pf_tickers" or str(k).startswith("pf_w_")]:
        del state[key]


# =============================================================================
# The asset library
# =============================================================================

def _liquidity(score) -> str:
    try:
        value = float(score)
    except (TypeError, ValueError):
        return ""
    return "très liquide" if value >= 90 else "liquide" if value >= 70 else "liquidité moyenne" if value >= 40 \
        else "peu liquide"


def where(info: dict) -> str:
    """Sector and geography in French, the geography left out when it only repeats the sector."""
    sector = SECTORS.get(info.get("sector"), info.get("sector", ""))
    place = GEOGRAPHIES.get(info.get("geography"), info.get("geography", ""))
    return " · ".join(x for x in dict.fromkeys([sector, place]) if x)


def _slug(ticker: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "_", ticker)


def search(query: str, kind: str = "") -> list[tuple[str, dict]]:
    """The library's assets matching a class and a text (symbol, name or sector), by name."""
    q = (query or "").strip().lower()
    return [(t, i) for t, i in sorted(assets.ASSET_INFO.items(), key=lambda kv: str(kv[1].get("name", kv[0])).lower())
            if (not kind or i.get("asset_class") == kind)
            and (not q or q in t.lower() or q in str(i.get("name", "")).lower()
                 or q in str(i.get("sector", "")).lower() or q in SECTORS.get(i.get("sector"), "").lower())]


def assets_page(catalog, email, route) -> None:
    space = _space()
    _prepare(email)
    crumbs("Sensitor", space.label, "Actifs")
    page_header(f"Espace {space.numeral} · {esc(space.label)}", "Connaître un actif <em>avant de le détenir</em>.",
                "Ce qu'il est, le rôle qu'on lui prête dans un portefeuille et le risque qu'il porte, pour les "
                f"{len(assets.ASSET_INFO)} actions, ETF et cryptomonnaies de la bibliothèque.")
    _nav(ASSETS)
    chosen = route.get("asset")
    info = assets.ASSET_INFO.get(chosen or "")
    if info:
        _asset_sheet(chosen, info, email)
    elif chosen:
        note(f"« {chosen} » n'est pas dans la bibliothèque.")
    c1, c2 = st.columns([2, 1])
    with c1:
        query = st.text_input("Chercher", key="pf_asset_q", placeholder="Un nom, un symbole, un secteur")
    with c2:
        classes = ["", *CLASSES]
        kind = st.selectbox("Classe", classes, key="pf_asset_class",
                            format_func=lambda c: "Toutes" if not c else CLASSES[c])
    listed = search(query, kind)
    total = len(assets.ASSET_INFO)
    html(f'<p class="sx-c-summary"><b>{len(listed)} actif{"s" if len(listed) > 1 else ""}</b>'
         f'{" sur " + str(total) if len(listed) != total else ""}.</p>')
    for ticker, i in listed:
        tap(f"pf_asset_{_slug(ticker)}",
            f'<div class="sx-c-space"><span class="n">{esc(CLASSES.get(i.get("asset_class"), "")[:1])}</span>'
            f'<span class="t">{esc(i.get("name", ticker))}</span><span class="s">{esc(ticker)} · {esc(where(i))}</span>'
            f'<span class="st sep">risque {esc(RISKS.get(i.get("risk_level"), "non renseigné"))}</span>'
            f'<span class="go">{icon("arrow")}</span></div>',
            f"Fiche de {i.get('name', ticker)}", ASSETS, asset=ticker)
    if not listed:
        note("Aucun actif ne correspond à cette recherche.")
    _persist(email)
    footer()


def _asset_sheet(ticker: str, info: dict, email) -> None:
    state = st.session_state
    kind = CLASSES.get(info.get("asset_class"), info.get("asset_class", ""))
    facts = [" · ".join(dict.fromkeys(x for x in [kind, *where(info).split(" · ")] if x)) + ".",
             f"Niveau de risque : {RISKS.get(info.get('risk_level'), 'non renseigné')}.",
             f"Liquidité : {_liquidity(info.get('liquidity')) or 'non renseignée'}."]
    sheet = asset_sheets.load().get(ticker)
    description = sheet.description if sheet else asset_sheets.plain(info.get("description_fr"))
    reading = ""
    if sheet:
        reading = (f'<div class="sx-kicker">Le rôle qu\'on lui prête</div><p>{esc(sheet.role)}</p>'
                   f'<div class="sx-kicker">Sa limite</div><p>{esc(sheet.limite)}</p>'
                   '<p class="sx-note">Une lecture, à confronter aux cours : ni une certitude, ni un conseil.</p>')
    html(f'<div class="sx-c-blank"><div class="rub">{esc(ticker)} · fiche de la bibliothèque</div>'
         f'<h3>{esc(info.get("name", ticker))}</h3><p>{esc(description)}</p>'
         f'<ul class="sx-c-facts">{"".join(f"<li>{esc(x)}</li>" for x in facts)}</ul>{reading}</div>')
    if info.get("asset_class") == "Crypto" or info.get("sector") in ("Crypto", "Cryptocurrency"):
        rt.link("Bitcoin, une réserve de valeur ? Le cours", "course", key=f"pf_asset_course_{_slug(ticker)}",
                course="bitcoin-reserve-de-valeur")
    real = state.get("analysis_mode") == "real"
    holdings = dict(state.get("real_portfolio_holdings") or {})
    tickers = [t for t in state.get("selected_tickers") or [] if t in assets.ASSET_INFO]
    if real:
        c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
        with c1:
            qty = st.number_input("Quantité détenue", min_value=0.0001, value=1.0, step=0.1, format="%.4f",
                                  key=f"pf_asset_qty_{_slug(ticker)}")
        with c2:
            add = st.button("Ajouter à mon portefeuille réel", key=f"pf_asset_add_{_slug(ticker)}", type="primary")
        if add:
            holdings[ticker] = holdings.get(ticker, 0.0) + float(qty)
            state["real_portfolio_holdings"] = holdings
            state["current_portfolio"] = None
            _persist(email)
            rt.go(BUILD)
            st.rerun()
        return
    allowed = core_config.tier_limits(state.get("user_tier", "free"))["max_assets"]
    if ticker in tickers:
        note("Cet actif est déjà dans votre portefeuille de travail.")
        return
    if len(tickers) >= allowed:
        note(f"Votre portefeuille de travail compte {len(tickers)} lignes ; un compte gratuit en compose {allowed} au "
             "plus. Retirez-en une sur la page Construire pour faire de la place.")
        return
    if st.button("Ajouter à mon portefeuille de travail", key=f"pf_asset_add_{_slug(ticker)}", type="primary"):
        # The new line takes an equal share; the others keep their proportions in the rest.
        saved = {t: float((state.get("weights") or {}).get(t, 0.0)) for t in tickers}
        total = sum(saved.values())
        share = 1 / (len(tickers) + 1)
        weights = {t: (w / total if total > 0 else 1 / len(tickers)) * (1 - share) for t, w in saved.items()}
        weights[ticker] = share
        state["selected_tickers"] = [*tickers, ticker]
        state["weights"] = weights
        state["current_portfolio"] = None
        _reset_form(state)
        _persist(email)
        rt.go(BUILD)
        st.rerun()


RENDERERS = {BUILD: build_page, MODELS: models_page, ASSETS: assets_page,
             **{page: _page(page, render) for page, _label, render in TABS}}
