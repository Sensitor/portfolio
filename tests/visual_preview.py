"""
Visual preview harness — renders the real Sensitor pages with synthetic data.

Exists so the pages can be looked at, not just asserted on. It imports the actual
page renderers, the actual components and the actual stylesheet, so what appears
here is what the product renders; only the data and the benchmark feed are
synthetic. Nothing in this file is imported by the app.

Run with:  streamlit run tests/visual_preview.py
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Sensitor — Visual Preview", layout="wide",
                   initial_sidebar_state="collapsed")

from sensitor import design, market                      # noqa: E402
from sensitor.context import Context                     # noqa: E402
from sensitor.pages import (                             # noqa: E402
    render_health, render_overview, render_performance, render_risk, render_xray,
)

design.inject_theme()

TICKERS = {
    "SPY": (0.28, 0.010, 0.95), "QQQ": (0.17, 0.013, 0.90),
    "NVDA": (0.08, 0.030, 0.75), "VXUS": (0.12, 0.009, 0.70),
    "AGG": (0.15, 0.003, 0.10), "GLD": (0.10, 0.008, 0.05),
    "BTC-USD": (0.10, 0.036, 0.35),
}


class FakeAnalyzer:
    def __init__(self, returns_df, weights, initial_value=100_000):
        self.tickers = list(returns_df.columns)
        self.weights = dict(weights)
        self.returns = returns_df
        self.initial_value = initial_value
        w = np.array([weights[t] for t in self.tickers])
        self.portfolio_returns = returns_df @ w
        self.portfolio_values = initial_value * (1 + self.portfolio_returns).cumprod()


@st.cache_data
def build_data(days: int = 900, seed: int = 4):
    """Correlated synthetic returns with a drawdown episode, so charts have shape."""
    rng = np.random.default_rng(seed)
    index = pd.bdate_range("2022-03-01", periods=days)
    market_factor = rng.normal(0.0005, 0.009, days)
    market_factor[300:360] -= 0.004          # a visible crisis window
    market_factor[600:640] -= 0.002

    columns = {}
    for ticker, (_, vol, beta) in TICKERS.items():
        columns[ticker] = beta * market_factor + rng.normal(0.0002, vol, days) * (1 - beta * 0.5)
    frame = pd.DataFrame(columns, index=index)
    bench = pd.Series(market_factor, index=index, name="SPY")
    return frame, bench


returns_df, bench_returns = build_data()
weights = {t: v[0] for t, v in TICKERS.items()}
analyzer = FakeAnalyzer(returns_df, weights)

# The sandbox blocks Yahoo, so the benchmark feed is stubbed with the synthetic
# market factor. Everything downstream (alignment, regression, capture) is real.
market.fetch_returns = lambda ticker, start: bench_returns          # type: ignore[assignment]

import portfolio_optimizer_saas as app                    # noqa: E402

PAGES = {
    "Overview": render_overview,
    "Performance": render_performance,
    "Portfolio Health": render_health,
    "Portfolio X-Ray": render_xray,
    "Risk Lab": render_risk,
}

query_page = st.query_params.get("page", "Overview")
query_lang = st.query_params.get("lang", "en")
page_name = query_page if query_page in PAGES else "Overview"

ctx = Context(
    analyzer=analyzer,
    lang=query_lang,
    profile=st.query_params.get("profile", "balanced"),
    period=st.query_params.get("period", "MAX"),
    asset_info=app.ASSET_INFO,
    sector_map=app.SECTOR_MAPPING,
    geo_map=app.GEOGRAPHY_MAPPING,
    is_real=False,
)

PAGES[page_name](ctx)
