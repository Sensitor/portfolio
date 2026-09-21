"""
Quantitative engine for Sensitor Portfolio Intelligence — public facade.

`analytics` was one module until the V2 restructure. Performance and risk now
live in their own modules, but every call site in the app reaches them through
`analytics as A`, so this module re-exports the whole surface. Importing
`analytics` gives exactly what it always gave.

Where things actually live:

* `_base`        annualisation constants, period slicing, cumulative, drawdowns
* `performance`  return, ratios, rolling windows, drawdown episodes, benchmark,
                 attribution
* `risk`         VaR/CVaR, distribution shape, risk decomposition, correlation,
                 concentration, diversification

Conventions (unchanged): `returns` is a daily simple-return Series; `returns_df`
is one column per ticker; `weights` sums to ~1; 252 trading days a year; the
risk-free rate defaults to 4% and is stated wherever it affects a ratio.
"""

from __future__ import annotations

from ._base import (
    DEFAULT_RF, PERIODS, TRADING_DAYS, available_periods,
    cumulative, drawdown_series, slice_period,
)
from .performance import (
    benchmark_stats, drawdown_episodes, drawdown_summary, monthly_returns,
    perf_stats, return_contribution, rolling_stats,
)
from .risk import (
    avg_pairwise_correlation, concentration, correlation_matrix,
    distribution_stats, diversification_ratio, exposure_breakdown,
    risk_contribution, var_cvar,
)

__all__ = [
    "TRADING_DAYS", "DEFAULT_RF", "PERIODS",
    "slice_period", "available_periods", "cumulative", "drawdown_series",
    "perf_stats", "rolling_stats", "monthly_returns",
    "drawdown_episodes", "drawdown_summary",
    "benchmark_stats", "return_contribution",
    "var_cvar", "distribution_stats", "risk_contribution",
    "correlation_matrix", "avg_pairwise_correlation",
    "concentration", "diversification_ratio", "exposure_breakdown",
]
