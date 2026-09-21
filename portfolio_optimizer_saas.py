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

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ── Sensitor package ─────────────────────────────────────────────────────────
# Engine, design system, visual components and the twelve Intelligence and
# Workspace pages. Nothing below this line computes anything the package cannot.
from sensitor.core import config as core_config
from sensitor.core.i18n import LEGACY_STRINGS
from sensitor.investment import assets
from sensitor.investment.portfolio import UltimatePortfolioAnalyzer
from sensitor.ui import themes as sensitor_design
from sensitor.investment.context import build_context
from sensitor.core.i18n import tr as s_tr
from sensitor.pages import (
    render_advisor, render_copilot, render_health, render_optimize, render_overview,
    render_performance, render_portfolios, render_reports, render_risk,
    render_simulator, render_stress, render_xray,
    render_trading_analytics, render_trading_journal, render_trading_overview,
    render_trading_psychology, render_trading_risk,
)

# =============================================================================
# STRIPE / SUBSCRIPTION CONFIGURATION
# =============================================================================

# Configuration now lives in sensitor.core.config, which reads the environment
# once and has no Streamlit dependency — the same settings serve the app, the
# report generator and the future API. Re-bound to the original names so the
# legacy pages below are untouched.
STRIPE_CONFIG = {
    'payment_link': core_config.STRIPE_PAYMENT_LINK,
    'pro_price_monthly': core_config.PRO_PRICE_MONTHLY,
}
PRO_EMAILS = core_config.PRO_EMAILS
TIER_LIMITS = core_config.TIER_LIMITS


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Portfolio Health Pro",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS — Dark pro theme, Inter font, high contrast
# =============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif !important;
    }

    /* ── Animations ── */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideRight {
        from { opacity: 0; transform: translateX(-14px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes shimmer {
        0%   { background-position: -400px 0; }
        100% { background-position: 400px 0; }
    }
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(99,102,241,0.3); }
        50%       { box-shadow: 0 0 40px rgba(99,102,241,0.6); }
    }

    /* ── App background ── */
    .stApp {
        background: linear-gradient(160deg, #0d1526 0%, #111827 50%, #0f172a 100%) !important;
        min-height: 100vh;
    }

    /* ── Main content area ── */
    .main .block-container {
        background: transparent !important;
        border-radius: 0 !important;
        padding: 2rem 2.5rem !important;
        max-width: 1300px !important;
        animation: fadeUp 0.45s ease-out;
    }

    /* ── ALL TEXT in main area ── */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: #f8fafc !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }
    .main p, .main li, .main span, .main div, .main label {
        color: #e2e8f0 !important;
    }
    .main .stMarkdown, .main .stText {
        color: #e2e8f0 !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1526 0%, #111827 100%) !important;
        border-right: 1px solid rgba(0,212,255,0.12) !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #94a3b8 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
        text-align: left !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(99,102,241,0.2) !important;
        border-color: rgba(99,102,241,0.5) !important;
        color: #e2e8f0 !important;
        transform: translateX(3px) !important;
    }
    [data-testid="stSidebar"] .stButton > [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
        border-color: transparent !important;
        color: white !important;
        box-shadow: 0 2px 12px rgba(99,102,241,0.4) !important;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #e2e8f0 !important;
    }

    /* ── Main buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 11px 26px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 4px 16px rgba(79,70,229,0.35) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(79,70,229,0.5) !important;
    }
    .stButton > button[kind="secondary"] {
        background: rgba(255,255,255,0.06) !important;
        color: #94a3b8 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        box-shadow: none !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: rgba(255,255,255,0.1) !important;
        color: #e2e8f0 !important;
        transform: translateY(-1px) !important;
    }

    /* ── Score / stat cards ── */
    .score-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4c1d95 100%);
        border: 1px solid rgba(139,92,246,0.3);
        border-radius: 20px;
        padding: 32px 36px;
        margin: 16px 0;
        box-shadow: 0 8px 40px rgba(79,70,229,0.3);
        animation: fadeUp 0.5s ease-out;
        position: relative;
        overflow: hidden;
    }
    .score-card::before {
        content: '';
        position: absolute;
        top: -30%; right: -10%;
        width: 250px; height: 250px;
        background: radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .score-card::after {
        content: '';
        position: absolute;
        bottom: -20%; left: -5%;
        width: 180px; height: 180px;
        background: radial-gradient(circle, rgba(99,102,241,0.10) 0%, transparent 70%);
        border-radius: 50%;
    }
    .score-num {
        font-size: 5rem;
        font-weight: 900;
        color: white;
        line-height: 1;
        letter-spacing: -0.04em;
        text-shadow: 0 2px 20px rgba(255,255,255,0.2);
    }
    .score-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.55);
        margin-bottom: 8px;
    }
    .score-badge {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 5px 16px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: white;
        margin-top: 10px;
    }
    .bar-bg {
        background: rgba(255,255,255,0.12);
        border-radius: 6px;
        height: 6px;
        overflow: hidden;
        margin-top: 5px;
    }
    .bar-fill {
        height: 100%;
        border-radius: 6px;
        background: rgba(255,255,255,0.75);
        transition: width 0.7s ease-out;
    }

    /* ── Dark metric cards ── */
    .metric-card {
        background: #1e293b;
        border: 1px solid rgba(0,212,255,0.12);
        border-radius: 16px;
        padding: 22px 26px;
        transition: all 0.25s ease;
    }
    .metric-card:hover {
        border-color: rgba(0,212,255,0.35);
        box-shadow: 0 4px 24px rgba(0,212,255,0.10);
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 0.72rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #f1f5f9;
        line-height: 1;
        letter-spacing: -0.02em;
    }

    /* ── Recommendation cards ── */
    .rec-card {
        background: #1e293b;
        border-left: 4px solid #6366f1;
        padding: 18px 22px;
        margin: 10px 0;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.06);
        border-left: 4px solid #6366f1;
        animation: slideRight 0.4s ease-out;
        transition: all 0.2s ease;
    }
    .rec-card:hover {
        background: #1a2540;
        transform: translateX(4px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .rec-card h4 { color: #f1f5f9 !important; margin: 0 0 8px 0; font-size: 0.95rem; font-weight: 600; }
    .rec-card p  { color: #94a3b8 !important; margin: 4px 0; line-height: 1.6; font-size: 0.87rem; }
    .rec-card.critical { border-left-color: #ef4444 !important; }
    .rec-card.warning  { border-left-color: #f59e0b !important; }
    .rec-card.success  { border-left-color: #10b981 !important; }
    .rec-card.info     { border-left-color: #6366f1 !important; }

    /* ── Asset cards ── */
    .asset-card {
        background: #1e293b;
        border: 1px solid rgba(99,102,241,0.12);
        border-radius: 14px;
        padding: 20px 24px;
        margin: 6px 0;
        transition: all 0.25s ease;
    }
    .asset-card:hover {
        border-color: rgba(99,102,241,0.4);
        background: #1a2540;
        box-shadow: 0 4px 24px rgba(99,102,241,0.15);
    }
    .asset-card p, .asset-card span, .asset-card div {
        color: #94a3b8 !important;
    }

    /* ── Badges ── */
    .asset-class-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .risk-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }

    /* ── Progress bar (dark) ── */
    .progress-bar-bg {
        background: rgba(255,255,255,0.08);
        border-radius: 6px;
        height: 7px;
        overflow: hidden;
        margin-top: 4px;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 6px;
        transition: width 0.6s ease-out;
    }

    /* ── Model portfolio cards ── */
    .model-card {
        background: #1e293b;
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 16px;
        padding: 24px 28px;
        margin: 10px 0;
        transition: all 0.25s ease;
    }
    .model-card:hover {
        border-color: rgba(99,102,241,0.4);
        background: #1a2540;
        box-shadow: 0 8px 32px rgba(99,102,241,0.18);
        transform: translateY(-3px);
    }

    /* ── Upgrade card ── */
    .upgrade-card {
        background: linear-gradient(135deg, rgba(79,70,229,0.15), rgba(124,58,237,0.15));
        border: 1px solid rgba(99,102,241,0.35);
        border-radius: 16px;
        padding: 28px 32px;
        text-align: center;
        margin: 16px 0;
    }
    .upgrade-card h3 { color: #a5b4fc !important; margin: 0 0 8px 0; }
    .upgrade-card p  { color: #818cf8 !important; font-size: 0.9rem; }

    /* ── Paywall block ── */
    .paywall-block {
        background: rgba(79,70,229,0.08);
        border: 1px dashed rgba(99,102,241,0.3);
        border-radius: 14px;
        padding: 32px;
        text-align: center;
        margin: 16px 0;
    }

    /* ── Native Streamlit metric override ── */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #f1f5f9 !important;
        font-weight: 800 !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        color: #64748b !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
    }

    /* ── Progress bars ── */
    .stProgress > div > div {
        background: linear-gradient(90deg, #00d4ff 0%, #4f46e5 100%) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.04) !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748b !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.84rem !important;
        transition: all 0.2s !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0ea5e9, #4f46e5) !important;
        color: white !important;
        box-shadow: 0 2px 12px rgba(14,165,233,0.4) !important;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: #161b22 !important;
        border: 1px solid rgba(0,212,255,0.12) !important;
        border-radius: 10px !important;
        color: #cbd5e1 !important;
    }
    .streamlit-expanderHeader:hover {
        background: #1c2333 !important;
        border-color: rgba(0,212,255,0.3) !important;
    }
    details[open] .streamlit-expanderHeader {
        border-bottom-left-radius: 0 !important;
        border-bottom-right-radius: 0 !important;
    }

    /* ── KPI fintech cards ── */
    .kpi-card {
        background: linear-gradient(145deg, #1e293b, #263348);
        border: 1px solid rgba(0,212,255,0.12);
        border-radius: 18px;
        padding: 22px 24px 18px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    .kpi-card:hover {
        border-color: rgba(0,212,255,0.35);
        box-shadow: 0 8px 32px rgba(0,212,255,0.10);
        transform: translateY(-3px);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: -20px; right: -20px;
        width: 90px; height: 90px;
        background: radial-gradient(circle, rgba(0,212,255,0.07) 0%, transparent 70%);
        border-radius: 50%;
    }
    .kpi-icon  { font-size: 1.3rem; margin-bottom: 10px; }
    .kpi-label {
        font-size: 0.67rem; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: #475569; margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2.2rem; font-weight: 900; line-height: 1;
        letter-spacing: -0.03em; margin-bottom: 6px;
    }
    .kpi-sub   { font-size: 0.75rem; color: #475569; line-height: 1.4; }
    .kpi-positive { color: #00ff9c; }
    .kpi-negative { color: #ff4d4d; }
    .kpi-neutral  { color: #00d4ff; }
    .kpi-warning  { color: #ffb020; }

    /* ── Section headers ── */
    .section-header {
        display: flex; align-items: center; gap: 12px;
        margin: 32px 0 18px; padding-bottom: 12px;
        border-bottom: 1px solid rgba(0,212,255,0.1);
    }
    .section-icon {
        width: 34px; height: 34px;
        background: linear-gradient(135deg, rgba(0,212,255,0.12), rgba(99,102,241,0.12));
        border: 1px solid rgba(0,212,255,0.18);
        border-radius: 9px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem;
    }
    .section-title { font-size: 1rem; font-weight: 700; color: #e2e8f0; }
    .section-sub   { font-size: 0.76rem; color: #475569; margin-top: 2px; }

    /* ── Tooltip hint boxes ── */
    .tooltip-hint {
        background: rgba(0,212,255,0.05);
        border: 1px solid rgba(0,212,255,0.12);
        border-radius: 10px; padding: 10px 14px;
        font-size: 0.80rem; color: #64748b; line-height: 1.55;
    }
    .tooltip-hint strong { color: #00d4ff; }

    /* ── Fintech gradient divider ── */
    .ft-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(0,212,255,0.25) 40%,
                    rgba(99,102,241,0.25) 60%, transparent 100%);
        margin: 28px 0; border: none;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input {
        background: #131c30 !important;
        border: 1px solid rgba(99,102,241,0.2) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    }
    .stSelectbox > div > div {
        background: #131c30 !important;
        border: 1px solid rgba(99,102,241,0.2) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
    }

    /* ── Sliders ── */
    .stSlider > div > div > div {
        color: #f1f5f9 !important;
    }
    .stSlider label { color: #94a3b8 !important; font-size:0.82rem !important; }

    /* ── Success / warning / error ── */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
    }
    div[data-testid="stNotification"] { border-radius: 12px !important; }

    /* ── Divider ── */
    hr {
        border: none !important;
        border-top: 1px solid rgba(255,255,255,0.06) !important;
        margin: 24px 0 !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #060818; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #4f46e5; }

    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Sensitor design system — injected after the legacy stylesheet so its tokens win
# on the new pages while the existing pages keep their current appearance.
sensitor_design.inject_theme()

# =============================================================================
# DATA: ASSET INFO, MODEL PORTFOLIOS, SECTORS
# =============================================================================

# 630 lines of instrument reference data moved to sensitor.investment.assets in
# V2 Phase 2. Re-bound here so every legacy page keeps its module-level names.
ASSET_INFO = assets.ASSET_INFO
SECTOR_MAPPING = assets.SECTOR_MAPPING
GEOGRAPHY_MAPPING = assets.GEOGRAPHY_MAPPING
POPULAR_ASSETS = assets.POPULAR_ASSETS
MODEL_PORTFOLIOS = assets.MODEL_PORTFOLIOS


# =============================================================================
# SESSION STATE WITH AUTO-REBALANCE
# =============================================================================

def resolve_tier(email: str) -> str:
    """Entitlement for an email address. Delegates to sensitor.core.config."""
    return core_config.resolve_tier(email)



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
        'page': "overview",
        'language': "en",
        'selected_tickers': [],
        'weights': {},
        'user_profile': "balanced",
        'analysis_mode': "simulation",       # "simulation" or "real"
        'real_portfolio_holdings': {},        # {ticker: quantity}
        'real_portfolio_total_value': None,   # float — computed after price fetch
        'real_portfolio_prices': {},          # {ticker: current_price}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def auto_rebalance_weights():
    """Auto-rebalance weights to equal share and sync slider states."""
    tickers = st.session_state.selected_tickers
    if not tickers:
        st.session_state.weights = {}
        return

    equal_weight = 1.0 / len(tickers)

    # Reset to equal weights whenever the asset list changes
    if not st.session_state.weights or set(st.session_state.weights.keys()) != set(tickers):
        st.session_state.weights = {ticker: equal_weight for ticker in tickers}

    # Normalize to 100%
    total = sum(st.session_state.weights.values())
    if total > 0:
        st.session_state.weights = {k: v / total for k, v in st.session_state.weights.items()}

    # Sync slider widget states so displayed values update immediately
    for ticker, w in st.session_state.weights.items():
        st.session_state[f"ws_{ticker}"] = round(w * 100, 1)

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

def section_header(icon, title, subtitle=""):
    """Styled fintech section header with icon."""
    sub_html = f"<div class='section-sub'>{subtitle}</div>" if subtitle else ""
    st.markdown(f"""
    <div class="section-header">
      <div class="section-icon">{icon}</div>
      <div>
        <div class="section-title">{title}</div>
        {sub_html}
      </div>
    </div>
    """, unsafe_allow_html=True)


def ft_divider():
    """Fintech gradient divider."""
    st.markdown("<div class='ft-divider'></div>", unsafe_allow_html=True)


def render_kpi_cards(metrics, lang="en"):
    """4 fintech KPI cards: Sharpe, Return, Volatility, Drawdown."""
    sharpe = metrics['sharpe']
    ret    = metrics['annual_return']
    vol    = metrics['volatility']
    dd     = metrics['max_drawdown']

    sharpe_cls = "kpi-positive" if sharpe > 1 else "kpi-warning" if sharpe > 0.5 else "kpi-negative"
    ret_cls    = "kpi-positive" if ret > 0 else "kpi-negative"
    vol_cls    = "kpi-positive" if vol < 0.15 else "kpi-warning" if vol < 0.25 else "kpi-negative"
    dd_cls     = "kpi-positive" if dd > -0.10 else "kpi-warning" if dd > -0.20 else "kpi-negative"

    if lang == 'en':
        cards_data = [
            ("📈", "Sharpe Ratio",    f"{sharpe:.2f}",         "> 1.0 = excellent",        sharpe_cls),
            ("💰", "Annual Return",   f"{ret*100:+.1f}%",      "Annualised, since start",   ret_cls),
            ("〰️", "Volatility",      f"{vol*100:.1f}%",       "< 15% = low risk",          vol_cls),
            ("📉", "Max Drawdown",    f"{dd*100:.1f}%",        "Worst peak-to-trough loss", dd_cls),
        ]
    else:
        cards_data = [
            ("📈", "Ratio de Sharpe",  f"{sharpe:.2f}",        "> 1.0 = excellent",           sharpe_cls),
            ("💰", "Rendement Annuel", f"{ret*100:+.1f}%",     "Annualisé, depuis le début",  ret_cls),
            ("〰️", "Volatilité",       f"{vol*100:.1f}%",      "< 15% = faible risque",       vol_cls),
            ("📉", "Max Drawdown",     f"{dd*100:.1f}%",       "Perte maximale crête–creux",  dd_cls),
        ]

    cols = st.columns(4)
    for col, (icon, label, value, hint, cls) in zip(cols, cards_data):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-icon">{icon}</div>
              <div class="kpi-label">{label}</div>
              <div class="kpi-value {cls}">{value}</div>
              <div class="kpi-sub">{hint}</div>
            </div>
            """, unsafe_allow_html=True)


def render_health_gauge(score, lang="en"):
    """Plotly gauge chart for portfolio health score (0–100)."""
    if score >= 80:
        bar_color = "#00ff9c"
    elif score >= 60:
        bar_color = "#00d4ff"
    elif score >= 40:
        bar_color = "#ffb020"
    else:
        bar_color = "#ff4d4d"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(
            font=dict(size=52, color=bar_color, family='Inter, sans-serif'),
            suffix="/100",
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickwidth=1,
                tickvals=[0, 20, 40, 60, 80, 100],
                tickcolor='rgba(255,255,255,0.12)',
                tickfont=dict(color='#475569', size=10),
            ),
            bar=dict(color=bar_color, thickness=0.22),
            bgcolor='rgba(0,0,0,0)',
            borderwidth=0,
            steps=[
                dict(range=[0,  40], color='rgba(255,77,77,0.10)'),
                dict(range=[40, 60], color='rgba(255,176,32,0.10)'),
                dict(range=[60, 80], color='rgba(0,212,255,0.10)'),
                dict(range=[80,100], color='rgba(0,255,156,0.10)'),
            ],
            threshold=dict(
                line=dict(color=bar_color, width=3),
                thickness=0.80,
                value=score,
            ),
        ),
    ))
    fig.update_layout(
        height=240,
        margin=dict(l=20, r=20, t=20, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif'),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_metric_tooltips(lang="en"):
    """Collapsible tooltip panel explaining key financial metrics."""
    label = "ℹ️ Understanding the metrics" if lang == 'en' else "ℹ️ Comprendre les métriques"
    with st.expander(label):
        if lang == 'en':
            tips = [
                ("📈 Sharpe Ratio",  "Measures return per unit of risk. Above 1 is good, above 2 is excellent. Below 0 means the portfolio loses money after adjusting for risk."),
                ("〰️ Volatility",    "Annualised standard deviation of daily returns. < 10% = very stable, 10–20% = moderate, > 25% = high risk."),
                ("📉 Max Drawdown",  "The largest percentage drop from a portfolio peak to a trough. Lower is better. E.g. −30% means the portfolio once lost 30% of its value."),
                ("🔀 Diversification", "Spreading assets across sectors, geographies and asset classes to reduce concentration risk. More uncorrelated assets = better diversification."),
                ("🔗 Correlation",   "A value between −1 and +1. Assets close to +1 move together (less diversification). Assets near −1 move oppositely (good hedge)."),
            ]
        else:
            tips = [
                ("📈 Ratio de Sharpe", "Mesure le rendement par unité de risque. > 1 = bon, > 2 = excellent. < 0 = le portefeuille perd de l'argent après ajustement du risque."),
                ("〰️ Volatilité",      "Écart-type annualisé des rendements quotidiens. < 10% = très stable, 10–20% = modéré, > 25% = risque élevé."),
                ("📉 Max Drawdown",    "La plus grande baisse entre un sommet et un creux. Plus c'est proche de 0, mieux c'est. Ex : −30% = perte temporaire de 30% de la valeur."),
                ("🔀 Diversification", "Répartir les actifs par secteur, zone géographique et classe d'actifs pour réduire la concentration. Plus les actifs sont décorrélés, mieux c'est."),
                ("🔗 Corrélation",     "Valeur entre −1 et +1. Proche de +1 = actifs évoluent ensemble (moins de diversification). Proche de −1 = actifs opposés (bonne couverture)."),
            ]
        for title, desc in tips:
            st.markdown(f"""
            <div class="tooltip-hint" style="margin-bottom:8px;">
              <strong>{title}</strong><br/>{desc}
            </div>
            """, unsafe_allow_html=True)


def render_health_score(health, lang="en"):
    """Render the Global Portfolio Health Score card."""
    total = health['total']
    color = health['color']
    grade = health['grade'] if lang == 'en' else health['grade_fr']
    label = "Portfolio Health Score" if lang == 'en' else "Score de Santé du Portefeuille"

    sub_labels = {
        'en': ('Structure', 'Performance', 'Liquidity'),
        'fr': ('Structure', 'Performance', 'Liquidité'),
    }[lang]

    sub_scores = [
        (sub_labels[0], health['structure']),
        (sub_labels[1], health['performance']),
        (sub_labels[2], health['liquidity']),
    ]

    bars_html = ""
    for name, val in sub_scores:
        bars_html += f"""
        <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;font-size:0.82rem;margin-bottom:4px;opacity:0.85;">
                <span>{name}</span><span style="font-weight:600;">{val}/100</span>
            </div>
            <div class="subscore-bar-bg">
                <div class="subscore-bar-fill" style="width:{val}%;"></div>
            </div>
        </div>"""

    st.markdown(f"""
    <div class="health-card">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:16px;">
        <div>
          <div style="font-size:0.75rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;opacity:0.7;margin-bottom:6px;">
            {label}
          </div>
          <div class="health-score-num">{total}<span style="font-size:1.8rem;font-weight:400;opacity:0.6;">/100</span></div>
          <div class="health-grade">{grade}</div>
        </div>
        <div style="min-width:200px;flex:1;max-width:320px;">
          {bars_html}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_robustness_score(robustness, lang="en"):
    """Render Robustness Index using native Streamlit components — no HTML injection."""
    total = robustness['total']
    color = robustness['color']
    interpretation = robustness['interpretation']

    # ── Header row
    label = "Robustness Index" if lang == 'en' else "Indice de Robustesse"
    interp_fr = {
        "Very Robust": "Très Robuste", "Robust": "Robuste",
        "Fragile": "Fragile", "High Risk": "Risque Élevé",
    }
    interp_display = interpretation if lang == 'en' else interp_fr.get(interpretation, interpretation)

    score_color_map = {
        "#10b981": "normal", "#6366f1": "normal", "#f59e0b": "inverse", "#ef4444": "inverse"
    }

    st.markdown(f"""<div style="background:linear-gradient(135deg,#1e1b4b,#312e81,#4c1d95);
border:1px solid rgba(139,92,246,0.3);border-radius:20px;padding:28px 32px;margin:12px 0;
box-shadow:0 8px 40px rgba(79,70,229,0.25);position:relative;overflow:hidden;">
<div style="font-size:0.7rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
color:rgba(255,255,255,0.5);margin-bottom:6px;">{label}</div>
<div style="font-size:4.5rem;font-weight:900;color:white;line-height:1;letter-spacing:-0.04em;">
{total}<span style="font-size:1.8rem;font-weight:400;opacity:0.4;">/100</span></div>
<div style="display:inline-block;margin-top:10px;background:rgba(255,255,255,0.12);
border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:4px 16px;
font-size:0.75rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;
color:white;">{interp_display}</div></div>""", unsafe_allow_html=True)

    # ── Breakdown using native Streamlit (no HTML needed)
    breakdown_label = "Score Breakdown" if lang == 'en' else "Détail du Score"
    st.markdown(f"**{breakdown_label}**")

    components = [
        ("Diversification",                                              robustness['diversification'], 20),
        ("Concentration",                                                robustness['concentration'],   20),
        ("Correlation"   if lang == 'en' else "Corrélation",            robustness['correlation'],     15),
        ("Volatility"    if lang == 'en' else "Volatilité",             robustness['volatility'],      15),
        ("Drawdown",                                                     robustness['drawdown'],        15),
        ("Geography"     if lang == 'en' else "Géographie",             robustness['geography'],       10),
        ("Sectors"       if lang == 'en' else "Secteurs",               robustness['sector'],           5),
    ]

    col_a, col_b = st.columns(2)
    for i, (name, score, max_score) in enumerate(components):
        pct = score / max_score
        icon = "🟢" if pct > 0.8 else "🟡" if pct > 0.6 else "🔴"
        target_col = col_a if i % 2 == 0 else col_b
        with target_col:
            st.markdown(
                f"<div style='font-size:0.78rem;color:#94a3b8;margin-bottom:2px;"
                f"margin-top:10px;'>{icon} <strong style='color:#e2e8f0;'>{name}</strong>"
                f" <span style='float:right;color:#64748b;'>{score}/{max_score}</span></div>",
                unsafe_allow_html=True
            )
            st.progress(pct)

def render_improvement_suggestions(suggestions, lang="en"):
    """Render improvement suggestions."""
    if not suggestions:
        ok_msg = "No major improvements needed." if lang == "en" else "Aucune amélioration majeure requise."
        st.success(ok_msg)
        return
    
    rec_title = "Improvement Suggestions" if lang == "en" else "Suggestions d'Amélioration"
    st.markdown(f"### {rec_title}")
    
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'INFO': 3}
    suggestions.sort(key=lambda x: priority_order.get(x['priority'], 4))
    
    for sug in suggestions:
        badge_colors = {
            'CRITICAL': '#ef4444',
            'HIGH': '#f59e0b',
            'MEDIUM': '#6366f1',
            'INFO': '#10b981'
        }
        badge_color = badge_colors.get(sug['priority'], '#64748b')
        
        issue_label = "Issue" if lang == "en" else "Problème"
        sol_label = "Solution" if lang == "en" else "Solution"
        impact_label = "Expected impact" if lang == "en" else "Impact attendu"
        st.markdown(f"""
        <div class='rec-card {sug['type']}'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                <h4 style='margin: 0;'>{sug['title']}</h4>
                <span style='background: {badge_color}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 0.72rem; font-weight: 600; letter-spacing:0.04em;'>
                    {sug['priority']}
                </span>
            </div>
            <p><strong>{issue_label}:</strong> {sug['issue']}</p>
            <p><strong>{sol_label}:</strong> {sug['solution']}</p>
            {f"<p style='color:#818cf8;font-weight:600;margin-top:10px;font-size:0.85rem;'>{impact_label}: {sug['impact']}</p>" if sug.get("impact") else ""}
        </div>
        """, unsafe_allow_html=True)

def render_asset_card(ticker, lang="en", show_weight=None):
    """Educational asset card with enriched content."""
    _default_desc = (
        "This asset is not yet in our library. It will still be analysed from market data."
        if lang == 'en' else
        "Cet actif n'est pas encore dans notre bibliothèque. Il sera quand même analysé à partir des données de marché."
    )
    info = ASSET_INFO.get(ticker, {
        "name": ticker,
        "description": _default_desc,
        "sector": SECTOR_MAPPING.get(ticker, "Unknown"),
        "geography": GEOGRAPHY_MAPPING.get(ticker, "Unknown"),
        "asset_class": "Unknown",
        "utility": "N/A",
        "typical_use": "N/A",
        "risk_level": "Unknown",
        "liquidity": 70,
        "dividend_yield": "N/A",
        "market_cap": "N/A",
    })
    # Pick bilingual fields if available
    description = info.get(f"description_{lang}", info.get("description", ""))
    utility     = info.get(f"utility_{lang}",     info.get("utility", "N/A"))
    typical_use = info.get(f"typical_use_{lang}", info.get("typical_use", "N/A"))

    risk_colors = {
        "Low": "#10b981", "Low-Medium": "#22d3ee", "Medium": "#6366f1",
        "Medium-High": "#f59e0b", "High": "#f97316", "Very High": "#ef4444",
        "Unknown": "#94a3b8",
    }
    class_colors = {
        "Stock": "#dbeafe", "ETF": "#d1fae5", "Crypto": "#fef3c7",
        "Commodity": "#fde8d8", "Bond": "#ede9fe", "Unknown": "#f1f5f9",
    }
    class_text_colors = {
        "Stock": "#1d4ed8", "ETF": "#065f46", "Crypto": "#92400e",
        "Commodity": "#c2410c", "Bond": "#5b21b6", "Unknown": "#64748b",
    }

    risk = info.get("risk_level", "Unknown")
    asset_class = info.get("asset_class", "Unknown")
    liq = info.get("liquidity", 70)
    risk_color = risk_colors.get(risk, "#94a3b8")
    cls_bg = class_colors.get(asset_class, "#f1f5f9")
    cls_txt = class_text_colors.get(asset_class, "#64748b")

    # Display labels (translated)
    risk_labels_fr = {
        "Low": "Faible", "Low-Medium": "Faible-Moyen", "Medium": "Moyen",
        "Medium-High": "Moyen-Élevé", "High": "Élevé", "Very High": "Très Élevé",
        "Unknown": "Inconnu",
    }
    class_labels_fr = {
        "Stock": "Action", "ETF": "ETF", "Crypto": "Crypto",
        "Commodity": "Matière 1ère", "Bond": "Obligation", "Unknown": "Inconnu",
    }
    risk_display = risk if lang == 'en' else risk_labels_fr.get(risk, risk)
    class_display = asset_class if lang == 'en' else class_labels_fr.get(asset_class, asset_class)

    weight_html = ""
    if show_weight is not None:
        weight_html = f"<span style='font-size:0.78rem;font-weight:600;color:#4f46e5;margin-left:8px;'>{show_weight*100:.1f}%</span>"

    with st.expander(f"{ticker}  —  {info['name']}"):
        role_label = "Portfolio role" if lang == 'en' else "Rôle dans le portefeuille"
        use_label = "Typical use" if lang == 'en' else "Utilisation typique"
        liq_label = "Liquidity" if lang == 'en' else "Liquidité"
        sector_label = "Sector" if lang == 'en' else "Secteur"
        geo_label = "Geography" if lang == 'en' else "Géographie"
        div_label = "Dividend / Yield" if lang == 'en' else "Dividende / Rendement"
        cap_label = "Market Cap / AUM" if lang == 'en' else "Cap. Boursière / AUM"
        st.markdown(f"""
        <div class="asset-card">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
            <span class="asset-class-badge" style="background:{cls_bg};color:{cls_txt};">{class_display}</span>
            <span class="risk-badge" style="background:{risk_color}22;color:{risk_color};">{risk_display}</span>
            {weight_html}
          </div>
          <p style="color:#94a3b8;font-size:0.88rem;line-height:1.7;margin-bottom:16px;">{description}</p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px 24px;font-size:0.83rem;">
            <div><span style="color:#4b5563;font-weight:500;">{sector_label}</span><br/>
                 <span style="color:#e2e8f0;font-weight:600;">{info['sector']}</span></div>
            <div><span style="color:#4b5563;font-weight:500;">{geo_label}</span><br/>
                 <span style="color:#e2e8f0;font-weight:600;">{info['geography']}</span></div>
            <div><span style="color:#4b5563;font-weight:500;">{div_label}</span><br/>
                 <span style="color:#e2e8f0;font-weight:600;">{info.get('dividend_yield', 'N/A')}</span></div>
            <div><span style="color:#4b5563;font-weight:500;">{cap_label}</span><br/>
                 <span style="color:#e2e8f0;font-weight:600;">{info.get('market_cap', 'N/A')}</span></div>
          </div>
          <div style="margin-top:14px;padding-top:14px;border-top:1px solid rgba(99,102,241,0.12);">
            <div style="font-size:0.75rem;color:#4b5563;font-weight:600;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;">{liq_label}</div>
            <div class="progress-bar-bg" style="margin-bottom:10px;">
              <div class="progress-bar-fill" style="width:{liq}%;background:#6366f1;"></div>
            </div>
            <div style="font-size:0.82rem;color:#64748b;line-height:1.6;">
              <span style="color:#94a3b8;font-weight:600;">{role_label}:</span> {utility}<br/>
              <span style="color:#94a3b8;font-weight:600;">{use_label}:</span> {typical_use}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

def render_enhanced_charts(analyzer, lang="en"):
    """Enhanced visualizations with translated tabs and fintech styling."""

    if lang == 'fr':
        tab_labels = ["📈 Performance", "📉 Drawdown", "🥧 Allocation", "🌍 Géographie", "🏭 Secteurs"]
    else:
        tab_labels = ["📈 Performance", "📉 Drawdown", "🥧 Allocation", "🌍 Geography", "🏭 Sectors"]

    tabs = st.tabs(tab_labels)

    CHART_LAYOUT = dict(
        height=440,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', size=12, color='#94a3b8'),
        margin=dict(l=10, r=10, t=48, b=10),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#1c2333', bordercolor='rgba(0,212,255,0.3)',
                        font=dict(color='#f1f5f9', size=12)),
    )
    AXIS_STYLE = dict(
        showgrid=True,
        gridcolor='rgba(255,255,255,0.04)',
        gridwidth=1,
        linecolor='rgba(255,255,255,0.06)',
        tickfont=dict(size=11, color='#475569'),
        zerolinecolor='rgba(255,255,255,0.05)',
    )

    with tabs[0]:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=analyzer.portfolio_values.index,
            y=analyzer.portfolio_values.values,
            mode='lines',
            name='Portfolio' if lang == 'en' else 'Portefeuille',
            line=dict(color='#00d4ff', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(0,212,255,0.06)',
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>$%{y:,.0f}<extra></extra>',
        ))
        fig.update_layout(
            title=dict(
                text="Portfolio Performance" if lang == 'en' else "Performance du Portefeuille",
                font=dict(size=14, color='#e2e8f0', family='Inter'),
            ),
            yaxis=dict(tickprefix="$", **AXIS_STYLE),
            xaxis=AXIS_STYLE,
            **CHART_LAYOUT
        )
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        metrics = analyzer.calculate_metrics()
        drawdown = metrics['drawdown_series']
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values * 100,
            mode='lines',
            name='Drawdown',
            line=dict(color='#ff4d4d', width=2),
            fill='tozeroy',
            fillcolor='rgba(255,77,77,0.08)',
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>%{y:.1f}%<extra></extra>',
        ))
        fig.update_layout(
            title=dict(
                text="Portfolio Drawdown" if lang == 'en' else "Drawdown du Portefeuille",
                font=dict(size=14, color='#e2e8f0', family='Inter'),
            ),
            yaxis=dict(ticksuffix="%", **AXIS_STYLE),
            xaxis=AXIS_STYLE,
            **CHART_LAYOUT
        )
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        palette = ['#00d4ff','#4f46e5','#00ff9c','#ffb020','#ff4d4d',
                   '#818cf8','#34d399','#fbbf24','#a5b4fc','#6ee7b7']
        alloc_title = "Portfolio Allocation" if lang == 'en' else "Allocation du Portefeuille"
        fig = go.Figure(data=[go.Pie(
            labels=list(analyzer.weights.keys()),
            values=[v * 100 for v in analyzer.weights.values()],
            hole=0.50,
            marker=dict(colors=palette, line=dict(color='#0e1117', width=2)),
            textinfo='label+percent',
            textfont=dict(size=12, color='white'),
            hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>',
        )])
        fig.update_layout(
            title=dict(text=alloc_title, font=dict(size=14, color='#e2e8f0', family='Inter')),
            showlegend=True,
            legend=dict(orientation='v', x=1.02, y=0.5, font=dict(color='#94a3b8', size=11)),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', color='#94a3b8'),
            height=440, margin=dict(l=10, r=10, t=48, b=10),
            hoverlabel=dict(bgcolor='#1c2333', bordercolor='rgba(0,212,255,0.3)',
                            font=dict(color='#f1f5f9', size=12)),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        geo_alloc = {}
        for ticker in analyzer.tickers:
            geo = GEOGRAPHY_MAPPING.get(ticker, "Unknown")
            geo_alloc[geo] = geo_alloc.get(geo, 0) + analyzer.weights[ticker]

        sorted_geo = dict(sorted(geo_alloc.items(), key=lambda x: x[1], reverse=True))
        geo_title = "Geographic Allocation" if lang == 'en' else "Allocation Géographique"
        bar_colors = ['#00d4ff' if i == 0 else '#4f46e5' if i == 1 else '#818cf8'
                      for i in range(len(sorted_geo))]
        fig = go.Figure(data=[go.Bar(
            x=list(sorted_geo.keys()),
            y=[v*100 for v in sorted_geo.values()],
            marker=dict(color=bar_colors, opacity=0.9,
                        line=dict(color='rgba(0,212,255,0.3)', width=1)),
            text=[f"{v*100:.1f}%" for v in sorted_geo.values()],
            textposition='outside',
            textfont=dict(color='#94a3b8', size=11),
            hovertemplate='<b>%{x}</b><br>%{y:.1f}%<extra></extra>',
        )])
        fig.update_layout(
            title=dict(text=geo_title, font=dict(size=14, color='#e2e8f0', family='Inter')),
            yaxis=dict(ticksuffix="%", **AXIS_STYLE),
            xaxis=AXIS_STYLE,
            **CHART_LAYOUT
        )
        st.plotly_chart(fig, use_container_width=True)

    with tabs[4]:
        sector_alloc = {}
        for ticker in analyzer.tickers:
            sector = SECTOR_MAPPING.get(ticker, "Unknown")
            sector_alloc[sector] = sector_alloc.get(sector, 0) + analyzer.weights[ticker]

        sorted_sec = dict(sorted(sector_alloc.items(), key=lambda x: x[1], reverse=True))
        sec_title = "Sector Allocation" if lang == 'en' else "Allocation Sectorielle"
        sec_colors = ['#00ff9c', '#00d4ff', '#4f46e5', '#ffb020', '#ff4d4d',
                      '#818cf8', '#34d399', '#fbbf24', '#a5b4fc', '#6ee7b7']
        fig = go.Figure(data=[go.Bar(
            x=list(sorted_sec.keys()),
            y=[v*100 for v in sorted_sec.values()],
            marker=dict(
                color=sec_colors[:len(sorted_sec)],
                opacity=0.9,
                line=dict(color='rgba(255,255,255,0.1)', width=1),
            ),
            text=[f"{v*100:.1f}%" for v in sorted_sec.values()],
            textposition='outside',
            textfont=dict(color='#94a3b8', size=11),
            hovertemplate='<b>%{x}</b><br>%{y:.1f}%<extra></extra>',
        )])
        fig.update_layout(
            title=dict(text=sec_title, font=dict(size=14, color='#e2e8f0', family='Inter')),
            yaxis=dict(ticksuffix="%", **AXIS_STYLE),
            xaxis=AXIS_STYLE,
            **CHART_LAYOUT
        )
        st.plotly_chart(fig, use_container_width=True)

def render_upgrade_prompt(lang="en"):
    """Upgrade CTA card for free users."""
    price = STRIPE_CONFIG['pro_price_monthly']
    link = STRIPE_CONFIG['payment_link']
    title = "Upgrade to Pro" if lang == 'en' else "Passer à Pro"
    sub = (
        f"Unlock unlimited assets, portfolio optimisation, stress tests and more for ${price}/month."
        if lang == 'en' else
        f"Débloquez les actifs illimités, l'optimisation, les stress tests et plus encore pour {price} €/mois."
    )
    features = [
        ("Up to 50 assets per portfolio", "Jusqu'à 50 actifs par portefeuille"),
        ("Portfolio optimisation (Markowitz)", "Optimisation (Markowitz)"),
        ("Historical crisis stress tests", "Stress tests crises historiques"),
        ("Full Health Score breakdown", "Score de Santé détaillé"),
        ("Unlimited analyses", "Analyses illimitées"),
    ]
    features_html = "".join(
        f"<div style='font-size:0.85rem;color:#5b21b6;margin:4px 0;'>&#10003; {f[0] if lang=='en' else f[1]}</div>"
        for f in features
    )
    btn_html = (
        f'<a href="{link}" target="_blank" style="display:inline-block;margin-top:14px;'
        f'padding:10px 28px;background:linear-gradient(135deg,#4f46e5,#6366f1);color:white;'
        f'border-radius:9px;font-weight:600;font-size:0.9rem;text-decoration:none;'
        f'box-shadow:0 2px 8px rgba(79,70,229,0.3);">{title} — ${price}/mo</a>'
    ) if link else (
        f'<div style="margin-top:14px;font-size:0.82rem;color:#7c3aed;">Contact us to upgrade</div>'
    )

    st.markdown(f"""
    <div class="upgrade-card">
      <h3>{title}</h3>
      <p style="margin-bottom:12px;">{sub}</p>
      {features_html}
      {btn_html}
    </div>
    """, unsafe_allow_html=True)


def render_paywall(feature_name, lang="en"):
    """Inline paywall block for locked features."""
    msg = (
        f"**{feature_name}** is available on the Pro plan."
        if lang == 'en' else
        f"**{feature_name}** est disponible sur le plan Pro."
    )
    st.markdown(f"""
    <div style="background:#ede9fe;border:1px solid #c4b5fd;border-radius:12px;
                padding:20px 24px;text-align:center;margin:12px 0;">
      <div style="font-size:1.3rem;margin-bottom:8px;">&#128274;</div>
      <div style="font-weight:600;color:#4338ca;margin-bottom:4px;">{feature_name}</div>
      <div style="font-size:0.87rem;color:#5b21b6;">
        {'Available on Pro plan' if lang == 'en' else 'Disponible sur le plan Pro'}
      </div>
    </div>
    """, unsafe_allow_html=True)
    render_upgrade_prompt(lang)


def render_stress_test_results(stress_results, lang="en"):
    """Display stress test results using native Streamlit components."""
    if not stress_results:
        st.info("Not enough historical data for stress testing." if lang == 'en'
                else "Pas assez de données historiques pour ce test.")
        return

    loss_lbl       = "Portfolio loss"    if lang == 'en' else "Perte portefeuille"
    mkt_lbl        = "Market drop"       if lang == 'en' else "Chute du marché"
    resil_lbl      = "Resilience"        if lang == 'en' else "Résilience"
    vs_mkt_lbl     = "vs market"         if lang == 'en' else "vs marché"

    cols = st.columns(len(stress_results))
    for col, (scenario, result) in zip(cols, stress_results.items()):
        port_loss  = result['portfolio_loss'] * 100
        mkt_loss   = result['market_loss'] * 100
        resilience = max(0.0, min(1.0, result['resilience']))
        resil_pct  = resilience * 100

        if resil_pct >= 80:
            resil_color = "#00ff9c"
            badge = "🟢"
        elif resil_pct >= 50:
            resil_color = "#ffb020"
            badge = "🟡"
        else:
            resil_color = "#ff4d4d"
            badge = "🔴"

        with col:
            st.markdown(
                f"<div style='background:#1e293b;border:1px solid rgba(0,212,255,0.15);"
                f"border-radius:14px;padding:18px 20px;height:100%;'>"
                f"<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;"
                f"text-transform:uppercase;color:#475569;margin-bottom:6px;'>{scenario}</div>"
                f"<div style='font-size:0.78rem;color:#64748b;margin-bottom:14px;'>"
                f"{result['description']}</div>"
                f"<div style='font-size:0.7rem;color:#475569;margin-bottom:2px;'>{loss_lbl}</div>"
                f"<div style='font-size:1.6rem;font-weight:800;color:#ff4d4d;line-height:1;"
                f"margin-bottom:10px;'>{port_loss:+.1f}%</div>"
                f"<div style='font-size:0.7rem;color:#475569;margin-bottom:2px;'>{mkt_lbl}</div>"
                f"<div style='font-size:1rem;font-weight:600;color:#64748b;"
                f"margin-bottom:12px;'>{mkt_loss:.0f}%</div>"
                f"<div style='font-size:0.7rem;color:#475569;margin-bottom:4px;'>"
                f"{badge} {resil_lbl} {resil_pct:.0f}%</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.progress(resilience)

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


def _sidebar(lang):
    """Render sidebar navigation and user info."""
    with st.sidebar:
        st.markdown(
            "<div style='font-size:1.1rem;font-weight:700;color:#e2e8f0;letter-spacing:-0.01em;"
            "padding:0 0 4px 0;'>Portfolio Health Pro</div>"
            "<div style='font-size:0.72rem;color:#64748b;letter-spacing:0.05em;text-transform:uppercase;"
            "margin-bottom:20px;'>Professional Analytics</div>",
            unsafe_allow_html=True
        )

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

        st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:16px 0;'>",
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

        st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:14px 0;'>",
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
            # Redirect to appropriate default page
            if new_mode == "real":
                st.session_state.page = "real_portfolio"
            else:
                st.session_state.page = "overview"
            st.rerun()

        st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:14px 0;'>",
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
        if st.session_state.analysis_mode == "real":
            tools = [
                ("real_portfolio", t("real_portfolio", lang)),
                ("dashboard",      t("dashboard", lang)),
                ("library",        t("library", lang)),
                ("account",        t("account", lang)),
            ]
        else:
            tools = [
                ("new_analysis", t("new_analysis", lang)),
                ("models",       t("models", lang)),
                ("improve",      t("improve", lang)),
                ("dashboard",    t("dashboard", lang)),
                ("library",      t("library", lang)),
                ("account",      t("account", lang)),
            ]

        def _nav_group(title, entries):
            st.markdown(
                f"<div style='font-size:0.63rem;font-weight:700;letter-spacing:0.15em;"
                f"text-transform:uppercase;color:#465065;margin:6px 0 6px 4px;'>{title}</div>",
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

        st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:16px 0;'>",
                    unsafe_allow_html=True)

        # Tier badge
        tier = st.session_state.user_tier
        tier_color = "#10b981" if tier == 'pro' else "#f59e0b"
        tier_label = TIER_LIMITS[tier]['label']
        email_display = st.session_state.user_email or ("Demo mode" if lang == 'en' else "Mode démo")
        st.markdown(
            f"<div style='font-size:0.78rem;color:#64748b;margin-bottom:4px;'>{email_display}</div>"
            f"<div style='display:inline-block;background:{tier_color}22;color:{tier_color};"
            f"padding:2px 12px;border-radius:12px;font-size:0.72rem;font-weight:600;"
            f"letter-spacing:0.06em;text-transform:uppercase;'>{tier_label}</div>",
            unsafe_allow_html=True
        )
        if tier == 'free':
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("Upgrade to Pro" if lang == 'en' else "Passer à Pro",
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
        st.success(f"{s_tr('signed_in_as', lang)} **{email}** — "
                   f"{TIER_LIMITS[tier]['label']}")
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
        return

    if auth.multi_user:
        _multi_user_sign_in(auth, lang)
    else:
        _single_user_sign_in(auth, lang)


def _signed_in_email() -> str:
    from sensitor.pages._shared import current_user_email
    return current_user_email()


def _clear_session():
    st.session_state.session_token = ""
    st.session_state.user_email = ""
    st.session_state.authenticated = False
    st.session_state.user_tier = "free"


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


def main():
    init_session_state()
    lang = st.session_state.language
    tier = st.session_state.user_tier
    limits = TIER_LIMITS[tier]

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
        st.markdown("### Plans" if lang == 'en' else "### Abonnements")

        col_free, col_pro = st.columns(2)
        with col_free:
            st.markdown("""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:20px 22px;">
              <div style="font-weight:700;font-size:1rem;color:#0f172a;margin-bottom:4px;">Free</div>
              <div style="font-size:1.5rem;font-weight:800;color:#0f172a;">$0<span style="font-size:0.9rem;color:#64748b;font-weight:400;">/mo</span></div>
              <hr style="border-color:#e2e8f0;margin:12px 0;">
              <div style="font-size:0.85rem;color:#475569;">Up to 5 assets per portfolio</div>
              <div style="font-size:0.85rem;color:#475569;margin-top:4px;">Basic metrics &amp; charts</div>
              <div style="font-size:0.85rem;color:#475569;margin-top:4px;">Asset Library</div>
            </div>""", unsafe_allow_html=True)

        with col_pro:
            price = STRIPE_CONFIG['pro_price_monthly']
            link = STRIPE_CONFIG['payment_link']
            btn = (
                f'<a href="{link}" target="_blank" style="display:block;margin-top:14px;'
                f'padding:10px 0;background:linear-gradient(135deg,#4f46e5,#6366f1);color:white;'
                f'border-radius:9px;font-weight:600;font-size:0.88rem;text-decoration:none;'
                f'text-align:center;">Subscribe — ${price}/mo</a>'
            ) if link else (
                f'<div style="margin-top:14px;font-size:0.82rem;color:#7c3aed;">'
                f'Set STRIPE_PAYMENT_LINK env var to activate.</div>'
            )
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1e1b4b,#312e81);border-radius:12px;padding:20px 22px;">
              <div style="font-weight:700;font-size:1rem;color:white;margin-bottom:4px;">Pro</div>
              <div style="font-size:1.5rem;font-weight:800;color:white;">${price}<span style="font-size:0.9rem;color:#a5b4fc;font-weight:400;">/mo</span></div>
              <hr style="border-color:rgba(255,255,255,0.15);margin:12px 0;">
              <div style="font-size:0.85rem;color:#c7d2fe;">Up to 50 assets per portfolio</div>
              <div style="font-size:0.85rem;color:#c7d2fe;margin-top:4px;">Portfolio optimisation (Markowitz)</div>
              <div style="font-size:0.85rem;color:#c7d2fe;margin-top:4px;">Crisis stress tests</div>
              <div style="font-size:0.85rem;color:#c7d2fe;margin-top:4px;">Full Health Score breakdown</div>
              <div style="font-size:0.85rem;color:#c7d2fe;margin-top:4px;">Unlimited analyses</div>
              {btn}
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        how_label = "How Pro access works" if lang == 'en' else "Comment fonctionne l'accès Pro"
        with st.expander(how_label):
            st.markdown(
                """
**Step 1 — Subscribe** via the button above (Stripe secure checkout).

**Step 2 — Send your email** to the app administrator so your email is added to the Pro list
(or configure the `PRO_EMAILS` environment variable on Streamlit Cloud with your email).

**Step 3 — Log in** here with that email and your Pro features will unlock immediately.

> For automated activation, set up a Stripe webhook pointing to your backend and write the
> paying customer's email into the `PRO_EMAILS` environment variable.
                """ if lang == 'en' else """
**Étape 1 — Abonnez-vous** via le bouton ci-dessus (paiement sécurisé Stripe).

**Étape 2 — Envoyez votre email** à l'administrateur pour être ajouté à la liste Pro
(ou configurez la variable d'environnement `PRO_EMAILS` sur Streamlit Cloud avec votre email).

**Étape 3 — Connectez-vous** ici avec cet email et vos fonctionnalités Pro s'activeront.

> Pour une activation automatique, configurez un webhook Stripe vers votre backend
> qui écrit l'email de l'abonné dans la variable `PRO_EMAILS`.
                """
            )

    # ─────────────────────────────────────────────────────────────────────────
    # ASSET LIBRARY PAGE
    # ─────────────────────────────────────────────────────────────────────────
    elif page == "library":
        title = "Asset Library" if lang == 'en' else "Bibliothèque des Actifs"
        subtitle = (
            "Learn about each asset before adding it to your portfolio."
            if lang == 'en' else
            "Apprenez à connaître chaque actif avant de le ajouter à votre portefeuille."
        )
        st.title(title)
        st.markdown(f"<p style='color:#64748b;margin-top:-12px;'>{subtitle}</p>",
                    unsafe_allow_html=True)

        classes = sorted(set(v.get('asset_class', 'Unknown') for v in ASSET_INFO.values()))
        selected_class = st.selectbox(t("filter_type", lang), [t("filter_all", lang)] + classes)

        st.markdown("---")

        for ticker, info in ASSET_INFO.items():
            if selected_class != t("filter_all", lang) and info.get("asset_class") != selected_class:
                continue
            render_asset_card(ticker, lang)

    # ─────────────────────────────────────────────────────────────────────────
    # DASHBOARD PAGE
    # ─────────────────────────────────────────────────────────────────────────
    elif page == "dashboard":
        is_real_mode = st.session_state.analysis_mode == "real"

        if st.session_state.current_portfolio is None:
            st.title("Dashboard" if lang == 'en' else "Tableau de Bord")
            if is_real_mode:
                hint = ("Enter your holdings in the Real Portfolio page to get started."
                        if lang == 'en' else
                        "Entrez vos positions dans la page Portefeuille Réel pour commencer.")
                st.info(hint)
                if st.button(t("real_portfolio", lang), type="primary"):
                    st.session_state.page = "real_portfolio"
                    st.rerun()
            else:
                st.info(t("welcome", lang))
                if st.button(t("create_portfolio", lang), type="primary"):
                    st.session_state.page = "new_analysis"
                    st.rerun()
        else:
            analyzer = st.session_state.current_portfolio
            metrics    = analyzer.calculate_metrics()
            robustness = analyzer.calculate_robustness_index()

            # ── Page header
            n_assets = len(analyzer.tickers)
            tickers_preview = ", ".join(analyzer.tickers[:4]) + ("…" if n_assets > 4 else "")
            sub_info = (
                f"{n_assets} assets · {tickers_preview}"
                if lang == 'en' else
                f"{n_assets} actifs · {tickers_preview}"
            )
            dash_title = (
                ("Real Portfolio Dashboard" if lang == 'en' else "Tableau de Bord — Portefeuille Réel")
                if is_real_mode else
                ("Portfolio Dashboard" if lang == 'en' else "Tableau de Bord")
            )
            st.markdown(f"""
            <div style="margin-bottom:6px;">
              <h1 style="font-size:1.9rem;font-weight:900;color:#f1f5f9;letter-spacing:-0.03em;margin:0;">
                {dash_title}
              </h1>
              <p style="color:#475569;font-size:0.85rem;margin:4px 0 0;">{sub_info}</p>
            </div>
            """, unsafe_allow_html=True)

            ft_divider()

            # ── Real Portfolio value cards (only in real mode)
            if is_real_mode and st.session_state.real_portfolio_total_value:
                total_val = st.session_state.real_portfolio_total_value
                prices = st.session_state.real_portfolio_prices
                holdings = st.session_state.real_portfolio_holdings

                # Compute per-asset values
                asset_values = {}
                for tk in analyzer.tickers:
                    if tk in prices and tk in holdings:
                        asset_values[tk] = prices[tk] * holdings[tk]

                # Find top asset
                top_ticker = max(asset_values, key=asset_values.get) if asset_values else "—"
                top_info = ASSET_INFO.get(top_ticker, {})
                top_name = top_info.get("name", top_ticker)
                top_pct = (asset_values.get(top_ticker, 0) / total_val * 100) if total_val > 0 else 0

                # Health/robustness score
                health_score = robustness['total']

                section_header(
                    "💰",
                    t("real_portfolio", lang),
                    "Live portfolio value from your actual holdings" if lang == 'en'
                    else "Valeur en temps réel de vos positions",
                )

                vc1, vc2, vc3, vc4 = st.columns(4)
                with vc1:
                    st.markdown(f"""
                    <div class="kpi-card">
                      <div class="kpi-label">{t("total_value", lang)}</div>
                      <div class="kpi-value" style="color:#00d4ff;">${total_val:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with vc2:
                    st.markdown(f"""
                    <div class="kpi-card">
                      <div class="kpi-label">{t("num_assets", lang)}</div>
                      <div class="kpi-value" style="color:#a5b4fc;">{n_assets}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with vc3:
                    st.markdown(f"""
                    <div class="kpi-card">
                      <div class="kpi-label">{t("top_asset", lang)}</div>
                      <div class="kpi-value" style="color:#10b981;font-size:1.3rem;">{top_name}</div>
                      <div style="font-size:0.75rem;color:#475569;margin-top:2px;">{top_pct:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                with vc4:
                    h_color = "#10b981" if health_score >= 70 else "#f59e0b" if health_score >= 40 else "#ff4d4d"
                    st.markdown(f"""
                    <div class="kpi-card">
                      <div class="kpi-label">{t("portfolio_health", lang)}</div>
                      <div class="kpi-value" style="color:{h_color};">{health_score:.0f}/100</div>
                    </div>
                    """, unsafe_allow_html=True)

                ft_divider()

                # ── Holdings detail table
                section_header(
                    "📋",
                    t("real_holdings", lang),
                    "Breakdown of each position" if lang == 'en' else "Détail de chaque position",
                )

                # Table header
                hdr_cols = st.columns([2, 1.5, 1.5, 1.5, 1])
                with hdr_cols[0]:
                    st.markdown(f"**{t('ticker', lang)}**")
                with hdr_cols[1]:
                    st.markdown(f"**{t('quantity', lang)}**")
                with hdr_cols[2]:
                    st.markdown(f"**{t('price', lang)}**")
                with hdr_cols[3]:
                    st.markdown(f"**{t('value', lang)}**")
                with hdr_cols[4]:
                    st.markdown(f"**{t('weight_pct', lang)}**")

                for tk in analyzer.tickers:
                    if tk not in asset_values:
                        continue
                    qty = holdings.get(tk, 0)
                    price = prices.get(tk, 0)
                    val = asset_values[tk]
                    wt = (val / total_val * 100) if total_val > 0 else 0
                    tk_info = ASSET_INFO.get(tk, {})
                    tk_name = tk_info.get("name", tk)

                    row_cols = st.columns([2, 1.5, 1.5, 1.5, 1])
                    with row_cols[0]:
                        st.markdown(f"**{tk}** — {tk_name}" if tk_name != tk else f"**{tk}**")
                    with row_cols[1]:
                        st.write(f"{qty:,.4f}")
                    with row_cols[2]:
                        st.write(f"${price:,.2f}")
                    with row_cols[3]:
                        st.write(f"${val:,.2f}")
                    with row_cols[4]:
                        st.write(f"{wt:.1f}%")

                ft_divider()

                # ── Normalized historical chart (portfolio value scaled to actual value)
                section_header(
                    "📈",
                    "Portfolio Value History" if lang == 'en' else "Historique de Valeur du Portefeuille",
                    "Historical performance normalized to your current portfolio value"
                    if lang == 'en' else
                    "Performance historique normalisée à la valeur actuelle de votre portefeuille",
                )

                # Normalize: scale cumulative returns so that last value = total_val
                cumulative = (1 + analyzer.portfolio_returns).cumprod()
                if cumulative.iloc[-1] != 0:
                    normalized_values = total_val * (cumulative / cumulative.iloc[-1])
                else:
                    normalized_values = cumulative

                CHART_LAYOUT = dict(
                    height=440,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter, sans-serif', size=12, color='#94a3b8'),
                    margin=dict(l=10, r=10, t=48, b=10),
                    hovermode='x unified',
                    hoverlabel=dict(bgcolor='#1c2333', bordercolor='rgba(0,212,255,0.3)',
                                    font=dict(color='#f1f5f9', size=12)),
                )
                AXIS_STYLE = dict(
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.04)',
                    gridwidth=1,
                    linecolor='rgba(255,255,255,0.06)',
                    tickfont=dict(size=11, color='#475569'),
                    zerolinecolor='rgba(255,255,255,0.05)',
                )

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=normalized_values.index,
                    y=normalized_values.values,
                    mode='lines',
                    name=t("total_value", lang),
                    line=dict(color='#00d4ff', width=2.5),
                    fill='tozeroy',
                    fillcolor='rgba(0,212,255,0.06)',
                    hovertemplate='<b>%{x|%b %d, %Y}</b><br>$%{y:,.0f}<extra></extra>',
                ))
                fig.update_layout(
                    title=dict(
                        text="Portfolio Value" if lang == 'en' else "Valeur du Portefeuille",
                        font=dict(size=14, color='#e2e8f0', family='Inter'),
                    ),
                    yaxis=dict(tickprefix="$", **AXIS_STYLE),
                    xaxis=AXIS_STYLE,
                    **CHART_LAYOUT,
                )
                st.plotly_chart(fig, use_container_width=True)

                ft_divider()

                # ── Synthesis section
                section_header(
                    "🔎",
                    t("real_synthesis", lang),
                    "Asset class breakdown, diversification & risk"
                    if lang == 'en' else
                    "Répartition par classe d'actifs, diversification et risque",
                )

                # Asset class breakdown
                class_alloc = {}
                for tk in analyzer.tickers:
                    ac = ASSET_INFO.get(tk, {}).get("asset_class",
                         SECTOR_MAPPING.get(tk, "Unknown"))
                    wt = analyzer.weights.get(tk, 0)
                    class_alloc[ac] = class_alloc.get(ac, 0) + wt

                syn_c1, syn_c2 = st.columns(2)

                with syn_c1:
                    st.markdown(f"**{t('asset_class_breakdown', lang)}**")
                    palette = ['#00d4ff','#4f46e5','#00ff9c','#ffb020','#ff4d4d',
                               '#818cf8','#34d399','#fbbf24']
                    fig_ac = go.Figure(data=[go.Pie(
                        labels=list(class_alloc.keys()),
                        values=[v * 100 for v in class_alloc.values()],
                        hole=0.50,
                        marker=dict(colors=palette, line=dict(color='#0e1117', width=2)),
                        textinfo='label+percent',
                        textfont=dict(size=11, color='white'),
                        hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>',
                    )])
                    fig_ac.update_layout(
                        showlegend=False,
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Inter, sans-serif', color='#94a3b8'),
                        height=300, margin=dict(l=10, r=10, t=10, b=10),
                    )
                    st.plotly_chart(fig_ac, use_container_width=True)

                with syn_c2:
                    # Dominant asset
                    st.markdown(f"**{t('dominant_asset', lang)}**")
                    st.markdown(
                        f"<div style='background:rgba(0,212,255,0.06);border:1px solid rgba(0,212,255,0.12);"
                        f"border-radius:10px;padding:12px 16px;margin-bottom:12px;'>"
                        f"<div style='font-size:1.1rem;font-weight:700;color:#00d4ff;'>"
                        f"{top_name} ({top_ticker})</div>"
                        f"<div style='font-size:0.82rem;color:#64748b;'>{top_pct:.1f}% "
                        f"{'of portfolio' if lang == 'en' else 'du portefeuille'}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    # Diversification level
                    n_classes = len(class_alloc)
                    max_weight = max(analyzer.weights.values()) if analyzer.weights else 0
                    if n_classes >= 4 and max_weight < 0.30:
                        div_level = t("high_div", lang)
                        div_color = "#10b981"
                    elif n_classes >= 3 and max_weight < 0.45:
                        div_level = t("medium_div", lang)
                        div_color = "#f59e0b"
                    elif n_classes >= 2 and max_weight < 0.60:
                        div_level = t("low_div", lang)
                        div_color = "#ff8c00"
                    else:
                        div_level = t("very_low_div", lang)
                        div_color = "#ff4d4d"

                    st.markdown(f"**{t('diversification', lang)}**")
                    st.markdown(
                        f"<div style='display:inline-block;background:{div_color}22;color:{div_color};"
                        f"padding:4px 16px;border-radius:10px;font-size:0.9rem;font-weight:600;'>"
                        f"{div_level}</div>",
                        unsafe_allow_html=True,
                    )

                    # Overall risk
                    risk_levels = {"Low": 1, "Medium": 2, "Medium-High": 3, "High": 4, "Very High": 5}
                    total_risk_score = 0
                    total_w_risk = 0
                    for tk in analyzer.tickers:
                        rl = ASSET_INFO.get(tk, {}).get("risk_level", "Medium")
                        w = analyzer.weights.get(tk, 0)
                        total_risk_score += risk_levels.get(rl, 3) * w
                        total_w_risk += w

                    avg_risk = total_risk_score / total_w_risk if total_w_risk > 0 else 3
                    if avg_risk <= 1.5:
                        risk_label = "Low" if lang == 'en' else "Faible"
                        risk_color = "#10b981"
                    elif avg_risk <= 2.5:
                        risk_label = "Medium" if lang == 'en' else "Moyen"
                        risk_color = "#f59e0b"
                    elif avg_risk <= 3.5:
                        risk_label = "Medium-High" if lang == 'en' else "Moyen-Élevé"
                        risk_color = "#ff8c00"
                    else:
                        risk_label = "High" if lang == 'en' else "Élevé"
                        risk_color = "#ff4d4d"

                    st.markdown(f"**{t('overall_risk', lang)}**")
                    st.markdown(
                        f"<div style='display:inline-block;background:{risk_color}22;color:{risk_color};"
                        f"padding:4px 16px;border-radius:10px;font-size:0.9rem;font-weight:600;'>"
                        f"{risk_label}</div>",
                        unsafe_allow_html=True,
                    )

                ft_divider()

            # ── Section 1: KPI cards
            section_header(
                "⚡",
                "Key Performance Indicators" if lang == 'en' else "Indicateurs Clés de Performance",
                "Live metrics from your portfolio" if lang == 'en' else "Métriques en temps réel",
            )
            render_kpi_cards(metrics, lang)
            render_metric_tooltips(lang)

            ft_divider()

            # ── Section 2: Robustness Index
            section_header(
                "🛡️",
                "Robustness Index" if lang == 'en' else "Indice de Robustesse",
                "Multi-factor portfolio quality breakdown" if lang == 'en'
                else "Score de qualité multi-facteurs",
            )
            rob_col, gauge_col = st.columns([1.6, 1], gap="large")
            with rob_col:
                render_robustness_score(robustness, lang)
            with gauge_col:
                render_health_gauge(robustness['total'], lang)

            ft_divider()

            # ── Section 3: Auto summary
            section_header(
                "📋",
                t('portfolio_summary', lang),
                "AI-generated overview of your portfolio" if lang == 'en'
                else "Synthèse automatique de votre portefeuille",
            )
            summary_text = analyzer.generate_auto_summary(lang)
            import re as _re
            summary_html = _re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#e2e8f0;">\1</strong>', summary_text)
            st.markdown(f"""
            <div style="background:rgba(0,212,255,0.04);border:1px solid rgba(0,212,255,0.12);
                 border-radius:14px;padding:20px 24px;line-height:1.9;color:#94a3b8;font-size:0.93rem;">
              {summary_html}
            </div>
            """, unsafe_allow_html=True)

            ft_divider()

            # ── Section 4: Charts
            section_header(
                "📊",
                "Portfolio Analytics" if lang == 'en' else "Analyses du Portefeuille",
                "Performance, allocation & risk over time" if lang == 'en'
                else "Performance, allocation et risque dans le temps",
            )
            render_enhanced_charts(analyzer, lang)

            ft_divider()

            # ── Section 5: AI Recommendations
            section_header(
                "🤖",
                t('recommendations', lang),
                "Personalised suggestions based on your profile" if lang == 'en'
                else "Suggestions personnalisées selon votre profil",
            )
            suggestions = analyzer.generate_improvement_suggestions(lang)
            profile_suggestions = analyzer.generate_profile_adapted_suggestions(lang)
            render_improvement_suggestions(suggestions + profile_suggestions, lang)

            ft_divider()

            # ── Section 6: Stress tests
            section_header(
                "🔥",
                t('stress_test', lang),
                "Simulate historical crisis scenarios" if lang == 'en'
                else "Simuler des scénarios de crise historiques",
            )
            if limits['can_stress_test']:
                if st.button(t("run_stress", lang), type="primary"):
                    with st.spinner("Running stress tests…" if lang == 'en' else "Calcul des stress tests…"):
                        stress_results = analyzer.stress_test_scenarios()
                    render_stress_test_results(stress_results, lang)
            else:
                render_paywall(t("stress_test", lang), lang)

            ft_divider()

            # ── Section 7: Asset details
            section_header(
                "🔍",
                t('asset_info', lang),
                "Detailed breakdown of each asset in your portfolio" if lang == 'en'
                else "Détail de chaque actif dans votre portefeuille",
            )
            for ticker in analyzer.tickers:
                render_asset_card(ticker, lang, show_weight=analyzer.weights.get(ticker))

    # ─────────────────────────────────────────────────────────────────────────
    # NEW ANALYSIS PAGE
    # ─────────────────────────────────────────────────────────────────────────
    elif page == "new_analysis":
        title = t('new_analysis', lang)
        st.title(title)

        max_assets = limits['max_assets']
        current_count = len(st.session_state.selected_tickers)

        if tier == 'free' and current_count >= max_assets:
            st.warning(
                f"Free plan: up to {max_assets} assets. Upgrade to Pro for up to 50."
                if lang == 'en' else
                f"Plan Free : jusqu'à {max_assets} actifs. Passez à Pro pour 50."
            )

        tabs = st.tabs([t("search", lang), t("browse", lang)])

        with tabs[0]:
            search = st.text_input(
                t("search", lang),
                placeholder=t("search_ph", lang),
                label_visibility="collapsed"
            )
            if search:
                all_assets = {}
                for cat, assets in POPULAR_ASSETS.items():
                    for name, ticker in assets.items():
                        all_assets[f"{name} ({ticker})"] = ticker

                matches = {k: v for k, v in all_assets.items() if search.lower() in k.lower()}
                if not matches:
                    st.caption("No matches found. You can still type a ticker directly (e.g. NFLX).")
                    direct_ticker = search.upper().strip()
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"{direct_ticker}")
                    with col2:
                        if st.button(t("add", lang), key=f"direct_{direct_ticker}"):
                            if direct_ticker not in st.session_state.selected_tickers:
                                if len(st.session_state.selected_tickers) < max_assets:
                                    st.session_state.selected_tickers.append(direct_ticker)
                                    auto_rebalance_weights()
                                    st.rerun()

                for display, ticker in list(matches.items())[:12]:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.write(display)
                    with col2:
                        in_port = ticker in st.session_state.selected_tickers
                        add_label = (t("add", lang) + " \u2713") if in_port else t("add", lang)
                        if not in_port and st.button(add_label, key=f"sa_{ticker}"):
                            if len(st.session_state.selected_tickers) < max_assets:
                                st.session_state.selected_tickers.append(ticker)
                                auto_rebalance_weights()
                                st.rerun()

        with tabs[1]:
            for category, assets in POPULAR_ASSETS.items():
                st.markdown(f"**{category}**")
                cols = st.columns(4)
                for i, (name, ticker) in enumerate(assets.items()):
                    with cols[i % 4]:
                        in_port = ticker in st.session_state.selected_tickers
                        btn_label = f"{ticker}" + (" ✓" if in_port else "")
                        if not in_port and st.button(
                            btn_label, key=f"pop_{ticker}", use_container_width=True
                        ):
                            if len(st.session_state.selected_tickers) < max_assets:
                                st.session_state.selected_tickers.append(ticker)
                                auto_rebalance_weights()
                                st.rerun()
                st.markdown("")

        # Selected assets & weights
        st.markdown("---")
        st.markdown(f"### {t('selected_assets', lang)}")

        if st.session_state.selected_tickers:
            new_weights = {}
            n = len(st.session_state.selected_tickers)
            cols_per_row = min(n, 4)
            cols = st.columns(cols_per_row)

            for i, ticker in enumerate(st.session_state.selected_tickers):
                with cols[i % cols_per_row]:
                    cur_w = st.session_state.weights.get(ticker, 1.0 / n)
                    w = st.slider(ticker, 0.0, 100.0, step=1.0, key=f"ws_{ticker}")
                    new_weights[ticker] = w / 100
                    if st.button(t("remove", lang), key=f"rm_{ticker}", use_container_width=True):
                        st.session_state.selected_tickers.remove(ticker)
                        auto_rebalance_weights()
                        st.rerun()

            st.session_state.weights = new_weights
            total_w = sum(new_weights.values())
            if total_w <= 0:
                st.warning("All weights are 0 — please adjust the sliders." if lang == 'en'
                           else "Tous les poids sont à 0 — ajustez les curseurs.")
            elif abs(total_w - 1.0) > 0.01:
                st.session_state.weights = {k: v / total_w for k, v in new_weights.items()}
                st.warning(f"{t('total_weight', lang)}: {total_w*100:.1f}% — {t('normalised', lang)}")
            else:
                st.success(f"{t('total_weight', lang)}: {total_w*100:.1f}%")

            if st.button(t("analyse_btn", lang), type="primary", use_container_width=False):
                with st.spinner(t("loading", lang)):
                    analyzer = UltimatePortfolioAnalyzer(
                        st.session_state.selected_tickers,
                        st.session_state.weights,
                        (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
                        user_profile=st.session_state.user_profile
                    )
                    if _fetch_with_progress(analyzer):
                        st.session_state.current_portfolio = analyzer
                        st.success(t("analysis_done", lang))
                        st.session_state.page = "overview"
                        st.rerun()
                    else:
                        st.error(t("fetch_error", lang))
        else:
            st.info(t("welcome", lang))

        # Show upgrade banner if near limit
        if tier == 'free' and current_count >= max_assets - 1:
            render_upgrade_prompt(lang)

    # ─────────────────────────────────────────────────────────────────────────
    # MODEL PORTFOLIOS PAGE
    # ─────────────────────────────────────────────────────────────────────────
    elif page == "models":
        title = t('models', lang)
        st.title(title)

        if tier == 'free':
            preview_note = (
                "Model portfolios are available on the **Pro** plan. "
                "Here is a preview — upgrade to use them."
                if lang == 'en' else
                "Les portefeuilles modèles sont disponibles sur le plan **Pro**. "
                "Voici un aperçu — passez à Pro pour les utiliser."
            )
            st.info(preview_note)

        for model_name, model_data in MODEL_PORTFOLIOS.items():
            ret_pct = model_data['expected_return'] * 100
            vol_pct = model_data['expected_volatility'] * 100
            desc_key = "description_fr" if lang == 'fr' else "description_en"
            description = model_data.get(desc_key, model_data.get("description_en", ""))

            if tier == 'pro':
                alloc_html = "".join(
                    f"<span style='display:inline-block;background:rgba(99,102,241,0.15);border-radius:8px;"
                    f"padding:3px 10px;font-size:0.78rem;font-weight:600;color:#a5b4fc;"
                    f"margin:3px;border:1px solid rgba(99,102,241,0.2);'>{tk} {w*100:.0f}%</span>"
                    for tk, w in model_data['allocation'].items()
                )
            else:
                n = len(model_data['allocation'])
                locked_label = "assets" if lang == 'en' else "actifs"
                alloc_html = (
                    f"<span style='display:inline-block;background:rgba(99,102,241,0.08);border-radius:8px;"
                    f"padding:3px 14px;font-size:0.78rem;font-weight:600;color:#64748b;"
                    f"margin:3px;border:1px solid rgba(99,102,241,0.15);filter:blur(0px);'>"
                    f"🔒 {n} {locked_label} — Pro</span>"
                )
            ret_label = t("expected_return", lang)
            vol_label = t("volatility", lang)

            st.markdown(f"""
            <div class="model-card">
              <div style="font-size:1.05rem;font-weight:700;color:#f1f5f9;margin-bottom:5px;">{model_name}</div>
              <div style="font-size:0.84rem;color:#64748b;margin-bottom:16px;line-height:1.5;">{description}</div>
              <div style="display:flex;gap:28px;margin-bottom:16px;flex-wrap:wrap;">
                <div>
                  <div style="font-size:0.68rem;color:#4b5563;text-transform:uppercase;font-weight:600;
                              letter-spacing:0.07em;margin-bottom:3px;">{ret_label}</div>
                  <div style="font-size:1.4rem;font-weight:800;color:#10b981;">+{ret_pct:.0f}%</div>
                </div>
                <div>
                  <div style="font-size:0.68rem;color:#4b5563;text-transform:uppercase;font-weight:600;
                              letter-spacing:0.07em;margin-bottom:3px;">{vol_label}</div>
                  <div style="font-size:1.4rem;font-weight:800;color:#f59e0b;">{vol_pct:.0f}%</div>
                </div>
              </div>
              <div style="margin-bottom:4px;">{alloc_html}</div>
            </div>
            """, unsafe_allow_html=True)

            if tier == 'pro':
                use_label = t("use_model", lang)
                if st.button(use_label, key=f"use_{model_name}", use_container_width=False):
                    st.session_state.selected_tickers = list(model_data['allocation'].keys())
                    st.session_state.weights = model_data['allocation'].copy()
                    # sync slider states
                    for tk, w in model_data['allocation'].items():
                        st.session_state[f"ws_{tk}"] = round(w * 100, 1)
                    with st.spinner("Loading..." if lang == 'en' else "Chargement..."):
                        analyzer = UltimatePortfolioAnalyzer(
                            list(model_data['allocation'].keys()),
                            model_data['allocation'],
                            (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
                            user_profile=model_data['profile']
                        )
                        if _fetch_with_progress(analyzer):
                            st.session_state.current_portfolio = analyzer
                            ok_msg = f"{model_name} loaded!" if lang == 'en' else f"{model_name} chargé !"
                            st.success(ok_msg)
                            st.session_state.page = "overview"
                            st.rerun()
            else:
                locked_msg = "Pro plan required" if lang == 'en' else "Plan Pro requis"
                st.caption(f"🔒 {locked_msg}")

            st.markdown("")

    # ─────────────────────────────────────────────────────────────────────────
    # REAL PORTFOLIO PAGE
    # ─────────────────────────────────────────────────────────────────────────
    elif page == "real_portfolio":
        st.title(t("real_portfolio", lang))
        st.markdown(
            f"<p style='color:#64748b;margin-top:-12px;'>{t('real_portfolio_desc', lang)}</p>",
            unsafe_allow_html=True,
        )

        holdings = st.session_state.real_portfolio_holdings  # {ticker: qty}

        # ── Add holding form
        st.markdown(f"### {t('add_holding', lang)}")
        add_col1, add_col2, add_col3 = st.columns([3, 2, 1])
        with add_col1:
            # Search from POPULAR_ASSETS + direct ticker entry
            all_assets_flat = {}
            for cat, assets in POPULAR_ASSETS.items():
                for name, ticker in assets.items():
                    all_assets_flat[f"{name} ({ticker})"] = ticker
            rp_search = st.text_input(
                t("ticker", lang),
                placeholder=t("search_ph", lang),
                key="rp_search_input",
                label_visibility="collapsed",
            )
        with add_col2:
            rp_qty = st.number_input(
                t("quantity", lang),
                min_value=0.0001,
                value=1.0,
                step=0.1,
                format="%.4f",
                key="rp_qty_input",
            )
        with add_col3:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            add_clicked = st.button(t("add_holding", lang), key="rp_add_btn", type="primary",
                                    use_container_width=True)

        # Search results
        if rp_search:
            matches = {k: v for k, v in all_assets_flat.items() if rp_search.lower() in k.lower()}
            if matches:
                for display, ticker in list(matches.items())[:6]:
                    mc1, mc2 = st.columns([5, 1])
                    with mc1:
                        st.write(display)
                    with mc2:
                        if ticker not in holdings:
                            if st.button(t("add", lang), key=f"rp_sa_{ticker}"):
                                holdings[ticker] = rp_qty
                                st.session_state.real_portfolio_holdings = holdings
                                st.rerun()
                        else:
                            st.caption("✓")
            else:
                # Allow direct ticker entry
                direct = rp_search.upper().strip()
                if add_clicked and direct:
                    holdings[direct] = rp_qty
                    st.session_state.real_portfolio_holdings = holdings
                    st.rerun()
                st.caption(
                    f"No matches. Press '{t('add_holding', lang)}' to add **{direct}** directly."
                    if lang == 'en' else
                    f"Aucun résultat. Appuyez sur '{t('add_holding', lang)}' pour ajouter **{direct}** directement."
                )
        elif add_clicked:
            st.warning("Enter a ticker symbol." if lang == 'en' else "Entrez un symbole ticker.")

        st.markdown("---")

        # ── Current holdings table
        if holdings:
            st.markdown(f"### {t('real_holdings', lang)}")

            h_cols = st.columns([2, 2, 1])
            with h_cols[0]:
                st.markdown(f"**{t('ticker', lang)}**")
            with h_cols[1]:
                st.markdown(f"**{t('quantity', lang)}**")
            with h_cols[2]:
                st.markdown("")

            for ticker in list(holdings.keys()):
                rc1, rc2, rc3 = st.columns([2, 2, 1])
                with rc1:
                    info = ASSET_INFO.get(ticker, {})
                    name = info.get("name", ticker)
                    st.markdown(f"**{ticker}** — {name}" if name != ticker else f"**{ticker}**")
                with rc2:
                    new_qty = st.number_input(
                        t("quantity", lang),
                        min_value=0.0001,
                        value=float(holdings[ticker]),
                        step=0.1,
                        format="%.4f",
                        key=f"rp_qty_{ticker}",
                        label_visibility="collapsed",
                    )
                    holdings[ticker] = new_qty
                with rc3:
                    if st.button(t("remove_holding", lang), key=f"rp_rm_{ticker}", use_container_width=True):
                        del holdings[ticker]
                        st.session_state.real_portfolio_holdings = holdings
                        st.rerun()

            st.session_state.real_portfolio_holdings = holdings

            st.markdown("---")

            # ── Fetch prices & analyse
            if st.button(t("fetch_prices", lang), type="primary", use_container_width=False):
                tickers_list = list(holdings.keys())
                prices = {}
                progress_bar = st.progress(0)
                status = st.empty()

                for i, ticker in enumerate(tickers_list):
                    try:
                        status.text(f"Loading {ticker}...")
                        tk = yf.Ticker(ticker)
                        hist = tk.history(period="5d")
                        if not hist.empty:
                            prices[ticker] = hist['Close'].iloc[-1]
                    except Exception as e:
                        st.warning(f"{ticker}: {str(e)[:50]}")
                    progress_bar.progress((i + 1) / len(tickers_list))

                status.empty()
                progress_bar.empty()

                if not prices:
                    st.error(t("fetch_error", lang))
                else:
                    st.session_state.real_portfolio_prices = prices

                    # Calculate total value and weights
                    asset_values = {}
                    for ticker in tickers_list:
                        if ticker in prices:
                            asset_values[ticker] = prices[ticker] * holdings[ticker]

                    total_value = sum(asset_values.values())
                    st.session_state.real_portfolio_total_value = total_value

                    # Calculate weights from real values
                    real_weights = {tk: val / total_value for tk, val in asset_values.items() if total_value > 0}
                    available_tickers = list(real_weights.keys())

                    # Store in session state for the dashboard to use
                    st.session_state.selected_tickers = available_tickers
                    st.session_state.weights = real_weights

                    # Create analyzer with real weights
                    analyzer = UltimatePortfolioAnalyzer(
                        available_tickers,
                        real_weights,
                        (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
                        initial_value=total_value,
                        user_profile=st.session_state.user_profile,
                    )
                    if _fetch_with_progress(analyzer):
                        st.session_state.current_portfolio = analyzer
                        st.success(t("analysis_done", lang))
                        st.session_state.page = "overview"
                        st.rerun()
                    else:
                        st.error(t("fetch_error", lang))
        else:
            st.info(t("no_holdings", lang))

    # ─────────────────────────────────────────────────────────────────────────
    # IMPROVE / OPTIMISE PAGE
    # ─────────────────────────────────────────────────────────────────────────
    elif page == "improve":
        title = t('improve', lang)
        st.title(title)

        if st.session_state.current_portfolio is None:
            hint = "Create a portfolio first to see optimisation suggestions." if lang == 'en' \
                   else "Créez d'abord un portefeuille pour voir les suggestions d'optimisation."
            st.info(hint)
        else:
            analyzer = st.session_state.current_portfolio
            metrics = analyzer.calculate_metrics()

            cur_label = "Current Portfolio" if lang == 'en' else "Portefeuille Actuel"
            st.markdown(f"### {cur_label}")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Sharpe", f"{metrics['sharpe']:.2f}")
            with c2: st.metric("Annual Return", f"{metrics['annual_return']*100:.1f}%")
            with c3: st.metric("Volatility", f"{metrics['volatility']*100:.1f}%")
            with c4: st.metric("Max Drawdown", f"{metrics['max_drawdown']*100:.1f}%")

            st.markdown("---")

            if not limits['can_optimize']:
                render_paywall(
                    "Portfolio Optimisation" if lang == 'en' else "Optimisation du Portefeuille",
                    lang
                )
            else:
                opt_label = "Optimise Portfolio" if lang == 'en' else "Optimiser le Portefeuille"
                if st.button(opt_label, type="primary", use_container_width=False):
                    with st.spinner("Optimising..." if lang == 'en' else "Optimisation en cours..."):
                        st.session_state.optimal_result = analyzer.optimize_portfolio()

                optimal = st.session_state.get("optimal_result")
                if optimal:
                    opt_result_label = "Optimised Portfolio" if lang == 'en' else "Portefeuille Optimisé"
                    st.markdown(f"### {opt_result_label}")

                    col_cur, col_opt = st.columns(2)
                    with col_cur:
                        cur_h = "Current" if lang == 'en' else "Actuel"
                        st.markdown(f"**{cur_h}**")
                        st.metric("Sharpe", f"{metrics['sharpe']:.2f}")
                        for tk, w in analyzer.weights.items():
                            st.write(f"{tk}: {w*100:.1f}%")

                    with col_opt:
                        opt_h = "Optimised" if lang == 'en' else "Optimisé"
                        st.markdown(f"**{opt_h}**")
                        if metrics['sharpe'] != 0:
                            imp = ((optimal['sharpe'] / metrics['sharpe']) - 1) * 100
                            st.metric("Sharpe", f"{optimal['sharpe']:.2f}", f"+{imp:.1f}%")
                        else:
                            st.metric("Sharpe", f"{optimal['sharpe']:.2f}")
                        for tk, w in optimal['weights'].items():
                            st.write(f"{tk}: {w*100:.1f}%")

                    st.markdown("---")
                    apply_label = "Apply Optimisation" if lang == 'en' else "Appliquer l'Optimisation"
                    if st.button(apply_label, use_container_width=False):
                        new_a = UltimatePortfolioAnalyzer(
                            list(optimal['weights'].keys()),
                            optimal['weights'],
                            analyzer.start_date,
                            user_profile=st.session_state.user_profile
                        )
                        if _fetch_with_progress(new_a):
                            st.session_state.current_portfolio = new_a
                            st.session_state.weights = optimal['weights']
                            st.session_state.optimal_result = None
                            done_msg = "Optimisation applied!" if lang == 'en' else "Optimisation appliquée !"
                            st.success(done_msg)
                            st.rerun()


if __name__ == "__main__":
    main()
