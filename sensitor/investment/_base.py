"""
Shared primitives for the investment engine.

Pure computation — no Streamlit, no I/O, no globals. Every function takes plain
pandas/numpy input and returns plain Python containers, so the maths is testable
in isolation and reusable by the report generator, a future API, or batch jobs.

Conventions
-----------
* `returns` is a daily simple-return Series indexed by date.
* `returns_df` is a DataFrame of daily simple returns, one column per ticker.
* `weights` is a {ticker: weight} mapping summing to ~1.
* 252 trading days per year; crypto is treated the same way for comparability,
  which slightly understates its annualised volatility versus a 365-day basis.
* Risk-free rate defaults to 4% annual and is stated wherever it affects a ratio.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252
DEFAULT_RF = 0.04

# =============================================================================

# PERIOD SELECTION
# =============================================================================

PERIODS = ["1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y", "MAX"]

_PERIOD_DAYS = {"1M": 30, "3M": 91, "6M": 182, "1Y": 365, "3Y": 1095, "5Y": 1825}


def slice_period(obj, period: str):
    """Slice a date-indexed Series/DataFrame to a named period. Unknown -> full."""
    if obj is None or len(obj) == 0 or period == "MAX":
        return obj
    end = obj.index[-1]
    if period == "YTD":
        start = pd.Timestamp(year=end.year, month=1, day=1, tz=end.tz)
    elif period in _PERIOD_DAYS:
        start = end - pd.Timedelta(days=_PERIOD_DAYS[period])
    else:
        return obj
    sliced = obj.loc[obj.index >= start]
    # Never hand back a window too short to compute anything meaningful.
    return sliced if len(sliced) >= 5 else obj


def available_periods(returns) -> list[str]:
    """Only offer periods the history can actually cover."""
    if returns is None or len(returns) == 0:
        return ["MAX"]
    span_days = (returns.index[-1] - returns.index[0]).days
    out = [p for p in PERIODS if p in ("YTD", "MAX") or _PERIOD_DAYS[p] <= span_days + 5]
    return out or ["MAX"]


# =============================================================================

# CORE PERFORMANCE
# =============================================================================

def _safe_div(a, b, default=0.0):
    return a / b if b not in (0, None) and not np.isclose(b, 0) else default


def cumulative(returns) -> pd.Series:
    """Growth of 1 unit."""
    return (1 + returns).cumprod()


def drawdown_series(returns) -> pd.Series:
    cum = cumulative(returns)
    return (cum - cum.cummax()) / cum.cummax()

