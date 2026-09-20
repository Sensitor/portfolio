"""
Visual preview harness — renders the real Sensitor pages with synthetic data.

Exists so the pages can be looked at, not just asserted on. It imports the actual
page renderers, the actual components and the actual stylesheet, so what appears
here is what the product renders; only the data source is synthetic. Nothing in
this file is imported by the app.

One synthetic universe drives everything: the portfolio's holdings, the benchmarks
and the factor-proxy legs are all built from a single market factor with plausible
betas. That coherence matters — with independent random draws the regressions on
screen would correctly report no relationship, and the screenshots would show an
empty factor model rather than the page working.

Run with:  streamlit run tests/visual_preview.py
Query params: ?page=Overview&lang=fr&period=1Y&profile=aggressive
"""

from __future__ import annotations

import os
import sys
import tempfile

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Persistence pages write to SQLite. Keep the preview off any real database.
os.environ.setdefault(
    "SENSITOR_DB_PATH",
    os.path.join(tempfile.gettempdir(), "sensitor-preview", "preview.db"),
)

st.set_page_config(page_title="Sensitor — Visual Preview", layout="wide",
                   initial_sidebar_state="collapsed")

from sensitor import design, market                      # noqa: E402
from sensitor.context import Context                     # noqa: E402
from sensitor.pages import (                             # noqa: E402
    render_advisor, render_copilot, render_health, render_optimize, render_overview,
    render_performance, render_portfolios, render_reports, render_risk,
    render_simulator, render_stress, render_xray,
)

design.inject_theme()

# Portfolio holdings and their weights.
HOLDINGS = {
    "SPY": 0.28, "QQQ": 0.17, "NVDA": 0.08, "VXUS": 0.12,
    "AGG": 0.15, "GLD": 0.10, "BTC-USD": 0.10,
}

# Market beta and idiosyncratic volatility for every ticker the app may request —
# holdings, benchmarks and the factor-proxy legs.
BETAS = {
    "SPY": (1.00, 0.004), "VOO": (1.00, 0.004), "QQQ": (1.18, 0.006),
    "VXUS": (0.85, 0.006), "NVDA": (1.60, 0.022), "GLD": (0.04, 0.008),
    "AGG": (0.05, 0.003), "BTC-USD": (0.55, 0.034),
    "URTH": (0.95, 0.004), "VT": (0.92, 0.004),
    "IWM": (1.15, 0.007), "IWD": (0.90, 0.005), "IWF": (1.10, 0.006),
    "MTUM": (1.05, 0.005), "QUAL": (0.98, 0.004), "USMV": (0.72, 0.004),
    "TLT": (-0.10, 0.009), "SHY": (-0.01, 0.001), "IEF": (-0.06, 0.004),
    "HYG": (0.38, 0.004), "TIP": (0.02, 0.004), "DBC": (0.25, 0.011),
    "UUP": (-0.18, 0.004),
}

# Real crisis windows, carved into the synthetic market so scenario replay has
# something to find.
CRISES = (
    ("2007-10-09", "2009-03-09", -0.0022),
    ("2000-03-24", "2002-10-09", -0.0011),
    ("2020-02-19", "2020-03-23", -0.0160),
    ("2022-01-03", "2022-10-12", -0.0011),
    ("2018-10-01", "2018-12-24", -0.0040),
    ("2021-11-10", "2022-11-21", -0.0009),
)

PORTFOLIO_WINDOW = 900   # trading days of history for the portfolio itself


@st.cache_data
def build_universe(seed: int = 21):
    """One market factor; every series derived from it."""
    rng = np.random.default_rng(seed)
    index = pd.bdate_range("1999-01-04", periods=7000)
    core = rng.normal(0.0003, 0.011, len(index))
    for start, end, drift in CRISES:
        core[(index >= start) & (index <= end)] += drift

    market_factor = pd.Series(core, index=index)
    return {
        ticker: beta * market_factor + rng.normal(0.0002, vol, len(index))
        for ticker, (beta, vol) in BETAS.items()
    }


UNIVERSE = build_universe()
RECENT = pd.DataFrame({t: UNIVERSE[t] for t in HOLDINGS}).iloc[-PORTFOLIO_WINDOW:]


class FakeAnalyzer:
    """Minimal stand-in exposing exactly what `Context` reads off the real one."""

    def __init__(self, returns_df, weights, initial_value=100_000):
        self.tickers = list(returns_df.columns)
        self.weights = dict(weights)
        self.returns = returns_df
        self.initial_value = initial_value
        w = np.array([weights[t] for t in self.tickers])
        self.portfolio_returns = returns_df @ w
        self.portfolio_values = initial_value * (1 + self.portfolio_returns).cumprod()


# ── Stubbed market feed ──────────────────────────────────────────────────────
# The sandbox blocks Yahoo, so every fetch is served from the same universe.
# Everything downstream — alignment, regressions, factor construction, scenario
# replay — runs the real code against realistic shapes.

def _fetch_returns(ticker, start):
    series = UNIVERSE.get(ticker)
    if series is None:
        return None
    sliced = series.loc[series.index >= start]
    return sliced if len(sliced) > 5 else None


def _fetch_prices(ticker, start):
    series = _fetch_returns(ticker, start)
    return (1 + series).cumprod() * 100 if series is not None else None


market.fetch_returns = _fetch_returns                              # type: ignore[assignment]
market.fetch_prices = _fetch_prices                                # type: ignore[assignment]
market.fetch_many_returns = lambda tickers, start: {               # type: ignore[assignment]
    t: s for t in tickers if (s := _fetch_returns(t, start)) is not None
}
market.fetch_many_prices = lambda tickers, start: {                # type: ignore[assignment]
    t: s for t in tickers if (s := _fetch_prices(t, start)) is not None
}

import portfolio_optimizer_saas as app                    # noqa: E402

PAGES = {
    "Overview": render_overview,
    "Performance": render_performance,
    "Portfolio Health": render_health,
    "Portfolio X-Ray": render_xray,
    "Risk Lab": render_risk,
    "Stress Lab": render_stress,
    "Optimize": render_optimize,
    "Simulator": render_simulator,
    "Copilot": render_copilot,
    "Portfolios": render_portfolios,
    "Reports": render_reports,
    "Advisor": render_advisor,
}

# The persistence pages file data under a signed-in email.
st.session_state.setdefault("user_email", "preview@sensitor.local")
st.session_state.setdefault("user_tier", "pro")
st.session_state.setdefault("analysis_mode", "simulation")

page_name = st.query_params.get("page", "Overview")
if page_name not in PAGES:
    page_name = "Overview"

ctx = Context(
    analyzer=FakeAnalyzer(RECENT, HOLDINGS),
    lang=st.query_params.get("lang", "en"),
    profile=st.query_params.get("profile", "balanced"),
    period=st.query_params.get("period", "MAX"),
    asset_info=app.ASSET_INFO,
    sector_map=app.SECTOR_MAPPING,
    geo_map=app.GEOGRAPHY_MAPPING,
    is_real=False,
)

PAGES[page_name](ctx)
