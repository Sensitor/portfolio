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


def normalise_index(obj):
    """
    Force a Series or DataFrame onto naive, midnight-normalised dates.

    yfinance returns timezone-aware timestamps whose offsets differ by asset type
    (US equities, crypto, European funds), so joining two series straight from the
    API can intersect to nothing. Every join in the app goes through this first.
    """
    if obj is None or len(obj) == 0:
        return obj
    out = obj.copy()
    index = pd.DatetimeIndex(out.index)
    if index.tz is not None:
        index = index.tz_localize(None)
    out.index = index.normalize()
    return out[~out.index.duplicated(keep="last")]


def align(portfolio_returns, benchmark_returns):
    """
    Align two return series on their shared dates.

    Timezone-aware and naive indexes are normalised to naive dates first: yfinance
    hands back tz-aware timestamps whose offsets differ across asset types, and
    joining them directly silently produces an empty intersection.
    """
    if portfolio_returns is None or benchmark_returns is None:
        return None, None

    left, right = normalise_index(portfolio_returns), normalise_index(benchmark_returns)
    shared = left.index.intersection(right.index)
    if len(shared) < 20:
        return None, None
    return left.loc[shared], right.loc[shared]


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_many_returns(tickers: tuple, start: str) -> dict:
    """
    Daily returns for several tickers. Missing ones are simply absent from the
    result, so callers decide what to do about a gap rather than getting a silent
    zero series. Takes a tuple because Streamlit's cache key must be hashable.
    """
    out = {}
    for ticker in tickers:
        series = fetch_returns(ticker, start)
        if series is not None:
            out[ticker] = series
    return out


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_many_prices(tickers: tuple, start: str) -> dict:
    """Price history for several tickers, same contract as fetch_many_returns."""
    out = {}
    for ticker in tickers:
        series = fetch_prices(ticker, start)
        if series is not None:
            out[ticker] = series
    return out
