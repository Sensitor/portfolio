"""
Sensitor — Streamlit entry point.

This file is the UI shell: page config, the stylesheet, session state, the
sidebar, routing, and the seven original product pages. Everything it computes
with now lives in the `sensitor` package — reference data in
`investment.assets`, the analyzer in `investment.portfolio`, configuration in
`core.config`, translations in `core.i18n` — so the business logic is reachable
from a test, a script or the future API with no Streamlit runtime present.

See docs/ARCHITECTURE.md for the full layout and the migration table.
"""

import os

import streamlit as st


def _mirror_secrets() -> None:
    """
    Copy `st.secrets` into the environment, before anything reads it.

    Streamlit Cloud has no way to set environment variables: a deployment is
    configured through the Secrets box, which lands in `st.secrets` and nowhere
    else. Every module below this one reads `os.getenv`, because they have to
    run from a test, a script and the API with no Streamlit present.

    So the two are bridged here, at the top of the only file that is allowed to
    know about both — and an existing environment variable always wins, so
    running locally with a real environment is never overridden by a secrets
    file that happens to be lying around.
    """
    known = (
        "SENSITOR_DB_URL", "SENSITOR_DB_PATH", "SENSITOR_AUTH",
        "SENSITOR_API_TOKEN", "SENSITOR_CORS_ORIGINS",
        "PRO_EMAILS", "SENSITOR_ADMIN_EMAILS",
    )
    try:
        available = st.secrets
    except Exception:                                    # noqa: BLE001
        return                                           # no secrets file, fine
    for key in known:
        try:
            if key in available and not os.getenv(key):
                os.environ[key] = str(available[key])
        except Exception:                                # noqa: BLE001
            continue


_mirror_secrets()

# yfinance is no longer imported here. The last direct download in this file
# was the real-portfolio valuation, which now goes through
# `investment.portfolio.latest_prices` so the prices arrive already in one
# currency. The UI layer fetching its own market data is how the currency
# rule got bypassed in the first place.
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ── Sensitor package ─────────────────────────────────────────────────────────
# Engine, design system, visual components and the twelve Intelligence and
# Workspace pages. Nothing below this line computes anything the package cannot.
from sensitor.core import permissions as P
from sensitor.core.i18n import LEGACY_STRINGS, na
from sensitor.investment import assets
from sensitor.investment.currency import BASE_CURRENCIES, currency_symbol, mixed_currencies
from sensitor.investment.portfolio import UltimatePortfolioAnalyzer
from sensitor.pages import _workspace
from sensitor.ui import themes as sensitor_design
from sensitor.investment.context import build_context
from sensitor.platform.brand import mark_svg as _mark_svg
from sensitor.core.i18n import tr as s_tr
from sensitor.pages import (
    render_advisor, render_copilot, render_health, render_optimize, render_overview,
    render_performance, render_portfolios, render_reports, render_risk,
    render_simulator, render_stress, render_xray,
    render_trading_analytics, render_trading_journal, render_trading_overview,
    render_trading_psychology, render_trading_risk,
)

# =============================================================================
# ACCESS CONFIGURATION
# =============================================================================

# Configuration lives in sensitor.core.config and access in core.permissions.
# There is no payment link: no paid plan exists until a regulatory review has
# been done (CLAUDE.md).


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Sensitor",
    page_icon=_mark_svg(64, uid="favicon"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS: the « Carnet de bord » direction, from sensitor/ui/themes.py
# =============================================================================
#
# The first-generation pages keep their own classes (score, KPI, asset, model,
# recommendation cards); `inject_legacy` styles them with the same tokens. The
# widgets, the sidebar and the page are styled once, by `inject_theme`.

sensitor_design.inject_legacy()

sensitor_design.inject_theme()

# =============================================================================
# DATA: ASSET INFO, MODEL PORTFOLIOS, SECTORS
# =============================================================================

# Instrument reference data lives in sensitor.investment.assets; the three
# maps the analysis context reads are bound here (tests/visual_preview.py too).
ASSET_INFO = assets.ASSET_INFO
SECTOR_MAPPING = assets.SECTOR_MAPPING
GEOGRAPHY_MAPPING = assets.GEOGRAPHY_MAPPING


# =============================================================================
# SESSION STATE WITH AUTO-REBALANCE
# =============================================================================

def resolve_tier(email: str) -> str:
    """
    The member's level, from their active entitlements: the same answer the
    platform gets (`core.permissions`). `PRO_EMAILS` is turned into an
    entitlement at sign-in (`core.auth`), so it is not read here.
    """
    from sensitor.pages._shared import get_store
    store = get_store()
    return store.access(email).level if store is not None and email else P.FREE





# Pages the Sensitor platform may open directly with `?page=` (its « Portefeuille
# et risque » and « Journal de trading » spaces). Read once, when the session
# starts; any other value is ignored and the app opens as before.
DEEP_LINK_PAGES = {"overview", "trading_overview", "trading_journal"}

# The analyzer's first screens, retired once the platform carried them
# (docs/FUSION_ANALYSEUR.md): each old page name, and where it lives now. A
# bookmark, a saved state or a « Load » from the saved portfolios lands on a
# card that says so, with the link, rather than on a blank page.
MOVED_PAGES = {
    "dashboard": ("pf_overview", "Vue d'ensemble", "Overview"),
    "new_analysis": ("portfolio", "Construire", "Build"),
    "models": ("pf_models", "Allocations types", "Model allocations"),
    "real_portfolio": ("portfolio", "Construire, portefeuille réel", "Build, real portfolio"),
    "improve": ("pf_optimize", "Optimiser", "Optimise"),
    "library": ("pf_assets", "Bibliothèque d'actifs", "Asset library"),
}


def _moved_page(page: str, lang: str) -> None:
    """Where a retired page lives now: the platform, with a link when its address is set."""
    target, label_fr, label_en = MOVED_PAGES.get(page, ("portfolio", "Portefeuille et risque", "Portfolio and risk"))
    platform = os.getenv("SENSITOR_PUBLIC_URL", "").strip().rstrip("/")
    st.title(label_en if lang == "en" else label_fr)
    st.info(
        f"This screen now lives in the Sensitor platform, « Portefeuille et risque » space, page « {label_fr} ». "
        "Your working portfolio is the same there: it is saved to your account."
        if lang == "en" else
        f"Cet écran est désormais dans la plateforme Sensitor, espace « Portefeuille et risque », page "
        f"« {label_fr} ». Votre portefeuille de travail y est le même : il est enregistré sur votre compte."
    )
    if platform:
        st.link_button("Open it in the platform" if lang == "en" else "L'ouvrir dans la plateforme",
                       f"{platform}/?page={target}", type="primary")
    if st.button("Back to the overview" if lang == "en" else "Revenir à la vue d'ensemble", key="moved_back"):
        st.session_state.page = "overview"
        st.rerun()


def _requested_page() -> str | None:
    try:
        page = st.query_params.get("page")
    except Exception:
        return None
    return page if page in DEEP_LINK_PAGES else None


def init_session_state():
    defaults = {
        'authenticated': False,
        'user_email': "",
        # The session token is the only thing that makes `user_email` true.
        # `current_user_email()` resolves this against the store on every rerun
        # and clears both when it no longer resolves.
        'session_token': "",
        'user_tier': 'free',
        'current_portfolio': None,
        'page': _requested_page() or "overview",
        'language': "en",
        'selected_tickers': [],
        'weights': {},
        'user_profile': "balanced",
        'analysis_mode': "simulation",       # "simulation" or "real"
        # What the portfolio is denominated in. Every price is converted into it
        # before a return is computed, so a book holding LVMH and Apple reports
        # what one investor actually earned rather than two currencies added
        # together. See sensitor/investment/currency.py.
        'base_currency': "USD",
        'real_portfolio_holdings': {},        # {ticker: quantity}
        'real_portfolio_total_value': None,   # float: computed after price fetch
        'real_portfolio_prices': {},          # {ticker: current_price}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# =============================================================================
# TRANSLATIONS
# =============================================================================

# The legacy translation dictionary moved to sensitor.core.i18n alongside the
# Sensitor one. Same content, same lookups.
T = LEGACY_STRINGS



def t(key, lang="en"):
    return T.get(lang, T["en"]).get(key, key)

# =============================================================================
# ADVANCED PORTFOLIO ANALYZER
# =============================================================================

# The analyzer moved to sensitor.investment.portfolio, where it no longer needs
# a Streamlit runtime: fetch_data() reports through callbacks instead of calling
# st.progress and st.warning. _fetch_with_progress() below supplies the
# Streamlit-backed callbacks so the pages behave exactly as before.


# =============================================================================
# UI COMPONENTS
# =============================================================================

# =============================================================================
# MAIN APP
# =============================================================================

def _fetch_with_progress(analyzer):
    """
    Run the analyzer's download behind a Streamlit progress bar.

    The analyzer no longer knows about Streamlit; this supplies the callbacks so
    the user still sees the loading bar and the per-ticker warnings that the
    original inline version produced.
    """
    bar = st.progress(0)
    status = st.empty()

    def _progress(fraction, label):
        status.text(label)
        bar.progress(min(max(fraction, 0.0), 1.0))

    def _on_error(ticker, message):
        st.warning(f"{ticker}: {message}")

    try:
        return analyzer.fetch_data(progress=_progress, on_error=_on_error)
    finally:
        status.empty()
        bar.empty()


def _base_currency() -> str:
    return st.session_state.get("base_currency", "USD")


def _new_analyzer(tickers, weights, **kwargs):
    """
    Build an analyzer over the last two years, in the chosen base currency.

    One constructor for all four call sites. Before this there were four, and
    adding the currency argument to three of them would have left the fourth
    silently computing a portfolio in mixed money.
    """
    return UltimatePortfolioAnalyzer(
        tickers,
        weights,
        (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
        base_currency=_base_currency(),
        **kwargs,
    )


def _unanalysed_notice(lang) -> None:
    """
    Name the money the analysis does not cover.

    A holding priced by hand has a value today and no history, so it cannot
    have a volatility, a correlation or a drawdown — the analyzer drops it and
    every figure on every page is about what is left. Which is correct, and
    invisible unless it is said: a net worth of 68k and a risk report about 55k
    of it, with nothing on screen accounting for the difference, is a page that
    is quietly answering a different question than the one asked.
    """
    excluded = st.session_state.get("unanalysed_holdings") or {}
    if not excluded:
        return
    symbol = currency_symbol(_base_currency())
    total = sum(excluded.values())
    names = ", ".join(sorted(excluded))
    st.info(
        f"The figures below cover your traded holdings only. {names} "
        f"({symbol}{total:,.0f}) is valued but not analysed: a hand-entered "
        f"price has no history, so it has no volatility, correlation or "
        f"drawdown to report. Your total wealth is on the Real Portfolio page."
        if lang == "en" else
        f"Les chiffres ci-dessous ne couvrent que vos lignes cotées. {names} "
        f"({symbol}{total:,.0f}) est valorisé mais pas analysé : un prix saisi "
        f"à la main n'a pas d'historique, donc ni volatilité, ni corrélation, "
        f"ni drawdown. Votre patrimoine total est sur la page Portefeuille réel."
    )


def _currency_notice(analyzer, lang, *, verbose=False):
    """
    The one currency message that belongs above every page.

    An asset dropped for want of an exchange rate changes every figure on every
    page, so it is repeated on all of them. The conversion captions are not
    repeated — `pages/_shared.currency_notice` renders those once, under the
    overview's own header.

    `verbose` is accepted and ignored, so a caller that asks for the captions
    gets the error rather than a crash.
    """
    report = getattr(analyzer, "currency_report", None) or {}
    base = getattr(analyzer, "base_currency", "USD")
    dropped = report.get("dropped") or {}
    if not dropped:
        return

    names = ", ".join(sorted(dropped))
    st.error(
        f"Removed from the portfolio: no exchange rate against {base} could be "
        f"loaded for {names}. They are excluded rather than added in their own "
        f"currency, which would make every figure below meaningless."
        if lang == "en" else
        f"Retiré du portefeuille : aucun taux de change contre {base} n'a pu être "
        f"chargé pour {names}. Ces lignes sont exclues plutôt qu'ajoutées dans leur "
        f"propre devise, ce qui rendrait tous les chiffres ci-dessous dénués de sens."
    )


def _sidebar(lang):
    """Render sidebar navigation and user info."""
    with st.sidebar:
        # The same lockup as the platform's sidebar: the mark, the name, the space.
        space_name = "Portfolio and risk" if lang == "en" else "Portefeuille et risque"
        st.markdown(
            "<div style='display:flex;align-items:center;gap:.8rem;margin:0 0 20px 0;'>"
            f"{_mark_svg(38, uid='side')}<div>"
            "<div style='font:700 16px \'Schibsted Grotesk\',sans-serif;letter-spacing:.24em;"
            "color:#FFFDF8;'>SENSITOR</div>"
            "<div style='font-size:0.62rem;color:rgba(255,253,248,0.6);letter-spacing:0.09em;"
            f"text-transform:uppercase;margin-top:3px;'>{space_name}</div></div></div>",
            unsafe_allow_html=True
        )

        # The platform now carries these screens (docs/FUSION_ANALYSEUR.md): say so, with the link.
        platform = os.getenv("SENSITOR_PUBLIC_URL", "").strip().rstrip("/")
        if platform:
            label = ("These screens now live in the Sensitor platform, with the Academy and the journal."
                     if lang == "en" else
                     "Ces écrans sont désormais dans la plateforme Sensitor, avec l'Academy et le journal.")
            st.markdown(f"<div style='font-size:0.78rem;color:rgba(255,253,248,0.75);margin-bottom:6px;'>{label}</div>",
                        unsafe_allow_html=True)
            st.link_button("Open the platform" if lang == "en" else "Ouvrir la plateforme",
                           f"{platform}/?page=portfolio", use_container_width=True)

        # Language toggle
        c1, c2 = st.columns(2)
        with c1:
            if st.button("EN", use_container_width=True,
                         type="primary" if lang == "en" else "secondary"):
                st.session_state.language = "en"
                st.rerun()
        with c2:
            if st.button("FR", use_container_width=True,
                         type="primary" if lang == "fr" else "secondary"):
                st.session_state.language = "fr"
                st.rerun()

        st.markdown("<hr style='border-color:rgba(15,27,38,0.08);margin:16px 0;'>",
                    unsafe_allow_html=True)

        # Risk profile — translated labels
        profile_options = ["safe", "balanced", "aggressive"]
        profile_labels = [t("profile_safe", lang), t("profile_balanced", lang), t("profile_aggressive", lang)]
        current_idx = profile_options.index(st.session_state.user_profile)
        selected_label = st.selectbox(
            t("profile_label", lang),
            profile_labels,
            index=current_idx,
        )
        st.session_state.user_profile = profile_options[profile_labels.index(selected_label)]

        st.markdown("<hr style='border-color:rgba(15,27,38,0.06);margin:14px 0;'>",
                    unsafe_allow_html=True)

        # Analysis mode selector
        mode_options = ["simulation", "real"]
        mode_labels = [t("mode_simulation", lang), t("mode_real", lang)]
        current_mode_idx = mode_options.index(st.session_state.analysis_mode)
        mode_label = "Analysis Mode" if lang == 'en' else "Mode d'Analyse"
        selected_mode_label = st.selectbox(
            mode_label,
            mode_labels,
            index=current_mode_idx,
        )
        new_mode = mode_options[mode_labels.index(selected_mode_label)]
        if new_mode != st.session_state.analysis_mode:
            st.session_state.analysis_mode = new_mode
            st.session_state.page = "overview"
            st.rerun()

        # ── Base currency ────────────────────────────────────────────────────
        # Not a display preference. Prices are converted into this before any
        # return is computed, so changing it changes the numbers — a euro
        # investor holding US assets earned something different from a dollar
        # investor holding the same ones. The analysis is dropped on a change
        # rather than relabelled, because relabelling would put a euro sign in
        # front of a dollar return.
        currency_label = "Portfolio currency" if lang == 'en' else "Devise du portefeuille"
        current_base = st.session_state.get("base_currency", "USD")
        base_options = list(BASE_CURRENCIES)
        new_base = st.selectbox(
            currency_label,
            base_options,
            index=base_options.index(current_base) if current_base in base_options else 0,
            format_func=lambda code: f"{code} · {currency_symbol(code).strip() or code}",
        )
        if new_base != current_base:
            st.session_state.base_currency = new_base
            st.session_state.current_portfolio = None
            st.rerun()

        held = mixed_currencies(st.session_state.get("selected_tickers") or [],
                                assets.QUOTE_CURRENCY)
        if len(held) > 1:
            others = ", ".join(c for c in held if c != new_base)
            st.caption(
                f"Converted from {others} at the daily rate."
                if lang == 'en' else
                f"Converti depuis {others} au taux du jour."
            )

        st.markdown("<hr style='border-color:rgba(15,27,38,0.06);margin:14px 0;'>",
                    unsafe_allow_html=True)

        # ── Navigation ───────────────────────────────────────────────────────
        # Two products under one roof. The headings say which analytics a page
        # belongs to, because "Risk" means portfolio volatility on one side and
        # position sizing on the other — the same word for two different things.
        # The build/model/legacy tools keep their own heading so nothing that
        # existed before the restructure is lost.
        intelligence = [
            ("overview",    s_tr("nav_overview", lang)),
            ("performance", s_tr("nav_performance", lang)),
            ("health",      s_tr("nav_health", lang)),
            ("xray",        s_tr("nav_xray", lang)),
            ("risk",        s_tr("nav_risk", lang)),
            ("stress",      s_tr("nav_stress", lang)),
            ("optimize",    s_tr("nav_optimize", lang)),
            ("simulator",   s_tr("nav_simulator", lang)),
            ("copilot",     s_tr("nav_copilot", lang)),
        ]
        trading = [
            ("trading_overview",   s_tr("nav_trading_overview", lang)),
            ("trading_journal",    s_tr("nav_trading_journal", lang)),
            ("trading_analytics",  s_tr("nav_trading_analytics", lang)),
            ("trading_risk",       s_tr("nav_trading_risk", lang)),
            ("trading_psychology", s_tr("nav_trading_psychology", lang)),
        ]
        workspace = [
            ("portfolios", s_tr("nav_portfolios", lang)),
            ("reports",    s_tr("nav_reports", lang)),
            ("advisor",    s_tr("nav_advisor", lang)),
        ]
        # Building a portfolio, the model allocations, the asset library and the
        # real portfolio's entry moved to the platform (docs/FUSION_ANALYSEUR.md).
        tools = [("account", t("account", lang))]

        def _nav_group(title, entries):
            st.markdown(
                f"<div style='font-size:0.63rem;font-weight:700;letter-spacing:0.15em;"
                f"text-transform:uppercase;color:rgba(255,253,248,0.55);margin:6px 0 6px 4px;'>{title}</div>",
                unsafe_allow_html=True,
            )
            for key, label in entries:
                btn_type = "primary" if st.session_state.page == key else "secondary"
                if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
                    st.session_state.page = key
                    st.rerun()

        _nav_group(s_tr("nav_investment", lang), intelligence)
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        _nav_group(s_tr("nav_trading", lang), trading)
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        _nav_group("Workspace" if lang == "en" else "Espace de travail", workspace)
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        _nav_group("Build" if lang == "en" else "Construire", tools)

        st.markdown("<hr style='border-color:rgba(15,27,38,0.08);margin:16px 0;'>",
                    unsafe_allow_html=True)

        # Tier badge
        tier = st.session_state.user_tier
        tier_label = P.LEVEL_LABELS[P.level_of(tier)]
        email_display = st.session_state.user_email or ("Demo mode" if lang == 'en' else "Mode démo")
        st.markdown(
            f"<div style='font-size:0.78rem;color:rgba(255,253,248,0.6);margin-bottom:4px;'>{email_display}</div>"
            f"<div style='display:inline-block;border:1px solid rgba(255,253,248,0.35);color:#FFFDF8;"
            f"padding:2px 12px;border-radius:3px;font-size:0.72rem;font-weight:600;"
            f"letter-spacing:0.06em;text-transform:uppercase;'>{tier_label}</div>",
            unsafe_allow_html=True
        )
        if not P.is_premium(tier):
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("Premium access" if lang == 'en' else "Accès Premium",
                         use_container_width=True):
                st.session_state.page = "account"
                st.rerun()


SENSITOR_PAGES = {
    "overview": render_overview,
    "performance": render_performance,
    "health": render_health,
    "xray": render_xray,
    "risk": render_risk,
    "stress": render_stress,
    "optimize": render_optimize,
    "simulator": render_simulator,
    "copilot": render_copilot,
    "portfolios": render_portfolios,
    "reports": render_reports,
    "advisor": render_advisor,
}

# The trading pages take no investment context — they build their own from the
# journal. Kept in a separate map so `main()` does not have to construct an
# analysis context for a page that has no use for one.
TRADING_PAGES = {
    "trading_overview": render_trading_overview,
    "trading_journal": render_trading_journal,
    "trading_analytics": render_trading_analytics,
    "trading_risk": render_trading_risk,
    "trading_psychology": render_trading_psychology,
}


def _sensitor_context(lang):
    """
    Build the shared analysis context for the Sensitor pages.

    Wraps the existing analyzer rather than replacing it, so every Sensitor page
    reads the same returns the legacy engine computed. Returns None when no
    portfolio is loaded; the pages render their own empty state in that case.
    """
    analyzer = st.session_state.current_portfolio
    if analyzer is None:
        return None

    is_real = st.session_state.analysis_mode == "real"
    real_value = st.session_state.get("real_portfolio_total_value") if is_real else None

    return build_context(
        analyzer,
        lang=lang,
        profile=st.session_state.user_profile,
        period=st.session_state.get("sensitor_period", "MAX"),
        asset_info=ASSET_INFO,
        sector_map=SECTOR_MAPPING,
        geo_map=GEOGRAPHY_MAPPING,
        is_real=is_real,
        current_value=real_value,
        # The symbol every figure on every Sensitor page is printed with. Read
        # from the analyzer, not from the session: the analyzer is what actually
        # converted the prices, so if the two ever disagree the money on screen
        # follows the money in the maths.
        currency=currency_symbol(getattr(analyzer, "base_currency", "USD")),
    )


def _account_page(lang, tier):
    """
    Sign in, sign out, and say how this deployment protects the data.

    The identity is issued by `core.auth`, never taken from the text box. Both
    modes go through the same call, so the session plumbing multi-user depends
    on is the plumbing that runs on every single-user sign-in too.
    """
    from sensitor.pages._shared import get_auth

    st.title("Your Account" if lang == "en" else "Votre Compte")

    auth = get_auth()
    if auth is None:
        st.warning(s_tr("storage_note", lang))
        return

    mode = auth.describe_mode(lang)
    email = _signed_in_email()

    # The mode is stated, not assumed. An access-control mode nobody can see is
    # how a deployment ends up open with a text box for a login.
    st.info(s_tr(mode["key"], lang))

    if email:
        st.success(f"{s_tr('signed_in_as', lang)} **{email}** · "
                   f"{P.LEVEL_LABELS[P.level_of(tier)]}")
        cols = st.columns([1, 1, 3])
        with cols[0]:
            if st.button(s_tr("sign_out", lang), key="acct_out"):
                auth.sign_out(st.session_state.get("session_token"))
                _clear_session()
                st.rerun()
        with cols[1]:
            if auth.multi_user and st.button(s_tr("sign_out_all", lang),
                                             key="acct_out_all"):
                auth.sign_out_everywhere(email)
                _clear_session()
                st.rerun()

        if auth.multi_user:
            _change_password(auth, email, lang)
        _storage_location(lang)
        return

    if auth.multi_user:
        _multi_user_sign_in(auth, lang)
    else:
        _single_user_sign_in(auth, lang)


def _storage_location(lang):
    """
    Where the data actually is.

    Stated because "does my portfolio survive a reboot" has a file path for an
    answer, and the default path is relative to whatever directory the app was
    launched from — so running `streamlit run` from two places gives two
    databases and one of them looks empty. Somebody who can see the path can
    tell which one they are looking at.
    """
    from sensitor.database import postgres as pg
    from sensitor.database.connection import describe, target

    where = target()
    durable = pg.is_url(where)
    # Streamlit Cloud mounts the repository under /mount/src and gives the
    # container no persistent disk. Detecting it is what turns a general
    # warning nobody reads into a specific one about this deployment.
    ephemeral_host = os.path.abspath(".").startswith("/mount/src")

    with st.expander("Data & storage" if lang == "en" else "Données et stockage"):
        st.caption(f"**{describe(where)}**")

        if durable:
            st.success(
                "Stored in PostgreSQL. Your data survives restarts, redeploys and "
                "sleeps, and is reachable from any device."
                if lang == "en" else
                "Stocké dans PostgreSQL. Vos données survivent aux redémarrages, aux "
                "redéploiements et aux mises en veille, et sont accessibles depuis "
                "n'importe quel appareil."
            )
        elif ephemeral_host:
            st.error(
                "**This data will be lost.** You are running on a host with no "
                "persistent disk, so this SQLite file is deleted on every restart, "
                "redeploy and sleep. Create a free PostgreSQL database and put its "
                "URL in `SENSITOR_DB_URL`: see docs/DEPLOY.md."
                if lang == "en" else
                "**Ces données seront perdues.** Vous tournez sur un hébergeur sans "
                "disque persistant: ce fichier SQLite est supprimé à chaque "
                "redémarrage, redéploiement et mise en veille. Créez une base "
                "PostgreSQL gratuite et mettez son URL dans `SENSITOR_DB_URL` : "
                "voir docs/DEPLOY.md."
            )
        else:
            size = (f"{os.path.getsize(where) / 1024:.0f} KB"
                    if os.path.exists(where) else na(lang))
            st.caption(f"{size}")
            if not os.getenv("SENSITOR_DB_PATH") and not os.getenv("SENSITOR_DB_URL"):
                st.warning(
                    "Neither SENSITOR_DB_URL nor SENSITOR_DB_PATH is set, so this "
                    "path depends on the directory the app was started from. "
                    "Launching from somewhere else opens a different, empty database."
                    if lang == "en" else
                    "Ni SENSITOR_DB_URL ni SENSITOR_DB_PATH n'est défini: ce chemin "
                    "dépend du dossier depuis lequel l'app a été lancée. Un lancement "
                    "depuis un autre dossier ouvre une autre base, vide."
                )

        st.caption(
            "Your trades, your saved portfolios and the portfolio you are currently "
            "working on all live here. Nothing in this app sends them anywhere else."
            if lang == "en" else
            "Vos trades, vos portefeuilles enregistrés et le portefeuille en cours "
            "vivent tous ici. Rien dans cette application ne les envoie ailleurs."
        )


def _signed_in_email() -> str:
    from sensitor.pages._shared import current_user_email
    return current_user_email()


def _clear_session():
    st.session_state.session_token = ""
    st.session_state.user_email = ""
    st.session_state.authenticated = False
    st.session_state.user_tier = P.FREE
    # The allocation on screen belongs to whoever just signed out. Their row
    # stays in the database and comes back when they return; what is dropped
    # here is the copy in memory, so the next person to use this browser does
    # not inherit a portfolio that is not theirs.
    _workspace.forget()


def _apply(result, lang):
    """Put a successful sign-in into session state."""
    st.session_state.session_token = result.token
    st.session_state.user_email = result.email
    st.session_state.user_tier = resolve_tier(result.email)
    st.session_state.authenticated = True


def _auth_error(result, lang):
    message = s_tr(f"auth_{result.reason}", lang)
    st.error(f"{message} {result.detail}" if result.detail else message)


def _single_user_sign_in(auth, lang):
    st.markdown(s_tr("single_user_intro", lang))
    email_input = st.text_input("Email", placeholder="you@example.com",
                                label_visibility="collapsed", key="acct_email")
    if st.button("Continue" if lang == "en" else "Continuer",
                 type="primary", key="acct_continue"):
        result = auth.sign_in(email_input)
        if result:
            _apply(result, lang)
            st.rerun()
        else:
            _auth_error(result, lang)


def _multi_user_sign_in(auth, lang):
    sign_in_tab, sign_up_tab = st.tabs(
        [s_tr("sign_in", lang), s_tr("create_account", lang)])

    with sign_in_tab:
        with st.form("acct_signin"):
            email_input = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input(s_tr("mt5_password", lang), type="password")
            if st.form_submit_button(s_tr("sign_in", lang), type="primary"):
                result = auth.sign_in(email_input, password)
                if result:
                    _apply(result, lang)
                    st.rerun()
                else:
                    _auth_error(result, lang)

    with sign_up_tab:
        with st.form("acct_signup"):
            email_input = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input(s_tr("choose_password", lang), type="password")
            again = st.text_input(s_tr("repeat_password", lang), type="password")
            if st.form_submit_button(s_tr("create_account", lang), type="primary"):
                if password != again:
                    st.error(s_tr("auth_passwords_differ", lang))
                else:
                    result = auth.sign_up(email_input, password)
                    if result:
                        _apply(result, lang)
                        st.rerun()
                    else:
                        _auth_error(result, lang)


def _change_password(auth, email, lang):
    with st.expander(s_tr("change_password", lang)):
        with st.form("acct_password"):
            current = st.text_input(s_tr("current_password", lang), type="password")
            new = st.text_input(s_tr("choose_password", lang), type="password")
            again = st.text_input(s_tr("repeat_password", lang), type="password")
            if st.form_submit_button(s_tr("change_password", lang), type="primary"):
                if new != again:
                    st.error(s_tr("auth_passwords_differ", lang))
                    return
                result = auth.change_password(email, current, new)
                if result:
                    _apply(result, lang)
                    st.success(s_tr("password_changed", lang))
                    st.rerun()
                else:
                    _auth_error(result, lang)


def _workspace_store_and_user():
    """The store and the verified address, or (None, "") when nobody is signed in."""
    from sensitor.pages._shared import current_user_email, get_store
    store = get_store()
    if store is None:
        return None, ""
    return store, current_user_email()


def _restore_workspace(lang):
    """
    Put back the portfolio this person was last working on, and price it.

    The allocation comes out of SQLite; the prices do not. Re-fetching them is
    not a shortcut avoided — it is the point: a portfolio restored from a row
    written last month should be valued at today's market, not at the market as
    it was before the reboot.

    A failure here is reported and then dropped. The allocation is still on
    screen and the Analyse button still works, which is a better outcome than an
    app that will not open because a ticker was delisted while it was closed.
    """
    store, email = _workspace_store_and_user()
    _workspace.restore(store, email)

    if not _workspace.take_resume_flag():
        return
    tickers = st.session_state.get("selected_tickers") or []
    if not tickers or st.session_state.current_portfolio is not None:
        return

    with st.spinner(t("loading", lang)):
        analyzer = _new_analyzer(
            list(tickers),
            dict(st.session_state.weights),
            user_profile=st.session_state.user_profile,
        )
        if _fetch_with_progress(analyzer):
            st.session_state.current_portfolio = analyzer
        else:
            st.warning(
                "Your portfolio was restored but its prices could not be loaded. "
                "Open Build and run the analysis again."
                if lang == 'en' else
                "Votre portefeuille a été restauré mais ses prix n'ont pas pu être "
                "chargés. Ouvrez Construire et relancez l'analyse."
            )


def main():
    init_session_state()
    lang = st.session_state.language
    # Read fresh on every run: a level granted or revoked since sign-in applies now.
    if st.session_state.get("authenticated") and st.session_state.get("user_email"):
        st.session_state.user_tier = resolve_tier(st.session_state.user_email)
    tier = st.session_state.user_tier

    _restore_workspace(lang)
    _sidebar(lang)

    page = st.session_state.page

    # ─────────────────────────────────────────────────────────────────────────
    # SENSITOR INTELLIGENCE PAGES
    # ─────────────────────────────────────────────────────────────────────────
    if page in TRADING_PAGES:
        TRADING_PAGES[page]()
        return

    if page in SENSITOR_PAGES:
        ctx = _sensitor_context(lang)
        if ctx is not None:
            # Only the failure. A dropped asset changes every figure on every
            # page, so it belongs above all of them; the captions are rendered
            # by the overview itself, under its own header.
            _currency_notice(ctx.analyzer, lang, verbose=False)
            _unanalysed_notice(lang)
        SENSITOR_PAGES[page](ctx)
        if ctx is not None:
            st.session_state.sensitor_period = ctx.period
        return

    # ─────────────────────────────────────────────────────────────────────────
    # ACCOUNT / LOGIN PAGE
    # ─────────────────────────────────────────────────────────────────────────
    if page == "account":
        _account_page(lang, tier)

        st.markdown("---")
        st.markdown("### Access" if lang == 'en' else "### Accès")
        st.markdown(
            ("Free access: up to 5 assets per portfolio, every analysis page. Extended access adds up to 50 "
             "assets, optimisation and stress tests; there is no paid plan, and it is granted by the Sensitor "
             "team on the same account as the platform."
             if lang == 'en' else
             "Accès gratuit : jusqu'à 5 actifs par portefeuille, toutes les pages d'analyse. L'accès étendu ajoute "
             "jusqu'à 50 actifs, l'optimisation et les stress tests ; il n'y a pas d'abonnement payant, il est "
             "attribué par l'équipe Sensitor, sur le même compte que la plateforme.")
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PAGES THAT MOVED TO THE PLATFORM (docs/FUSION_ANALYSEUR.md)
    # ─────────────────────────────────────────────────────────────────────────
    else:
        _moved_page(page, lang)


def run():
    """
    One script run, with the working portfolio written down afterwards.

    The `finally` is what makes the persistence reliable. `main()` returns from
    six different branches and half the interactive paths end in `st.rerun()`,
    which raises — so anything written at "the end of main" would be written on
    some runs and not others. A `finally` runs on all of them, and on a rerun it
    runs *after* the new state was set, which is exactly the state worth keeping.
    """
    try:
        main()
    finally:
        try:
            store, email = _workspace_store_and_user()
            _workspace.persist(store, email)
        except Exception:                                # noqa: BLE001
            # Persisting is a convenience. It must never be the reason a page
            # fails to render.
            pass


if __name__ == "__main__":
    run()
