"""
Market data access for benchmarks.

Thin, cached wrapper around yfinance. Benchmark series are requested on nearly
every page, so they are cached for an hour: without that, each rerun of the
Streamlit script would re-download them and quickly hit Yahoo's rate limiter —
the failure mode that produced "Too Many Requests" in earlier versions.

Failures return None rather than raising. A missing benchmark degrades the page
to portfolio-only figures; it never takes the app down.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

# Ticker -> bilingual display name. Kept small and liquid on purpose.
BENCHMARKS = {
    "SPY": {"en": "S&P 500", "fr": "S&P 500"},
    "QQQ": {"en": "Nasdaq 100", "fr": "Nasdaq 100"},
    "URTH": {"en": "MSCI World", "fr": "MSCI Monde"},
    "VT": {"en": "All-World", "fr": "Monde Entier"},
    "AGG": {"en": "US Bonds", "fr": "Obligations US"},
    "GLD": {"en": "Gold", "fr": "Or"},
}

DEFAULT_BENCHMARK = "SPY"


def benchmark_label(ticker: str, lang: str = "en") -> str:
    return BENCHMARKS.get(ticker, {}).get(lang, ticker)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(ticker: str, start: str) -> pd.Series | None:
    """Daily close series for one ticker, or None if unavailable."""
    try:
        history = yf.Ticker(ticker).history(start=start)
        if history is None or history.empty or "Close" not in history:
            return None
        close = history["Close"].dropna()
        return close if len(close) > 5 else None
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_returns(ticker: str, start: str) -> pd.Series | None:
    """Daily simple returns for one ticker, or None if unavailable."""
    close = fetch_prices(ticker, start)
    if close is None:
        return None
    returns = close.pct_change().dropna()
    return returns if len(returns) > 5 else None


def align(portfolio_returns, benchmark_returns):
    """
    Align two return series on their shared dates.

    Timezone-aware and naive indexes are normalised to naive dates first: yfinance
    hands back tz-aware timestamps whose offsets differ across asset types, and
    joining them directly silently produces an empty intersection.
    """
    if portfolio_returns is None or benchmark_returns is None:
        return None, None

    def _normalise(series):
        series = series.copy()
        index = pd.DatetimeIndex(series.index)
        if index.tz is not None:
            index = index.tz_localize(None)
        series.index = index.normalize()
        return series[~series.index.duplicated(keep="last")]

    left, right = _normalise(portfolio_returns), _normalise(benchmark_returns)
    shared = left.index.intersection(right.index)
    if len(shared) < 20:
        return None, None
    return left.loc[shared], right.loc[shared]
