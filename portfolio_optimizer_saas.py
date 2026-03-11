"""
Portfolio Health Pro v4.0
Professional Portfolio Analysis Platform

v4.0 — UI/UX overhaul, Health Score, Stripe subscriptions, 35+ asset library
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from scipy.optimize import minimize
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# STRIPE / SUBSCRIPTION CONFIGURATION
# =============================================================================

STRIPE_CONFIG = {
    'payment_link': os.getenv('STRIPE_PAYMENT_LINK', ''),
    'pro_price_monthly': 9.99,
}

# Comma-separated emails with Pro access: PRO_EMAILS=alice@x.com,bob@y.com
PRO_EMAILS = set(
    e.strip().lower()
    for e in os.getenv('PRO_EMAILS', '').split(',')
    if e.strip()
)

TIER_LIMITS = {
    'free': {
        'max_assets': 5,
        'can_optimize': False,
        'can_stress_test': False,
        'label': 'Free',
    },
    'pro': {
        'max_assets': 50,
        'can_optimize': True,
        'can_stress_test': True,
        'label': 'Pro',
    },
}

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

# =============================================================================
# DATA: ASSET INFO, MODEL PORTFOLIOS, SECTORS
# =============================================================================

ASSET_INFO = {
    # ── US Large Cap Stocks ──────────────────────────────────────────────────
    # ── US Large Cap Stocks ──────────────────────────────────────────────────
    "AAPL": {
        "name": "Apple Inc.",
        "description": "The world's most valuable company by market cap. Designs and sells iPhones, Macs, iPads, and services (App Store, iCloud, Apple TV+). Revenue mix shifting toward high-margin recurring services.",
        "description_fr": "L'entreprise la plus valorisée au monde. Conçoit et vend iPhones, Macs, iPads et services (App Store, iCloud, Apple TV+). Revenus de plus en plus dominés par les services à haute marge.",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "Large-cap quality growth with expanding services moat",
        "utility_fr": "Croissance de qualité large-cap avec fort avantage concurrentiel services",
        "typical_use": "Core growth holding. 5–15% in balanced/growth portfolios.",
        "typical_use_fr": "Holding de croissance cœur. 5–15% dans les portefeuilles équilibrés/croissance.",
        "risk_level": "Medium-High", "liquidity": 100,
        "dividend_yield": "~0.5%", "market_cap": "~$3 billion",
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "description": "Global leader in cloud computing (Azure, #2 worldwide), enterprise software (Office 365, Teams), and gaming (Xbox, Activision). Benefits from AI integration across all product lines.",
        "description_fr": "Leader mondial du cloud (Azure, n°2 mondial), des logiciels d'entreprise (Office 365, Teams) et du gaming (Xbox, Activision). Bénéficie de l'intégration de l'IA dans toutes ses gammes.",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "Defensive tech with cloud and AI tailwinds",
        "utility_fr": "Tech défensive portée par le cloud et l'IA",
        "typical_use": "Defensive tech core holding. Pairs well with growth assets.",
        "typical_use_fr": "Position cœur tech défensive. Se marie bien avec des actifs de croissance.",
        "risk_level": "Medium", "liquidity": 100,
        "dividend_yield": "~0.7%", "market_cap": "~$3 trillion",
    },
    "GOOGL": {
        "name": "Alphabet (Google)",
        "description": "Parent company of Google Search (dominant ~90% market share), YouTube, Google Cloud, and Waymo. Advertising is the core revenue driver, diversified by fast-growing Cloud.",
        "description_fr": "Maison mère de Google Search (~90% de parts de marché), YouTube, Google Cloud et Waymo. La publicité est le moteur principal, diversifiée par le Cloud en forte croissance.",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "Search monopoly + cloud growth platform",
        "utility_fr": "Monopole de la recherche + plateforme cloud en croissance",
        "typical_use": "Growth or core holding. Diversifier from pure hardware tech.",
        "typical_use_fr": "Position de croissance ou cœur. Diversifie par rapport à la tech hardware.",
        "risk_level": "Medium", "liquidity": 100,
        "dividend_yield": "~0.5%", "market_cap": "~$2 trillion",
    },
    "AMZN": {
        "name": "Amazon",
        "description": "E-commerce giant and owner of AWS (Amazon Web Services), the world's leading cloud platform. AWS generates most of Amazon's profit despite being a fraction of revenue.",
        "description_fr": "Géant du e-commerce et propriétaire d'AWS (Amazon Web Services), la première plateforme cloud mondiale. AWS génère l'essentiel des bénéfices d'Amazon malgré une faible part du chiffre d'affaires.",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "E-commerce + cloud infrastructure dominance",
        "utility_fr": "Domination e-commerce + infrastructure cloud",
        "typical_use": "Growth portfolio core. Strong long-term compounding story.",
        "typical_use_fr": "Cœur de portefeuille croissance. Excellent historique de capitalisation long terme.",
        "risk_level": "Medium-High", "liquidity": 100,
        "dividend_yield": "0%", "market_cap": "~$2 trillion",
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "description": "Designs GPUs and AI chips. Dominant supplier of data center AI accelerators (H100, B200). Near-monopoly in AI training hardware, with expanding software (CUDA ecosystem).",
        "description_fr": "Conçoit des GPU et puces IA. Fournisseur dominant d'accélérateurs IA pour data centers (H100, B200). Quasi-monopole sur le matériel d'entraînement IA, avec l'écosystème logiciel CUDA.",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "Pure-play AI infrastructure exposure",
        "utility_fr": "Exposition pure à l'infrastructure IA",
        "typical_use": "High-conviction growth holding. High volatility, high reward.",
        "typical_use_fr": "Position de croissance forte conviction. Volatilité élevée, rendement élevé.",
        "risk_level": "High", "liquidity": 100,
        "dividend_yield": "~0.03%", "market_cap": "~$3 trillion",
    },
    "META": {
        "name": "Meta Platforms",
        "description": "Operates Facebook, Instagram, WhatsApp, and Threads — reaching 3+ billion daily users. Heavy AI investment in recommendation algorithms and Reality Labs (Quest VR headsets).",
        "description_fr": "Opère Facebook, Instagram, WhatsApp et Threads — atteignant 3 milliards+ d'utilisateurs quotidiens. Lourds investissements IA dans les algorithmes de recommandation et Reality Labs (casques VR Quest).",
        "sector": "Technology", "geography": "USA", "asset_class": "Stock",
        "utility": "Social media advertising dominance + AI-driven monetization",
        "utility_fr": "Domination publicité réseaux sociaux + monétisation pilotée par l'IA",
        "typical_use": "Growth holding. Strong cash generation and buybacks.",
        "typical_use_fr": "Position de croissance. Forte génération de trésorerie et rachats d'actions.",
        "risk_level": "Medium-High", "liquidity": 100,
        "dividend_yield": "~0.4%", "market_cap": "~$1.5 trillion",
    },
    "TSLA": {
        "name": "Tesla",
        "description": "Pioneer in electric vehicles and energy storage. Also developing autonomous driving (FSD), Robotaxi network, and Optimus humanoid robots. Highly valued for optionality.",
        "description_fr": "Pionnier des véhicules électriques et du stockage d'énergie. Développe aussi la conduite autonome (FSD), le réseau Robotaxi et les robots humanoïdes Optimus. Très valorisé pour ses options de croissance.",
        "sector": "Automotive", "geography": "USA", "asset_class": "Stock",
        "utility": "EV/autonomy/energy disruption play",
        "utility_fr": "Pari disruptif VE / autonomie / énergie",
        "typical_use": "Satellite holding in aggressive portfolios. Expect high volatility.",
        "typical_use_fr": "Position satellite dans les portefeuilles agressifs. Volatilité élevée attendue.",
        "risk_level": "Very High", "liquidity": 100,
        "dividend_yield": "0%", "market_cap": "~$800 billion",
    },
    "JPM": {
        "name": "JPMorgan Chase",
        "description": "America's largest bank by assets. Diversified across investment banking, consumer banking, asset management, and trading. Known for exceptional risk management and consistent profitability.",
        "description_fr": "La plus grande banque américaine par les actifs. Diversifiée en banque d'investissement, banque de détail, gestion d'actifs et trading. Reconnue pour sa gestion des risques et sa rentabilité constante.",
        "sector": "Financials", "geography": "USA", "asset_class": "Stock",
        "utility": "Financial sector exposure, income + stability",
        "utility_fr": "Exposition au secteur financier, revenus + stabilité",
        "typical_use": "Defensive income holding. Benefits from higher interest rates.",
        "typical_use_fr": "Position défensive de revenus. Bénéficie de la hausse des taux d'intérêt.",
        "risk_level": "Medium", "liquidity": 95,
        "dividend_yield": "~2.3%", "market_cap": "~$700 billion",
    },
    "JNJ": {
        "name": "Johnson & Johnson",
        "description": "Healthcare conglomerate spanning pharmaceuticals (Janssen), MedTech (surgical robots, orthopedics), and consumer health. Known as a 'Dividend King' with 60+ years of consecutive dividend increases.",
        "description_fr": "Conglomérat de santé couvrant la pharmacie (Janssen), le MedTech (robots chirurgicaux, orthopédie) et la santé grand public. 'Dividend King' avec 60+ ans d'augmentations consécutives.",
        "sector": "Healthcare", "geography": "USA", "asset_class": "Stock",
        "utility": "Defensive healthcare with reliable income",
        "utility_fr": "Santé défensive avec revenus fiables",
        "typical_use": "Defensive anchor for conservative portfolios.",
        "typical_use_fr": "Ancre défensive pour les portefeuilles conservateurs.",
        "risk_level": "Low-Medium", "liquidity": 95,
        "dividend_yield": "~3%", "market_cap": "~$400 billion",
    },
    "XOM": {
        "name": "ExxonMobil",
        "description": "One of the world's largest oil & gas companies. Integrated operations span exploration, refining, and chemicals. Strong free cash flow used for dividends and buybacks.",
        "description_fr": "L'un des plus grands groupes pétroliers et gaziers mondiaux. Opérations intégrées couvrant l'exploration, le raffinage et la chimie. Fort cash-flow libre reversé en dividendes et rachats d'actions.",
        "sector": "Energy", "geography": "USA", "asset_class": "Stock",
        "utility": "Energy sector and inflation hedge",
        "utility_fr": "Exposition au secteur énergie et couverture contre l'inflation",
        "typical_use": "Inflation hedge, income holding. Performs well in rising oil price environments.",
        "typical_use_fr": "Couverture inflation, revenu. Performe bien en période de hausse du pétrole.",
        "risk_level": "Medium", "liquidity": 95,
        "dividend_yield": "~3.5%", "market_cap": "~$450 billion",
    },
    "V": {
        "name": "Visa Inc.",
        "description": "The world's largest payment network. Processes billions of transactions globally. Asset-light, high-margin business model — earns a toll on every digital payment.",
        "description_fr": "Le plus grand réseau de paiement mondial. Traite des milliards de transactions. Modèle économique léger en actifs et à forte marge — perçoit un péage sur chaque paiement numérique.",
        "sector": "Financials", "geography": "USA", "asset_class": "Stock",
        "utility": "Global payments infrastructure, digital economy exposure",
        "utility_fr": "Infrastructure paiements mondiale, exposition à l'économie numérique",
        "typical_use": "Quality compounder for long-term growth portfolios.",
        "typical_use_fr": "Capitaliseur de qualité pour les portefeuilles de croissance long terme.",
        "risk_level": "Medium", "liquidity": 98,
        "dividend_yield": "~0.8%", "market_cap": "~$550 billion",
    },
    # ── US ETFs ──────────────────────────────────────────────────────────────
    "SPY": {
        "name": "SPDR S&P 500 ETF",
        "description": "The world's most traded ETF. Tracks the S&P 500 index — 500 largest US companies by market cap. Provides instant, low-cost exposure to American large-cap equities.",
        "description_fr": "L'ETF le plus échangé au monde. Réplique l'indice S&P 500 — les 500 plus grandes entreprises américaines. Offre une exposition instantanée et peu coûteuse aux actions américaines large-cap.",
        "sector": "Diversified", "geography": "USA", "asset_class": "ETF",
        "utility": "Core US large-cap equity exposure",
        "utility_fr": "Exposition cœur aux actions américaines large-cap",
        "typical_use": "Foundation of most diversified portfolios. 20–50% core holding.",
        "typical_use_fr": "Socle de la plupart des portefeuilles diversifiés. Position cœur de 20–50%.",
        "risk_level": "Medium", "liquidity": 100,
        "dividend_yield": "~1.3%", "market_cap": "~$500 billion AUM",
    },
    "QQQ": {
        "name": "Invesco Nasdaq 100 ETF",
        "description": "Tracks the 100 largest non-financial companies on the Nasdaq. Heavily concentrated in technology and growth stocks (Apple, Microsoft, NVIDIA, Amazon, Meta). Higher volatility than SPY.",
        "description_fr": "Réplique les 100 plus grandes entreprises non financières du Nasdaq. Fortement concentré en tech et croissance (Apple, Microsoft, NVIDIA, Amazon, Meta). Plus volatile que SPY.",
        "sector": "Technology-Heavy", "geography": "USA", "asset_class": "ETF",
        "utility": "Tech-focused growth exposure via index",
        "utility_fr": "Exposition croissance axée tech via indice",
        "typical_use": "Growth tilt, tech overweight. Complement to SPY.",
        "typical_use_fr": "Surpondération croissance/tech. Complément de SPY.",
        "risk_level": "Medium-High", "liquidity": 100,
        "dividend_yield": "~0.5%", "market_cap": "~$250 billion AUM",
    },
    "VTI": {
        "name": "Vanguard Total Market ETF",
        "description": "Broadest US equity ETF — tracks over 3,700 US stocks including small, mid, and large caps. More diversified than SPY. Ultra-low expense ratio (0.03%).",
        "description_fr": "L'ETF actions américaines le plus large — réplique 3 700+ titres US incluant petites, moyennes et grandes capitalisations. Plus diversifié que SPY. Frais ultra-faibles (0,03%).",
        "sector": "Diversified", "geography": "USA", "asset_class": "ETF",
        "utility": "Total US market exposure in one ticker",
        "utility_fr": "Exposition à l'ensemble du marché américain en un seul ticker",
        "typical_use": "Ultimate US equity core holding for long-term investors.",
        "typical_use_fr": "Position cœur actions américaines idéale pour les investisseurs long terme.",
        "risk_level": "Medium", "liquidity": 100,
        "dividend_yield": "~1.3%", "market_cap": "~$400 billion AUM",
    },
    "VOO": {
        "name": "Vanguard S&P 500 ETF",
        "description": "Vanguard's version of the S&P 500 tracker. Nearly identical holdings to SPY but with a lower expense ratio (0.03% vs 0.09%). Preferred by long-term buy-and-hold investors.",
        "description_fr": "La version Vanguard du tracker S&P 500. Composition quasi identique à SPY mais frais inférieurs (0,03% vs 0,09%). Préféré des investisseurs buy-and-hold long terme.",
        "sector": "Diversified", "geography": "USA", "asset_class": "ETF",
        "utility": "Low-cost S&P 500 exposure",
        "utility_fr": "Exposition S&P 500 à faible coût",
        "typical_use": "Core US equity holding, especially for tax-advantaged accounts.",
        "typical_use_fr": "Position cœur actions US, idéale pour les comptes fiscalement avantageux.",
        "risk_level": "Medium", "liquidity": 100,
        "dividend_yield": "~1.3%", "market_cap": "~$550 billion AUM",
    },
    "VXUS": {
        "name": "Vanguard Total International ETF",
        "description": "Tracks non-US stock markets — 7,000+ companies across developed (Europe, Japan, Canada) and emerging markets (China, India, Brazil). Essential for true global diversification.",
        "description_fr": "Réplique les marchés actions hors USA — 7 000+ entreprises dans les marchés développés (Europe, Japon, Canada) et émergents (Chine, Inde, Brésil). Indispensable pour une diversification mondiale.",
        "sector": "International Diversified", "geography": "Ex-US Global", "asset_class": "ETF",
        "utility": "Single-ticker access to all non-US equities",
        "utility_fr": "Accès en un seul ticker à toutes les actions hors USA",
        "typical_use": "International diversification — 20–40% of equity allocation.",
        "typical_use_fr": "Diversification internationale — 20–40% de l'allocation actions.",
        "risk_level": "Medium", "liquidity": 98,
        "dividend_yield": "~2.8%", "market_cap": "~$70 billion AUM",
    },
    "EFA": {
        "name": "iShares MSCI EAFE ETF",
        "description": "Tracks large and mid-cap stocks in developed markets outside the US: Europe, Australasia, and the Far East (Japan, UK, France, Germany, Switzerland). No emerging market exposure.",
        "description_fr": "Réplique les grandes et moyennes capitalisations des marchés développés hors USA : Europe, Australasie, Extrême-Orient (Japon, UK, France, Allemagne, Suisse). Pas d'exposition aux marchés émergents.",
        "sector": "International Developed", "geography": "Developed Ex-US", "asset_class": "ETF",
        "utility": "Developed market diversification (Europe + Asia)",
        "utility_fr": "Diversification marchés développés (Europe + Asie)",
        "typical_use": "Conservative international allocation. Lower vol than EEM.",
        "typical_use_fr": "Allocation internationale conservatrice. Moins volatile qu'EEM.",
        "risk_level": "Medium", "liquidity": 98,
        "dividend_yield": "~3%", "market_cap": "~$50 billion AUM",
    },
    "EEM": {
        "name": "iShares MSCI Emerging Markets ETF",
        "description": "Tracks large and mid-cap stocks in 24 emerging market countries. Top exposures: China, India, Taiwan, South Korea, Brazil. Higher growth potential, higher volatility.",
        "description_fr": "Réplique les grandes et moyennes caps dans 24 pays émergents. Principales expositions : Chine, Inde, Taïwan, Corée du Sud, Brésil. Potentiel de croissance élevé, volatilité élevée.",
        "sector": "Emerging Markets", "geography": "Emerging Markets", "asset_class": "ETF",
        "utility": "Emerging market growth exposure",
        "utility_fr": "Exposition à la croissance des marchés émergents",
        "typical_use": "Satellite allocation (5–15%) for return enhancement.",
        "typical_use_fr": "Allocation satellite (5–15%) pour améliorer les rendements.",
        "risk_level": "High", "liquidity": 97,
        "dividend_yield": "~2.5%", "market_cap": "~$20 billion AUM",
    },
    "VNQ": {
        "name": "Vanguard Real Estate ETF",
        "description": "Tracks US Real Estate Investment Trusts (REITs). Provides exposure to commercial real estate (offices, apartments, retail, industrial, data centers) without directly owning property.",
        "description_fr": "Réplique les fonds d'investissement immobilier américains (REITs). Donne accès à l'immobilier commercial (bureaux, appartements, commerces, entrepôts, data centers) sans détenir directement de biens.",
        "sector": "Real Estate", "geography": "USA", "asset_class": "ETF",
        "utility": "Real estate income + inflation hedge",
        "utility_fr": "Revenus immobiliers + couverture contre l'inflation",
        "typical_use": "Income and diversification. Often 5–10% in balanced portfolios.",
        "typical_use_fr": "Revenus et diversification. Souvent 5–10% dans les portefeuilles équilibrés.",
        "risk_level": "Medium", "liquidity": 95,
        "dividend_yield": "~3.8%", "market_cap": "~$35 billion AUM",
    },
    "TLT": {
        "name": "iShares 20+ Year Treasury Bond ETF",
        "description": "Tracks long-duration US government bonds (20+ year maturities). High sensitivity to interest rate changes — falls when rates rise, surges when rates fall. Classic safe-haven and recession hedge.",
        "description_fr": "Réplique les obligations d'État américaines à long terme (maturités 20+ ans). Très sensible aux taux : baisse quand les taux montent, monte quand ils baissent. Valeur refuge classique et couverture récession.",
        "sector": "Fixed Income", "geography": "USA", "asset_class": "ETF",
        "utility": "Long-duration rate hedge and crisis buffer",
        "utility_fr": "Couverture taux longue durée et tampon de crise",
        "typical_use": "Recession hedge, deflation protection. High duration risk.",
        "typical_use_fr": "Couverture récession, protection déflation. Risque de duration élevé.",
        "risk_level": "Medium", "liquidity": 99,
        "dividend_yield": "~4%", "market_cap": "~$50 billion AUM",
    },
    "AGG": {
        "name": "iShares Core US Aggregate Bond ETF",
        "description": "Broad US investment-grade bond market — government, corporate, and mortgage-backed securities. The benchmark fixed income ETF. Lower yield than TLT but much less rate sensitivity.",
        "description_fr": "Marché obligataire américain investment-grade au sens large — obligations d'État, d'entreprises et titres adossés à des créances hypothécaires. L'ETF obligataire de référence. Rendement inférieur à TLT mais bien moins sensible aux taux.",
        "sector": "Fixed Income", "geography": "USA", "asset_class": "ETF",
        "utility": "Portfolio stability, income, capital preservation",
        "utility_fr": "Stabilité du portefeuille, revenus, préservation du capital",
        "typical_use": "Ballast in balanced portfolios. Classic 40% in 60/40 allocation.",
        "typical_use_fr": "Lest des portefeuilles équilibrés. Le classique 40% dans l'allocation 60/40.",
        "risk_level": "Low", "liquidity": 100,
        "dividend_yield": "~3.5%", "market_cap": "~$100 billion AUM",
    },
    "LQD": {
        "name": "iShares Investment Grade Corporate Bond ETF",
        "description": "Tracks investment-grade corporate bonds. Higher yield than AGG (includes corporate credit premium). More rate-sensitive than short-term bonds.",
        "description_fr": "Réplique les obligations d'entreprises investment-grade. Rendement supérieur à AGG (prime de crédit corporate incluse). Plus sensible aux taux que les obligations court terme.",
        "sector": "Fixed Income", "geography": "USA", "asset_class": "ETF",
        "utility": "Higher-yield bond exposure with manageable credit risk",
        "utility_fr": "Exposition obligataire à rendement élevé avec risque de crédit maîtrisé",
        "typical_use": "Enhanced income vs AGG. Complement to government bonds.",
        "typical_use_fr": "Revenus améliorés par rapport à AGG. Complément aux obligations souveraines.",
        "risk_level": "Low-Medium", "liquidity": 98,
        "dividend_yield": "~4.5%", "market_cap": "~$35 billion AUM",
    },
    "SCHD": {
        "name": "Schwab US Dividend Equity ETF",
        "description": "Tracks US dividend-paying stocks with a quality filter (high yield + stable growth). Concentrated in Financials, Healthcare, Consumer Staples, and Industrials.",
        "description_fr": "Réplique les actions américaines à dividende avec filtre qualité (rendement élevé + croissance stable). Concentré en Financières, Santé, Biens de consommation courante et Industrie.",
        "sector": "Dividend/Income", "geography": "USA", "asset_class": "ETF",
        "utility": "Quality dividend income + capital appreciation",
        "utility_fr": "Dividendes de qualité + appréciation du capital",
        "typical_use": "Income-focused portion of equity allocation.",
        "typical_use_fr": "Partie revenus de l'allocation actions.",
        "risk_level": "Low-Medium", "liquidity": 98,
        "dividend_yield": "~3.5%", "market_cap": "~$55 billion AUM",
    },
    "GLD": {
        "name": "SPDR Gold Shares ETF",
        "description": "Physically-backed gold ETF. Holds actual gold bars in vaults. Tracks the spot gold price minus a small expense ratio (0.40%). The most liquid gold ETF in the world.",
        "description_fr": "ETF or physique. Détient de véritables lingots d'or en coffre-fort. Réplique le cours spot de l'or moins de faibles frais (0,40%). Le plus liquide des ETF or au monde.",
        "sector": "Commodities", "geography": "Global", "asset_class": "ETF",
        "utility": "Inflation hedge, safe haven, portfolio insurance",
        "utility_fr": "Couverture inflation, valeur refuge, assurance portefeuille",
        "typical_use": "Crisis protection and inflation hedge — 5–15% allocation.",
        "typical_use_fr": "Protection en crise et couverture inflation — allocation 5–15%.",
        "risk_level": "Low-Medium", "liquidity": 100,
        "dividend_yield": "0%", "market_cap": "~$60 billion AUM",
    },
    "SLV": {
        "name": "iShares Silver Trust ETF",
        "description": "Physically-backed silver ETF. Tracks the spot price of silver. More volatile than gold but also more industrial use (solar panels, electronics). Can outperform gold in bull markets.",
        "description_fr": "ETF argent physique. Réplique le cours spot de l'argent. Plus volatile que l'or mais avec des usages industriels importants (panneaux solaires, électronique). Peut surperformer l'or en phase haussière.",
        "sector": "Commodities", "geography": "Global", "asset_class": "ETF",
        "utility": "Industrial metal + precious metal speculation",
        "utility_fr": "Métal industriel + spéculation métal précieux",
        "typical_use": "Small satellite (1–5%). More speculative than GLD.",
        "typical_use_fr": "Petit satellite (1–5%). Plus spéculatif que GLD.",
        "risk_level": "Medium-High", "liquidity": 95,
        "dividend_yield": "0%", "market_cap": "~$12 billion AUM",
    },
    "XLK": {
        "name": "Technology Select Sector SPDR ETF",
        "description": "Pure tech sector ETF tracking S&P 500 technology companies. Top holdings: Apple, Microsoft, NVIDIA. More concentrated sector bet than QQQ.",
        "description_fr": "ETF purement tech répliquant les entreprises technologiques du S&P 500. Principales positions : Apple, Microsoft, NVIDIA. Pari sectoriel plus concentré que QQQ.",
        "sector": "Technology", "geography": "USA", "asset_class": "ETF",
        "utility": "Pure US technology sector exposure",
        "utility_fr": "Exposition pure au secteur technologique américain",
        "typical_use": "Tactical tech overweight in growth portfolios.",
        "typical_use_fr": "Surpondération tactique tech dans les portefeuilles de croissance.",
        "risk_level": "High", "liquidity": 98,
        "dividend_yield": "~0.6%", "market_cap": "~$65 billion AUM",
    },
    "XLF": {
        "name": "Financial Select Sector SPDR ETF",
        "description": "Tracks S&P 500 financial companies: banks, insurance, asset managers. Benefits from rising interest rates. Top holdings: JPMorgan, Berkshire, Visa, Mastercard.",
        "description_fr": "Réplique les entreprises financières du S&P 500 : banques, assurances, gestionnaires d'actifs. Bénéficie des hausses de taux. Principales positions : JPMorgan, Berkshire, Visa, Mastercard.",
        "sector": "Financials", "geography": "USA", "asset_class": "ETF",
        "utility": "Financial sector exposure, rate-sensitive",
        "utility_fr": "Exposition au secteur financier, sensible aux taux",
        "typical_use": "Tactical sector allocation when rates are rising.",
        "typical_use_fr": "Allocation sectorielle tactique en période de hausse des taux.",
        "risk_level": "Medium", "liquidity": 98,
        "dividend_yield": "~1.8%", "market_cap": "~$40 billion AUM",
    },
    "ARKK": {
        "name": "ARK Innovation ETF",
        "description": "Actively managed fund focusing on disruptive technology: AI, genomics, robotics, fintech, crypto. High concentration in small and mid-cap growth companies. Very high volatility.",
        "description_fr": "Fonds actif axé sur la technologie disruptive : IA, génomique, robotique, fintech, crypto. Forte concentration en entreprises de croissance petites et moyennes caps. Volatilité très élevée.",
        "sector": "Disruptive Tech", "geography": "USA", "asset_class": "ETF",
        "utility": "High-conviction disruptive innovation exposure",
        "utility_fr": "Exposition forte conviction à l'innovation disruptive",
        "typical_use": "Speculative satellite allocation (max 5%). Very high risk/reward.",
        "typical_use_fr": "Allocation satellite spéculative (max 5%). Risque/rendement très élevé.",
        "risk_level": "Very High", "liquidity": 88,
        "dividend_yield": "0%", "market_cap": "~$6 billion AUM",
    },
    # ── Crypto ───────────────────────────────────────────────────────────────
    "BTC-USD": {
        "name": "Bitcoin (BTC)",
        "description": "The first and largest cryptocurrency by market cap. Operates on a decentralised blockchain with a hard-capped supply of 21 million coins. Increasingly viewed as 'digital gold' by institutions.",
        "description_fr": "La première et plus grande cryptomonnaie par capitalisation. Fonctionne sur une blockchain décentralisée avec une offre limitée à 21 millions de coins. De plus en plus considéré comme 'l'or numérique' par les institutions.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Digital scarcity store-of-value, speculative return driver",
        "utility_fr": "Réserve de valeur par rareté numérique, moteur de rendement spéculatif",
        "typical_use": "Small allocation (3–10%) as portfolio diversifier and return booster.",
        "typical_use_fr": "Petite allocation (3–10%) comme diversificateur et booster de rendement.",
        "risk_level": "Very High", "liquidity": 85,
        "dividend_yield": "0%", "market_cap": "~$1.5 trillion",
    },
    "ETH-USD": {
        "name": "Ethereum (ETH)",
        "description": "The leading smart contract platform powering DeFi, NFTs, and Web3. Transitioned to Proof-of-Stake in 2022, reducing energy use by 99.9%. Ether is used to pay transaction fees.",
        "description_fr": "La principale plateforme de contrats intelligents alimentant la DeFi, les NFTs et le Web3. Passé en Proof-of-Stake en 2022, réduisant la consommation d'énergie de 99,9%. L'Ether sert à payer les frais de transaction.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Web3 infrastructure platform exposure",
        "utility_fr": "Exposition à la plateforme d'infrastructure Web3",
        "typical_use": "Complement to Bitcoin. Typically smaller allocation (1–5%).",
        "typical_use_fr": "Complément du Bitcoin. Allocation généralement plus petite (1–5%).",
        "risk_level": "Very High", "liquidity": 82,
        "dividend_yield": "0% (staking ~4%)", "market_cap": "~$300 billion",
    },
    "SOL-USD": {
        "name": "Solana (SOL)",
        "description": "High-performance Layer 1 blockchain processing 50,000+ transactions per second at low cost. Dominant in meme coins, NFTs, and DeFi. More volatile than BTC/ETH but higher growth potential.",
        "description_fr": "Blockchain Layer 1 haute performance traitant 50 000+ transactions/seconde à faible coût. Dominante dans les meme coins, NFTs et DeFi. Plus volatile que BTC/ETH mais potentiel de croissance élevé.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "High-growth crypto ecosystem exposure",
        "utility_fr": "Exposition à l'écosystème crypto à forte croissance",
        "typical_use": "Speculative satellite (1–3%). Very high volatility.",
        "typical_use_fr": "Satellite spéculatif (1–3%). Volatilité très élevée.",
        "risk_level": "Very High", "liquidity": 70,
        "dividend_yield": "0% (staking ~7%)", "market_cap": "~$70 billion",
    },
    "BNB-USD": {
        "name": "Binance Coin (BNB)",
        "description": "Native token of the Binance ecosystem — the world's largest crypto exchange. Used for trading fee discounts, BNB Chain transactions (DeFi/dApps), and token launches via Binance Launchpad.",
        "description_fr": "Token natif de l'écosystème Binance — le plus grand exchange crypto au monde. Utilisé pour les réductions de frais de trading, les transactions BNB Chain (DeFi/dApps) et les lancements via Binance Launchpad.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Exchange utility token + BNB Chain ecosystem",
        "utility_fr": "Token utilitaire d'exchange + écosystème BNB Chain",
        "typical_use": "Speculative satellite (1–2%). Tied to Binance exchange health.",
        "typical_use_fr": "Satellite spéculatif (1–2%). Lié à la santé de l'exchange Binance.",
        "risk_level": "Very High", "liquidity": 78,
        "dividend_yield": "0%", "market_cap": "~$80 billion",
    },
    "XRP-USD": {
        "name": "XRP (Ripple)",
        "description": "Digital asset designed for fast, low-cost international payments. Used by banks and financial institutions via RippleNet. Won a landmark SEC lawsuit in 2023 clarifying its legal status in the US.",
        "description_fr": "Actif numérique conçu pour des paiements internationaux rapides et peu coûteux. Utilisé par les banques via RippleNet. A gagné un procès historique contre la SEC en 2023 clarifiant son statut légal aux USA.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Cross-border payments and banking infrastructure crypto",
        "utility_fr": "Crypto dédiée aux paiements transfrontaliers et à l'infrastructure bancaire",
        "typical_use": "Speculative satellite (1–3%). High regulatory sensitivity.",
        "typical_use_fr": "Satellite spéculatif (1–3%). Très sensible aux évolutions réglementaires.",
        "risk_level": "Very High", "liquidity": 80,
        "dividend_yield": "0%", "market_cap": "~$120 billion",
    },
    "ADA-USD": {
        "name": "Cardano (ADA)",
        "description": "Proof-of-Stake Layer 1 blockchain built with a research-first, peer-reviewed approach. Developed by IOHK (co-founded by Ethereum co-founder Charles Hoskinson). Focuses on scalability and sustainability.",
        "description_fr": "Blockchain Layer 1 Proof-of-Stake construite avec une approche académique et revue par les pairs. Développée par IOHK (cofondé par le co-fondateur d'Ethereum Charles Hoskinson). Axée sur la scalabilité et la durabilité.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Proof-of-Stake smart contract platform, sustainable blockchain",
        "utility_fr": "Plateforme de contrats intelligents PoS, blockchain durable",
        "typical_use": "Speculative alt-coin (0.5–2%). Higher risk than ETH.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–2%). Risque plus élevé qu'ETH.",
        "risk_level": "Very High", "liquidity": 72,
        "dividend_yield": "0% (staking ~4%)", "market_cap": "~$25 billion",
    },
    "AVAX-USD": {
        "name": "Avalanche (AVAX)",
        "description": "High-speed Layer 1 blockchain with sub-second finality and low fees. Uses a unique 3-chain architecture (X, P, C chains). Growing DeFi and gaming ecosystem, strong institutional adoption.",
        "description_fr": "Blockchain Layer 1 haute vitesse avec finalité en sous-seconde et frais bas. Architecture unique à 3 chaînes (X, P, C). Écosystème DeFi et gaming en croissance, forte adoption institutionnelle.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "High-performance DeFi and institutional blockchain",
        "utility_fr": "Blockchain DeFi haute performance et institutionnelle",
        "typical_use": "Speculative alt-coin (0.5–2%). Competitive with SOL.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–2%). En compétition avec SOL.",
        "risk_level": "Very High", "liquidity": 68,
        "dividend_yield": "0% (staking ~8%)", "market_cap": "~$15 billion",
    },
    "DOT-USD": {
        "name": "Polkadot (DOT)",
        "description": "Multi-chain protocol enabling different blockchains to communicate and share security. Uses a Relay Chain + Parachain architecture. Developed by Ethereum co-founder Gavin Wood and the Web3 Foundation.",
        "description_fr": "Protocole multi-chaînes permettant à différentes blockchains de communiquer et partager leur sécurité. Architecture Relay Chain + Parachain. Développé par le co-fondateur d'Ethereum Gavin Wood et la Web3 Foundation.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Cross-chain interoperability protocol",
        "utility_fr": "Protocole d'interopérabilité multi-chaînes",
        "typical_use": "Speculative alt-coin (0.5–1.5%). High technical complexity.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–1,5%). Complexité technique élevée.",
        "risk_level": "Very High", "liquidity": 65,
        "dividend_yield": "0% (staking ~15%)", "market_cap": "~$10 billion",
    },
    "LINK-USD": {
        "name": "Chainlink (LINK)",
        "description": "Decentralised oracle network that connects smart contracts to real-world data (prices, weather, sports results). Critical DeFi infrastructure — used by 1,000+ blockchain protocols.",
        "description_fr": "Réseau oracle décentralisé connectant les smart contracts aux données du monde réel (prix, météo, résultats sportifs). Infrastructure DeFi critique — utilisée par 1 000+ protocoles blockchain.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "DeFi infrastructure — blockchain oracle network",
        "utility_fr": "Infrastructure DeFi — réseau oracle blockchain",
        "typical_use": "Speculative alt-coin (0.5–2%). Fundamental DeFi infrastructure bet.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–2%). Pari sur l'infrastructure DeFi fondamentale.",
        "risk_level": "Very High", "liquidity": 65,
        "dividend_yield": "0%", "market_cap": "~$8 billion",
    },
    "MATIC-USD": {
        "name": "Polygon (POL/MATIC)",
        "description": "Ethereum Layer 2 scaling solution dramatically reducing gas fees and transaction times. Now rebranding to POL as it transitions to a multi-chain aggregator. Used by major brands (Starbucks, Nike, Reddit).",
        "description_fr": "Solution de mise à l'échelle Layer 2 d'Ethereum réduisant drastiquement les frais de gas et les temps de transaction. En cours de rebranding vers POL dans sa transition vers un agrégateur multi-chaînes. Utilisé par Starbucks, Nike, Reddit.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Ethereum Layer 2 scaling and multi-chain aggregation",
        "utility_fr": "Mise à l'échelle Layer 2 d'Ethereum et agrégation multi-chaînes",
        "typical_use": "Speculative alt-coin (0.5–2%). Strong enterprise adoption.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–2%). Forte adoption entreprises.",
        "risk_level": "Very High", "liquidity": 70,
        "dividend_yield": "0%", "market_cap": "~$5 billion",
    },
    "DOGE-USD": {
        "name": "Dogecoin (DOGE)",
        "description": "Originally a meme coin, Dogecoin has become a widely recognised crypto asset with strong community support. Favoured by Elon Musk. Used for tipping and micro-payments. Unlimited supply.",
        "description_fr": "À l'origine un meme coin, Dogecoin est devenu un actif crypto reconnu avec une forte communauté. Soutenu par Elon Musk. Utilisé pour les pourboires et micro-paiements. Offre illimitée.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Meme coin / community-driven speculative asset",
        "utility_fr": "Meme coin / actif spéculatif piloté par la communauté",
        "typical_use": "Pure speculation (0–1%). Very high sentiment sensitivity.",
        "typical_use_fr": "Pure spéculation (0–1%). Très sensible au sentiment de marché.",
        "risk_level": "Very High", "liquidity": 75,
        "dividend_yield": "0%", "market_cap": "~$25 billion",
    },
    "INJ-USD": {
        "name": "Injective (INJ)",
        "description": "Layer 1 blockchain optimised for DeFi applications — particularly decentralised exchanges (DEX), derivatives, and prediction markets. Fast (10,000+ TPS), EVM-compatible, with a deflationary token burn mechanism.",
        "description_fr": "Blockchain Layer 1 optimisée pour les applications DeFi — notamment les échanges décentralisés (DEX), les dérivés et les marchés prédictifs. Rapide (10 000+ TPS), compatible EVM, avec un mécanisme de burn déflationniste.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "DeFi-native blockchain for derivatives and exchanges",
        "utility_fr": "Blockchain native DeFi pour dérivés et échanges décentralisés",
        "typical_use": "High-risk alt-coin (0.5–1%). Emerging DeFi infrastructure.",
        "typical_use_fr": "Alt-coin à haut risque (0,5–1%). Infrastructure DeFi émergente.",
        "risk_level": "Very High", "liquidity": 55,
        "dividend_yield": "0% (staking ~10%)", "market_cap": "~$3 billion",
    },
    "TON-USD": {
        "name": "Toncoin (TON)",
        "description": "Blockchain developed originally by Telegram, now operated by the TON Foundation. Deeply integrated with Telegram's 900M users. Fast, scalable, and increasingly used for payments and Web3 games.",
        "description_fr": "Blockchain développée à l'origine par Telegram, désormais gérée par la TON Foundation. Profondément intégrée aux 900M d'utilisateurs Telegram. Rapide, scalable, de plus en plus utilisée pour les paiements et les jeux Web3.",
        "sector": "Cryptocurrency", "geography": "Global", "asset_class": "Crypto",
        "utility": "Telegram-integrated payments and Web3 gateway",
        "utility_fr": "Passerelle paiements et Web3 intégrée à Telegram",
        "typical_use": "Speculative alt-coin (0.5–1.5%). Unique Telegram distribution advantage.",
        "typical_use_fr": "Alt-coin spéculatif (0,5–1,5%). Avantage unique de distribution via Telegram.",
        "risk_level": "Very High", "liquidity": 60,
        "dividend_yield": "0% (staking ~4%)", "market_cap": "~$20 billion",
    },
}

SECTOR_MAPPING = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", "AMZN": "Technology",
    "TSLA": "Automotive", "NVDA": "Technology", "META": "Technology", "NFLX": "Technology",
    "JPM": "Financials", "JNJ": "Healthcare", "XOM": "Energy", "V": "Financials",
    "MA": "Financials", "WMT": "Consumer", "HD": "Consumer", "BRK-B": "Financials",
    "SPY": "Diversified", "QQQ": "Technology", "VTI": "Diversified", "VOO": "Diversified",
    "VXUS": "International", "EFA": "International", "EEM": "Emerging Markets",
    "VNQ": "Real Estate", "TLT": "Bonds", "AGG": "Bonds", "LQD": "Bonds",
    "SCHD": "Dividend", "GLD": "Commodities", "SLV": "Commodities",
    "XLK": "Technology", "XLF": "Financials", "XLE": "Energy", "XLV": "Healthcare",
    "ARKK": "Technology",
    "BTC-USD": "Crypto", "ETH-USD": "Crypto", "SOL-USD": "Crypto", "BNB-USD": "Crypto",
    "XRP-USD": "Crypto", "ADA-USD": "Crypto", "AVAX-USD": "Crypto", "DOT-USD": "Crypto",
    "LINK-USD": "Crypto", "MATIC-USD": "Crypto", "DOGE-USD": "Crypto",
    "INJ-USD": "Crypto", "TON-USD": "Crypto",
}

GEOGRAPHY_MAPPING = {
    "AAPL": "USA", "MSFT": "USA", "GOOGL": "USA", "AMZN": "USA",
    "NVDA": "USA", "META": "USA", "TSLA": "USA", "NFLX": "USA",
    "JPM": "USA", "JNJ": "USA", "XOM": "USA", "V": "USA",
    "MA": "USA", "WMT": "USA", "HD": "USA", "BRK-B": "USA",
    "SPY": "USA", "QQQ": "USA", "VTI": "USA", "VOO": "USA",
    "VXUS": "International", "EFA": "Developed Ex-US", "EEM": "Emerging Markets",
    "VNQ": "USA", "TLT": "USA", "AGG": "USA", "LQD": "USA",
    "SCHD": "USA", "XLK": "USA", "XLF": "USA", "XLE": "USA", "XLV": "USA",
    "ARKK": "USA", "GLD": "Global", "SLV": "Global",
    "BTC-USD": "Global", "ETH-USD": "Global", "SOL-USD": "Global", "BNB-USD": "Global",
    "XRP-USD": "Global", "ADA-USD": "Global", "AVAX-USD": "Global", "DOT-USD": "Global",
    "LINK-USD": "Global", "MATIC-USD": "Global", "DOGE-USD": "Global",
    "INJ-USD": "Global", "TON-USD": "Global",
    "VWO": "Emerging Markets",
}

POPULAR_ASSETS = {
    "US Stocks": {
        "Apple": "AAPL", "Microsoft": "MSFT", "Google": "GOOGL", "Amazon": "AMZN",
        "NVIDIA": "NVDA", "Meta": "META", "Tesla": "TSLA", "JPMorgan": "JPM",
        "Johnson & Johnson": "JNJ", "ExxonMobil": "XOM", "Visa": "V",
    },
    "US ETFs": {
        "S&P 500 (SPY)": "SPY", "S&P 500 (VOO)": "VOO", "Nasdaq 100": "QQQ",
        "Total Market": "VTI", "Dividends": "SCHD", "Real Estate": "VNQ",
        "Long Bonds": "TLT", "Aggregate Bonds": "AGG", "Tech Sector": "XLK",
        "ARK Innovation": "ARKK",
    },
    "International ETFs": {
        "All World Ex-US": "VXUS", "Developed Markets": "EFA", "Emerging Markets": "EEM",
    },
    "Commodities & Gold": {
        "Gold": "GLD", "Silver": "SLV",
    },
    "Crypto": {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD",
        "BNB": "BNB-USD", "XRP": "XRP-USD", "Cardano": "ADA-USD",
        "Avalanche": "AVAX-USD", "Polkadot": "DOT-USD", "Chainlink": "LINK-USD",
        "Polygon": "MATIC-USD", "Dogecoin": "DOGE-USD", "Injective": "INJ-USD",
        "Toncoin": "TON-USD",
    },
}

MODEL_PORTFOLIOS = {
    "Capital Preservation": {
        "description_en": "Ultra-defensive: bonds + gold. Prioritises capital protection over returns.",
        "description_fr": "Ultra-défensif : obligations + or. Priorité à la protection du capital.",
        "profile": "safe",
        "allocation": {"AGG": 0.45, "TLT": 0.20, "GLD": 0.20, "SPY": 0.15},
        "expected_return": 0.05,
        "expected_volatility": 0.06,
    },
    "Defensive Income": {
        "description_en": "Conservative mix generating reliable dividend income with low volatility.",
        "description_fr": "Mix conservateur générant des revenus de dividendes fiables à faible volatilité.",
        "profile": "safe",
        "allocation": {"SCHD": 0.30, "AGG": 0.30, "VNQ": 0.15, "GLD": 0.15, "SPY": 0.10},
        "expected_return": 0.07,
        "expected_volatility": 0.09,
    },
    "Classic 60/40": {
        "description_en": "The timeless 60% stocks / 40% bonds portfolio. Balanced risk-return profile.",
        "description_fr": "Le classique 60% actions / 40% obligations. Profil risque/rendement équilibré.",
        "profile": "balanced",
        "allocation": {"SPY": 0.30, "VXUS": 0.15, "QQQ": 0.15, "AGG": 0.25, "GLD": 0.10, "VNQ": 0.05},
        "expected_return": 0.08,
        "expected_volatility": 0.12,
    },
    "Global Growth": {
        "description_en": "Diversified across US, international and emerging markets. Long-term growth.",
        "description_fr": "Diversifié entre marchés US, internationaux et émergents. Croissance long terme.",
        "profile": "balanced",
        "allocation": {"VTI": 0.30, "EFA": 0.20, "EEM": 0.15, "AGG": 0.20, "GLD": 0.10, "VNQ": 0.05},
        "expected_return": 0.09,
        "expected_volatility": 0.14,
    },
    "Tech Leaders": {
        "description_en": "Concentrated in top technology companies driving the AI and cloud revolution.",
        "description_fr": "Concentré sur les grandes entreprises tech à la pointe de l'IA et du cloud.",
        "profile": "aggressive",
        "allocation": {"MSFT": 0.20, "GOOGL": 0.20, "NVDA": 0.20, "AAPL": 0.15, "AMZN": 0.15, "META": 0.10},
        "expected_return": 0.18,
        "expected_volatility": 0.24,
    },
    "Crypto & Innovation": {
        "description_en": "High-conviction bet on digital assets and disruptive technology. Very high risk.",
        "description_fr": "Pari fort sur les actifs numériques et la tech disruptive. Risque très élevé.",
        "profile": "aggressive",
        "allocation": {"BTC-USD": 0.30, "ETH-USD": 0.20, "NVDA": 0.20, "QQQ": 0.20, "ARKK": 0.10},
        "expected_return": 0.25,
        "expected_volatility": 0.40,
    },
    "Dividend Champion": {
        "description_en": "Quality dividend payers for passive income. Defensive sectors.",
        "description_fr": "Actions à dividendes de qualité pour revenus passifs. Secteurs défensifs.",
        "profile": "balanced",
        "allocation": {"SCHD": 0.35, "JNJ": 0.15, "JPM": 0.15, "XOM": 0.10, "VNQ": 0.15, "GLD": 0.10},
        "expected_return": 0.09,
        "expected_volatility": 0.11,
    },
    "All-Weather": {
        "description_en": "Ray Dalio-inspired portfolio resilient across all economic environments.",
        "description_fr": "Inspiré de Ray Dalio, résilient dans tous les environnements économiques.",
        "profile": "balanced",
        "allocation": {"SPY": 0.30, "TLT": 0.20, "AGG": 0.15, "GLD": 0.15, "EFA": 0.10, "VNQ": 0.10},
        "expected_return": 0.08,
        "expected_volatility": 0.10,
    },
}

# =============================================================================
# SESSION STATE WITH AUTO-REBALANCE
# =============================================================================

def resolve_tier(email: str) -> str:
    """Return 'pro' if email is in PRO_EMAILS, else 'free'."""
    if not email:
        return 'free'
    return 'pro' if email.lower() in PRO_EMAILS else 'free'


def init_session_state():
    defaults = {
        'authenticated': False,
        'user_email': "",
        'user_tier': 'free',
        'current_portfolio': None,
        'page': "dashboard",
        'language': "en",
        'selected_tickers': [],
        'weights': {},
        'user_profile': "balanced",
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

T = {
    "en": {
        "dashboard": "Dashboard", "new_analysis": "New Analysis",
        "models": "Model Portfolios", "improve": "Optimise",
        "library": "Asset Library", "account": "Account",
        "robustness": "Robustness Index", "recommendations": "Recommendations",
        "stress_test": "Stress Tests", "asset_info": "Asset Details",
        "portfolio_summary": "Portfolio Summary",
        "selected_assets": "Selected Assets",
        "analyse_btn": "Analyse Portfolio",
        "run_stress": "Run Stress Tests",
        "optimise_btn": "Optimise Portfolio",
        "apply_opt": "Apply Optimisation",
        "current": "Current", "optimised": "Optimised",
        "use_model": "Use this portfolio",
        "expected_return": "Expected Return",
        "volatility": "Volatility",
        "sharpe": "Sharpe Ratio",
        "annual_return": "Annual Return",
        "max_drawdown": "Max Drawdown",
        "total_weight": "Total",
        "add": "Add", "remove": "Remove",
        "search_ph": "Apple, Bitcoin, S&P 500...",
        "browse": "Browse",
        "search": "Search",
        "welcome": "Welcome! Start by creating a portfolio.",
        "create_portfolio": "Create Portfolio",
        "no_portfolio": "Create a portfolio first.",
        "loading": "Fetching market data...",
        "analysis_done": "Analysis complete!",
        "fetch_error": "Could not fetch data. Check ticker symbols.",
        "upgrade_pro": "Upgrade to Pro",
        "login": "Continue",
        "logout": "Log out",
        "profile_label": "Risk Profile",
        "profile_safe": "Prudent",
        "profile_balanced": "Balanced",
        "profile_aggressive": "Aggressive",
        "filter_type": "Filter by type",
        "filter_all": "All",
        "normalised": "Total normalised to 100%.",
    },
    "fr": {
        "dashboard": "Tableau de Bord", "new_analysis": "Nouvelle Analyse",
        "models": "Portefeuilles Modèles", "improve": "Optimiser",
        "library": "Bibliothèque", "account": "Compte",
        "robustness": "Indice de Robustesse", "recommendations": "Recommandations",
        "stress_test": "Tests de Stress", "asset_info": "Détail des Actifs",
        "portfolio_summary": "Résumé du Portefeuille",
        "selected_assets": "Actifs Sélectionnés",
        "analyse_btn": "Analyser le Portefeuille",
        "run_stress": "Lancer les Tests de Stress",
        "optimise_btn": "Optimiser le Portefeuille",
        "apply_opt": "Appliquer l'Optimisation",
        "current": "Actuel", "optimised": "Optimisé",
        "use_model": "Utiliser ce portefeuille",
        "expected_return": "Rendement Attendu",
        "volatility": "Volatilité",
        "sharpe": "Ratio de Sharpe",
        "annual_return": "Rendement Annuel",
        "max_drawdown": "Perte Max",
        "total_weight": "Total",
        "add": "Ajouter", "remove": "Supprimer",
        "search_ph": "Apple, Bitcoin, S&P 500...",
        "browse": "Parcourir",
        "search": "Rechercher",
        "welcome": "Bienvenue ! Commencez par créer un portefeuille.",
        "create_portfolio": "Créer un Portefeuille",
        "no_portfolio": "Créez d'abord un portefeuille.",
        "loading": "Récupération des données...",
        "analysis_done": "Analyse terminée !",
        "fetch_error": "Impossible de récupérer les données. Vérifiez les tickers.",
        "upgrade_pro": "Passer à Pro",
        "login": "Continuer",
        "logout": "Se déconnecter",
        "profile_label": "Profil de Risque",
        "profile_safe": "Prudent",
        "profile_balanced": "Équilibré",
        "profile_aggressive": "Agressif",
        "filter_type": "Filtrer par type",
        "filter_all": "Tous",
        "normalised": "Total normalisé à 100%.",
    }
}

def t(key, lang="en"):
    return T.get(lang, T["en"]).get(key, key)

# =============================================================================
# ADVANCED PORTFOLIO ANALYZER
# =============================================================================

class UltimatePortfolioAnalyzer:
    def __init__(self, tickers, weights, start_date='2021-01-01', initial_value=100000, user_profile="balanced"):
        self.tickers = tickers
        self.weights = weights
        self.start_date = start_date
        self.initial_value = initial_value
        self.user_profile = user_profile
        self.data = None
        
    def fetch_data(self):
        """Fetch data with progress."""
        all_data = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        for i, ticker in enumerate(self.tickers):
            try:
                status.text(f"Loading {ticker}...")
                data = yf.Ticker(ticker).history(start=self.start_date)
                data = data[['Close']].rename(columns={'Close': ticker})
                all_data.append(data)
                progress_bar.progress((i + 1) / len(self.tickers))
            except Exception as e:
                st.warning(f"{ticker}: {str(e)[:50]}")
        
        status.empty()
        progress_bar.empty()
        
        if not all_data:
            return False

        self.data = pd.concat(all_data, axis=1)
        # Only keep tickers that actually downloaded successfully
        available = [t for t in self.tickers if t in self.data.columns]
        if not available:
            return False
        self.data = self.data[available].ffill().bfill()

        # Sync tickers and weights to available data
        self.tickers = available
        total_w = sum(self.weights[t] for t in available)
        self.weights = {t: self.weights[t] / total_w for t in available}

        self.returns = self.data.pct_change().dropna()
        weights_array = np.array([self.weights[t] for t in self.tickers])
        self.portfolio_returns = self.returns @ weights_array
        self.portfolio_values = self.initial_value * (1 + self.portfolio_returns).cumprod()
        return True
    
    def calculate_robustness_index(self):
        """
        FIX #2: Calculate Portfolio Robustness Index (0-100).
        Measures portfolio resilience to crises and structural risks.
        """
        metrics = self.calculate_metrics()
        
        # 1. DIVERSIFICATION (20 points)
        n_assets = len(self.tickers)
        if n_assets >= 10:
            div_score = 20
        elif n_assets >= 7:
            div_score = 17
        elif n_assets >= 5:
            div_score = 14
        elif n_assets >= 3:
            div_score = 10
        else:
            div_score = 5
        
        # 2. CONCENTRATION (20 points)
        max_weight = max(self.weights.values())
        if max_weight < 0.15:
            conc_score = 20
        elif max_weight < 0.25:
            conc_score = 16
        elif max_weight < 0.35:
            conc_score = 12
        elif max_weight < 0.45:
            conc_score = 8
        else:
            conc_score = 4
        
        # 3. CORRELATION (15 points)
        corr_matrix = self.returns.corr()
        avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, 1)].mean()
        if avg_corr < 0.30:
            corr_score = 15
        elif avg_corr < 0.50:
            corr_score = 12
        elif avg_corr < 0.70:
            corr_score = 8
        else:
            corr_score = 4
        
        # 4. VOLATILITY (15 points)
        vol = metrics['volatility']
        if vol < 0.10:
            vol_score = 15
        elif vol < 0.15:
            vol_score = 13
        elif vol < 0.25:
            vol_score = 10
        elif vol < 0.35:
            vol_score = 6
        else:
            vol_score = 3
        
        # 5. DRAWDOWN (15 points)
        max_dd = abs(metrics['max_drawdown'])
        if max_dd < 0.10:
            dd_score = 15
        elif max_dd < 0.20:
            dd_score = 12
        elif max_dd < 0.30:
            dd_score = 9
        elif max_dd < 0.40:
            dd_score = 5
        else:
            dd_score = 2
        
        # 6. GEOGRAPHIC DIVERSIFICATION (10 points)
        geographies = set()
        for ticker in self.tickers:
            geo = GEOGRAPHY_MAPPING.get(ticker, "Unknown")
            geographies.add(geo)
        
        geo_count = len(geographies)
        if geo_count >= 3:
            geo_score = 10
        elif geo_count >= 2:
            geo_score = 7
        else:
            geo_score = 3
        
        # 7. SECTOR DIVERSIFICATION (5 points)
        sectors = set()
        for ticker in self.tickers:
            sector = SECTOR_MAPPING.get(ticker, "Unknown")
            sectors.add(sector)
        
        sector_count = len(sectors)
        if sector_count >= 4:
            sector_score = 5
        elif sector_count >= 3:
            sector_score = 4
        elif sector_count >= 2:
            sector_score = 2
        else:
            sector_score = 1
        
        # TOTAL SCORE
        total = div_score + conc_score + corr_score + vol_score + dd_score + geo_score + sector_score
        
        # Interpretation
        if total >= 90:
            interpretation = "Very Robust"
            color = "#10b981"
        elif total >= 70:
            interpretation = "Robust"
            color = "#6366f1"
        elif total >= 50:
            interpretation = "Fragile"
            color = "#f59e0b"
        else:
            interpretation = "High Risk"
            color = "#ef4444"
        
        return {
            'total': int(total),
            'diversification': div_score,
            'concentration': conc_score,
            'correlation': corr_score,
            'volatility': vol_score,
            'drawdown': dd_score,
            'geography': geo_score,
            'sector': sector_score,
            'interpretation': interpretation,
            'color': color,
        }
    
    def calculate_health_score(self):
        """
        Global Portfolio Health Score (0-100).
        Combines three dimensions:
          - Structure (40%): Robustness Index
          - Performance Quality (35%): Sharpe + Annual Return
          - Liquidity (25%): weighted average liquidity of assets
        """
        robustness = self.calculate_robustness_index()
        metrics = self.calculate_metrics()

        # ── 1. Structure (directly from Robustness Index) ──────────────────
        structure = robustness['total']  # 0-100

        # ── 2. Performance Quality ─────────────────────────────────────────
        sharpe = metrics['sharpe']
        annual_ret = metrics['annual_return']

        if sharpe >= 2.0:   sharpe_s = 100
        elif sharpe >= 1.5: sharpe_s = 84
        elif sharpe >= 1.0: sharpe_s = 68
        elif sharpe >= 0.5: sharpe_s = 50
        elif sharpe >= 0:   sharpe_s = 30
        else:               sharpe_s = 10

        if annual_ret >= 0.15:   ret_s = 100
        elif annual_ret >= 0.10: ret_s = 84
        elif annual_ret >= 0.07: ret_s = 68
        elif annual_ret >= 0.04: ret_s = 50
        elif annual_ret >= 0:    ret_s = 30
        else:                    ret_s = 10

        performance = (sharpe_s * 0.55 + ret_s * 0.45)  # 0-100

        # ── 3. Liquidity ───────────────────────────────────────────────────
        weighted_liq = 0.0
        for ticker in self.tickers:
            info = ASSET_INFO.get(ticker, {})
            liq = info.get('liquidity', 70)
            weighted_liq += liq * self.weights[ticker]
        liquidity = weighted_liq  # 0-100

        # ── Overall ────────────────────────────────────────────────────────
        total = structure * 0.40 + performance * 0.35 + liquidity * 0.25
        total = round(min(100, max(0, total)))

        if total >= 85:
            grade, color = "Excellent", "#10b981"
        elif total >= 70:
            grade, color = "Good", "#4f46e5"
        elif total >= 55:
            grade, color = "Fair", "#f59e0b"
        elif total >= 40:
            grade, color = "Weak", "#f97316"
        else:
            grade, color = "Critical", "#ef4444"

        grade_fr = {"Excellent": "Excellent", "Good": "Bon", "Fair": "Passable",
                    "Weak": "Faible", "Critical": "Critique"}

        return {
            'total': total,
            'structure': round(structure),
            'performance': round(performance),
            'liquidity': round(liquidity),
            'grade': grade,
            'grade_fr': grade_fr[grade],
            'color': color,
        }

    def generate_improvement_suggestions(self, lang="en"):
        """
        FIX #3 & #4: Generate intelligent improvement suggestions.
        Analyzes current portfolio and suggests optimized version.
        """
        metrics = self.calculate_metrics()
        robustness = self.calculate_robustness_index()
        suggestions = []
        
        # HIGH PRIORITY
        max_weight = max(self.weights.values())
        max_ticker = max(self.weights, key=self.weights.get)
        
        if max_weight > 0.40:
            suggestions.append({
                'priority': 'CRITICAL',
                'type': 'critical',
                'title': 'Critical Concentration' if lang == 'en' else 'Concentration Critique',
                'issue': f'{max_ticker} = {max_weight*100:.0f}%',
                'solution': f'Reduce to <30%. Diversify into VXUS + AGG' if lang == 'en'
                           else f'Réduire <30%. Diversifier vers VXUS + AGG',
                'impact': 'Robustness +15 pts' if lang == 'en' else 'Robustesse +15 pts',
            })
        
        # Sector concentration
        sectors = {}
        for ticker in self.tickers:
            sector = SECTOR_MAPPING.get(ticker, "Unknown")
            sectors[sector] = sectors.get(sector, 0) + self.weights[ticker]
        
        for sector, exposure in sectors.items():
            if exposure > 0.50 and sector != "Diversified":
                suggestions.append({
                    'priority': 'HIGH',
                    'type': 'warning',
                    'title': f'High {sector} Exposure' if lang == 'en' else f'Exposition {sector} Élevée',
                    'issue': f'{exposure*100:.0f}% in {sector}' if lang == 'en' else f'{exposure*100:.0f}% dans {sector}',
                    'solution': f'Add international ETF (VXUS) or bonds (AGG)' if lang == 'en'
                               else f'Ajouter ETF international (VXUS) ou obligations (AGG)',
                    'impact': 'Robustness +10 pts' if lang == 'en' else 'Robustesse +10 pts',
                })
        
        # Geographic concentration
        geographies = {}
        for ticker in self.tickers:
            geo = GEOGRAPHY_MAPPING.get(ticker, "Unknown")
            geographies[geo] = geographies.get(geo, 0) + self.weights[ticker]
        
        usa_exposure = geographies.get("USA", 0)
        if usa_exposure > 0.70:
            suggestions.append({
                'priority': 'HIGH',
                'type': 'warning',
                'title': 'Geographic Concentration' if lang == 'en' else 'Concentration Géographique',
                'issue': f'{usa_exposure*100:.0f}% USA exposure' if lang == 'en' else f'{usa_exposure*100:.0f}% exposition USA',
                'solution': 'Add VXUS (international) for global diversification' if lang == 'en'
                           else 'Ajouter VXUS (international) pour diversification mondiale',
                'impact': 'Robustness +8 pts' if lang == 'en' else 'Robustesse +8 pts',
            })
        
        # Lack of bonds/hedges
        has_bonds = any(ticker in ['AGG', 'BND', 'TLT'] for ticker in self.tickers)
        has_gold = any(ticker in ['GLD', 'IAU'] for ticker in self.tickers)
        
        if not has_bonds and not has_gold:
            suggestions.append({
                'priority': 'MEDIUM',
                'type': 'info',
                'title': 'Missing Hedges' if lang == 'en' else 'Absence de Couverture',
                'issue': 'No bonds or gold in portfolio' if lang == 'en' else 'Aucune obligation ni or dans le portefeuille',
                'solution': 'Add 10-20% AGG (bonds) and 5-10% GLD (gold) for stability' if lang == 'en'
                           else 'Ajouter 10-20% AGG (obligations) et 5-10% GLD (or)',
                'impact': 'Robustness +6 pts' if lang == 'en' else 'Robustesse +6 pts',
            })
        
        # Low diversification
        if len(self.tickers) < 5:
            suggestions.append({
                'priority': 'HIGH',
                'type': 'warning',
                'title': 'Low Diversification' if lang == 'en' else 'Faible Diversification',
                'issue': f'Only {len(self.tickers)} assets' if lang == 'en' else f'Seulement {len(self.tickers)} actifs',
                'solution': 'Add 3-5 more assets from different sectors/geographies' if lang == 'en'
                           else 'Ajouter 3-5 actifs de secteurs/géographies différents',
                'impact': 'Robustness +12 pts' if lang == 'en' else 'Robustesse +12 pts',
            })
        
        # High volatility
        if metrics['volatility'] > 0.25:
            suggestions.append({
                'priority': 'MEDIUM',
                'type': 'warning',
                'title': 'High Volatility' if lang == 'en' else 'Volatilité Élevée',
                'issue': f'{metrics["volatility"]*100:.0f}% annual volatility' if lang == 'en' else f'{metrics["volatility"]*100:.0f}% de volatilité annuelle',
                'solution': 'Reduce high-vol assets. Add AGG (bonds) for stability' if lang == 'en'
                           else 'Réduire actifs volatils. Ajouter AGG (obligations)',
                'impact': 'Robustness +7 pts' if lang == 'en' else 'Robustesse +7 pts',
            })
        
        return suggestions
    
    def generate_profile_adapted_suggestions(self, lang="en"):
        """
        FIX #5: Profile-adapted recommendations (Safe/Balanced/Aggressive).
        """
        profile = self.user_profile
        suggestions = []
        
        if profile == "safe":
            # Check if portfolio is too risky
            vol = self.calculate_metrics()['volatility']
            if vol > 0.12:
                suggestions.append({
                    'priority': 'HIGH',
                    'type': 'warning',
                    'title': 'Too Risky for Safe Profile' if lang == 'en' else 'Trop Risqué pour Profil Sûr',
                    'issue': f'Volatility {vol*100:.0f}% > recommended 12%' if lang == 'en' else f'Volatilité {vol*100:.0f}% > recommandé 12%',
                    'solution': 'Increase bonds (AGG) to 40-50% and reduce equity exposure' if lang == 'en'
                               else 'Augmenter obligations (AGG) à 40-50% et réduire actions',
                    'recommended': ['AGG', 'GLD', 'SPY'],
                })
            
            # Recommend defensive assets
            has_defensive = any(ticker in ['AGG', 'GLD'] for ticker in self.tickers)
            if not has_defensive:
                suggestions.append({
                    'priority': 'HIGH',
                    'type': 'info',
                    'title': 'Add Defensive Assets' if lang == 'en' else 'Ajouter Actifs Défensifs',
                    'issue': 'Missing safe-haven assets' if lang == 'en' else 'Actifs refuge absents',
                    'solution': 'Add AGG (bonds 40%) and GLD (gold 15%)' if lang == 'en'
                               else 'Ajouter AGG (obligations 40%) et GLD (or 15%)',
                    'recommended': ['AGG', 'GLD'],
                })
        
        elif profile == "balanced":
            # Check 60/40 ratio
            stock_exposure = sum(self.weights[t] for t in self.tickers 
                                if SECTOR_MAPPING.get(t, "") not in ["Bonds", "Commodities"])
            
            if stock_exposure > 0.70:
                suggestions.append({
                    'priority': 'MEDIUM',
                    'type': 'info',
                    'title': 'Adjust to 60/40 Mix' if lang == 'en' else 'Ajuster vers 60/40',
                    'issue': f'{stock_exposure*100:.0f}% stocks (target 60%)' if lang == 'en' else f'{stock_exposure*100:.0f}% actions (cible 60%)',
                    'solution': 'Increase bonds to reach 40% allocation' if lang == 'en'
                               else 'Augmenter obligations vers 40%',
                    'recommended': ['AGG', 'VXUS', 'VNQ'],
                })
        
        elif profile == "aggressive":
            # Check growth exposure
            has_growth = any(ticker in ['QQQ', 'NVDA', 'TSLA', 'BTC-USD'] for ticker in self.tickers)
            if not has_growth:
                suggestions.append({
                    'priority': 'MEDIUM',
                    'type': 'info',
                    'title': 'Add Growth Assets' if lang == 'en' else 'Ajouter Actifs Croissance',
                    'issue': 'Missing high-growth exposure' if lang == 'en' else 'Exposition croissance insuffisante',
                    'solution': 'Consider QQQ (Nasdaq), NVDA, or 5-10% BTC-USD' if lang == 'en'
                               else 'Considérer QQQ (Nasdaq), NVDA, ou 5-10% BTC-USD',
                    'recommended': ['QQQ', 'NVDA', 'BTC-USD', 'TSLA'],
                })
        
        return suggestions
    
    def stress_test_scenarios(self):
        """Simulate historical crisis scenarios using independent yfinance downloads."""
        scenarios = {
            "2008 Crisis": {
                "start": "2008-09-01", "end": "2009-03-01",
                "market_drop": -0.40,
                "description": "Financial crisis, market -40%",
            },
            "COVID-2020": {
                "start": "2020-02-01", "end": "2020-04-30",
                "market_drop": -0.30,
                "description": "Pandemic crash, market -30%",
            },
            "Inflation 2022": {
                "start": "2022-01-01", "end": "2022-10-01",
                "market_drop": -0.20,
                "description": "Rate hikes, market -20%",
            },
        }

        results = {}
        for name, scenario in scenarios.items():
            try:
                raw = yf.download(
                    self.tickers,
                    start=scenario["start"],
                    end=scenario["end"],
                    auto_adjust=True,
                    progress=False,
                )
                if raw.empty:
                    continue
                prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
                # Keep only tickers that actually downloaded
                available = [t for t in self.tickers if t in prices.columns]
                if not available:
                    continue
                prices = prices[available].dropna(how="all")
                if len(prices) < 5:
                    continue
                weights_arr = np.array([self.weights[t] for t in available])
                weights_arr /= weights_arr.sum()  # renormalise for missing tickers
                rets = prices.pct_change().dropna()
                port_rets = rets @ weights_arr
                total_ret = (1 + port_rets).prod() - 1
                results[name] = {
                    'portfolio_loss': total_ret,
                    'market_loss': scenario['market_drop'],
                    'resilience': 1 - abs(total_ret / scenario['market_drop']),
                    'recovery_days': len(prices),
                    'description': scenario['description'],
                }
            except Exception:
                pass
        return results
    
    def generate_auto_summary(self, lang="en"):
        """
        FIX #9: Auto-generated portfolio summary.
        """
        metrics = self.calculate_metrics()
        robustness = self.calculate_robustness_index()
        
        # Sector analysis
        sectors = {}
        for ticker in self.tickers:
            sector = SECTOR_MAPPING.get(ticker, "Unknown")
            sectors[sector] = sectors.get(sector, 0) + self.weights[ticker]
        
        dominant_sector = max(sectors, key=sectors.get) if sectors else "Unknown"
        sector_exposure = sectors.get(dominant_sector, 0)
        
        # Geography analysis
        geographies = {}
        for ticker in self.tickers:
            geo = GEOGRAPHY_MAPPING.get(ticker, "Unknown")
            geographies[geo] = geographies.get(geo, 0) + self.weights[ticker]
        
        dominant_geo = max(geographies, key=geographies.get) if geographies else "Unknown"
        geo_exposure = geographies.get(dominant_geo, 0)
        
        # Risk level
        vol = metrics['volatility']
        if vol < 0.12:
            risk_level = "low" if lang == "en" else "faible"
        elif vol < 0.20:
            risk_level = "moderate" if lang == "en" else "modérée"
        else:
            risk_level = "elevated" if lang == "en" else "élevée"
        
        # Diversification status
        if len(self.tickers) < 5:
            div_status = "limited" if lang == "en" else "limitée"
        elif len(self.tickers) < 8:
            div_status = "moderate" if lang == "en" else "modérée"
        else:
            div_status = "good" if lang == "en" else "bonne"
        
        if lang == "en":
            summary = f"""
            Your portfolio is **heavily exposed to {dominant_sector}** ({sector_exposure*100:.0f}%) 
            and **{dominant_geo}** markets ({geo_exposure*100:.0f}%).
            Diversification is **{div_status}** across {len(self.tickers)} assets.
            Volatility is **{risk_level}** ({vol*100:.0f}% annual).
            Robustness score: **{robustness['total']}/100 ({robustness['interpretation']})**.
            """
        else:
            interp_fr = {
                "Very Robust": "Très Robuste", "Robust": "Robuste",
                "Fragile": "Fragile", "High Risk": "Risque Élevé",
            }
            interp_display = interp_fr.get(robustness['interpretation'], robustness['interpretation'])
            summary = f"""
            Votre portefeuille est **fortement exposé au secteur {dominant_sector}** ({sector_exposure*100:.0f}%)
            et aux marchés **{dominant_geo}** ({geo_exposure*100:.0f}%).
            La diversification est **{div_status}** sur {len(self.tickers)} actifs.
            La volatilité est **{risk_level}** ({vol*100:.0f}% annuelle).
            Score de robustesse: **{robustness['total']}/100 ({interp_display})**.
            """
        
        return summary.strip()
    
    def calculate_metrics(self):
        """Calculate all performance metrics."""
        returns = self.portfolio_returns
        total_return = (self.portfolio_values.iloc[-1] / self.initial_value) - 1
        years = len(returns) / 252
        annual_return = (1 + total_return) ** (1 / years) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe = annual_return / volatility if volatility > 0 else 0
        
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'final_value': self.portfolio_values.iloc[-1],
            'drawdown_series': drawdown,
        }
    
    def optimize_portfolio(self):
        """Markowitz optimization."""
        expected_returns = self.returns.mean() * 252
        cov_matrix = self.returns.cov() * 252
        
        def negative_sharpe(weights):
            port_return = np.dot(weights, expected_returns)
            port_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            return -(port_return - 0.04) / port_vol
        
        n = len(self.tickers)
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = tuple((0.05, 0.40) for _ in range(n))
        initial = np.array([1/n] * n)
        
        result = minimize(negative_sharpe, initial, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        optimal_weights = dict(zip(self.tickers, result.x))
        optimal_return = np.dot(result.x, expected_returns)
        optimal_vol = np.sqrt(np.dot(result.x, np.dot(cov_matrix, result.x)))
        optimal_sharpe = (optimal_return - 0.04) / optimal_vol
        
        return {
            'weights': optimal_weights,
            'expected_return': optimal_return,
            'volatility': optimal_vol,
            'sharpe': optimal_sharpe
        }

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

        # Navigation
        nav = [
            ("dashboard",    t("dashboard", lang)),
            ("new_analysis", t("new_analysis", lang)),
            ("models",       t("models", lang)),
            ("improve",      t("improve", lang)),
            ("library",      t("library", lang)),
            ("account",      t("account", lang)),
        ]
        for key, label in nav:
            btn_type = "primary" if st.session_state.page == key else "secondary"
            if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
                st.session_state.page = key
                st.rerun()

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


def main():
    init_session_state()
    lang = st.session_state.language
    tier = st.session_state.user_tier
    limits = TIER_LIMITS[tier]

    _sidebar(lang)

    page = st.session_state.page

    # ─────────────────────────────────────────────────────────────────────────
    # ACCOUNT / LOGIN PAGE
    # ─────────────────────────────────────────────────────────────────────────
    if page == "account":
        title = "Your Account" if lang == 'en' else "Votre Compte"
        st.title(title)

        if st.session_state.authenticated and st.session_state.user_email:
            st.success(f"Logged in as **{st.session_state.user_email}** — {TIER_LIMITS[tier]['label']} plan")
            if st.button("Log out" if lang == 'en' else "Se déconnecter"):
                st.session_state.authenticated = False
                st.session_state.user_email = ""
                st.session_state.user_tier = "free"
                st.rerun()
        else:
            st.markdown(
                "Enter your email to access your account. "
                "If you have a Pro subscription, your features will unlock automatically."
                if lang == 'en' else
                "Entrez votre email pour accéder à votre compte. "
                "Vos fonctionnalités Pro seront débloquées automatiquement."
            )
            email_input = st.text_input(
                "Email", placeholder="you@example.com", label_visibility="collapsed"
            )
            if st.button("Continue" if lang == 'en' else "Continuer",
                         type="primary", use_container_width=False):
                if email_input:
                    st.session_state.user_email = email_input
                    st.session_state.user_tier = resolve_tier(email_input)
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    # Guest / demo mode — still let them use the free tier
                    st.session_state.authenticated = True
                    st.session_state.user_tier = "free"
                    st.rerun()

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
        if st.session_state.current_portfolio is None:
            st.title("Dashboard" if lang == 'en' else "Tableau de Bord")
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
            st.markdown(f"""
            <div style="margin-bottom:6px;">
              <h1 style="font-size:1.9rem;font-weight:900;color:#f1f5f9;letter-spacing:-0.03em;margin:0;">
                {"Portfolio Dashboard" if lang == 'en' else "Tableau de Bord"}
              </h1>
              <p style="color:#475569;font-size:0.85rem;margin:4px 0 0;">{sub_info}</p>
            </div>
            """, unsafe_allow_html=True)

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
                    if analyzer.fetch_data():
                        st.session_state.current_portfolio = analyzer
                        st.success(t("analysis_done", lang))
                        st.session_state.page = "dashboard"
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
                        if analyzer.fetch_data():
                            st.session_state.current_portfolio = analyzer
                            ok_msg = f"{model_name} loaded!" if lang == 'en' else f"{model_name} chargé !"
                            st.success(ok_msg)
                            st.session_state.page = "dashboard"
                            st.rerun()
            else:
                locked_msg = "Pro plan required" if lang == 'en' else "Plan Pro requis"
                st.caption(f"🔒 {locked_msg}")

            st.markdown("")

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
                        if new_a.fetch_data():
                            st.session_state.current_portfolio = new_a
                            st.session_state.weights = optimal['weights']
                            st.session_state.optimal_result = None
                            done_msg = "Optimisation applied!" if lang == 'en' else "Optimisation appliquée !"
                            st.success(done_msg)
                            st.rerun()


if __name__ == "__main__":
    main()
