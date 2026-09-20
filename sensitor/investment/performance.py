"""
Performance measurement.

Return, risk-adjusted ratios, rolling windows, drawdown episodes, benchmark
regression and per-holding attribution. Split out of `analytics` in the V2
restructure; `analytics` re-exports everything here, so existing call sites are
unaffected.

Shared primitives (`cumulative`, `drawdown_series`, the annualisation constants)
stay in `analytics` because both this module and `risk` need them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as _stats

from ._base import (
    DEFAULT_RF, TRADING_DAYS, _safe_div, cumulative, drawdown_series,
)


def perf_stats(returns, rf: float = DEFAULT_RF) -> dict:
    """Headline performance and risk statistics for a return series."""
    returns = returns.dropna()
    n = len(returns)
    if n < 2:
        return {k: 0.0 for k in (
            "total_return", "cagr", "volatility", "downside_vol", "sharpe",
            "sortino", "calmar", "max_drawdown", "mean_underwater", "best_day",
            "worst_day", "hit_rate", "n_days", "years",
        )}

    total_return = float(cumulative(returns).iloc[-1] - 1)
    years = n / TRADING_DAYS
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 and total_return > -1 else 0.0

    vol = float(returns.std() * np.sqrt(TRADING_DAYS))
    downside = returns[returns < 0]
    downside_vol = float(downside.std() * np.sqrt(TRADING_DAYS)) if len(downside) > 1 else 0.0

    dd = drawdown_series(returns)
    max_dd = float(dd.min())
    # Mean depth across all underwater *days* — distinct from drawdown_summary's
    # avg_drawdown, which averages the depth of each distinct episode.
    mean_underwater = float(dd[dd < 0].mean()) if (dd < 0).any() else 0.0

    return {
        "total_return": total_return,
        "cagr": float(cagr),
        "volatility": vol,
        "downside_vol": downside_vol,
        "sharpe": _safe_div(cagr - rf, vol),
        "sortino": _safe_div(cagr - rf, downside_vol),
        "calmar": _safe_div(cagr, abs(max_dd)),
        "max_drawdown": max_dd,
        "mean_underwater": mean_underwater,
        "best_day": float(returns.max()),
        "worst_day": float(returns.min()),
        "hit_rate": float((returns > 0).mean()),
        "n_days": n,
        "years": years,
        "rf": rf,
    }


def rolling_stats(returns, window: int = 63, rf: float = DEFAULT_RF) -> pd.DataFrame:
    """Rolling annualised return, volatility and Sharpe (default window ~1 quarter)."""
    returns = returns.dropna()
    if len(returns) < window + 5:
        return pd.DataFrame(columns=["return", "volatility", "sharpe"])
    roll_ret = returns.rolling(window).apply(
        lambda w: (1 + w).prod() ** (TRADING_DAYS / window) - 1, raw=True
    )
    roll_vol = returns.rolling(window).std() * np.sqrt(TRADING_DAYS)
    roll_sharpe = (roll_ret - rf) / roll_vol.replace(0, np.nan)
    out = pd.DataFrame(
        {"return": roll_ret, "volatility": roll_vol, "sharpe": roll_sharpe}
    ).dropna()
    return out


def monthly_returns(returns) -> pd.DataFrame:
    """Year x month matrix of compounded monthly returns."""
    returns = returns.dropna()
    if len(returns) < 2:
        return pd.DataFrame()
    monthly = returns.groupby(
        [returns.index.year, returns.index.month]
    ).apply(lambda w: (1 + w).prod() - 1)
    monthly.index.names = ["year", "month"]
    return monthly.unstack("month")


# =============================================================================

# DRAWDOWN ANALYSIS
# =============================================================================

def drawdown_episodes(returns, top: int = 5) -> list[dict]:
    """
    Identify distinct drawdown episodes, deepest first.

    An episode runs from the last equity peak, through the trough, to the day the
    equity curve regains that peak. An episode still underwater at the end of the
    sample is returned with `recovered=False` and no recovery date.
    """
    returns = returns.dropna()
    if len(returns) < 5:
        return []

    cum = cumulative(returns)
    peak = cum.cummax()
    underwater = cum < peak

    episodes, start = [], None
    for i, flag in enumerate(underwater.to_numpy()):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            episodes.append((start, i))
            start = None
    if start is not None:
        episodes.append((start, len(cum) - 1))

    out = []
    for s, e in episodes:
        window = cum.iloc[s:e + 1]
        peak_value = float(peak.iloc[s])
        trough_pos = int(window.to_numpy().argmin())
        trough_value = float(window.iloc[trough_pos])
        depth = trough_value / peak_value - 1
        if depth > -0.005:          # ignore noise shallower than 0.5%
            continue
        recovered = bool(not underwater.iloc[e]) and e < len(cum) - 1
        peak_date = cum.index[max(s - 1, 0)]
        trough_date = window.index[trough_pos]
        recovery_date = cum.index[e] if recovered else None
        out.append({
            "depth": float(depth),
            "peak_date": peak_date,
            "trough_date": trough_date,
            "recovery_date": recovery_date,
            "recovered": recovered,
            "decline_days": int((trough_date - peak_date).days),
            "recovery_days": int((recovery_date - trough_date).days) if recovered else None,
            "underwater_days": int(((recovery_date or cum.index[-1]) - peak_date).days),
        })

    out.sort(key=lambda d: d["depth"])
    return out[:top]


def drawdown_summary(returns) -> dict:
    """Aggregate drawdown profile, including where the portfolio stands today."""
    returns = returns.dropna()
    if len(returns) < 5:
        return {}
    dd = drawdown_series(returns)
    episodes = drawdown_episodes(returns, top=100)
    recovered = [e for e in episodes if e["recovered"]]
    return {
        "current_drawdown": float(dd.iloc[-1]),
        "max_drawdown": float(dd.min()),
        "avg_drawdown": float(np.mean([e["depth"] for e in episodes])) if episodes else 0.0,
        "n_episodes": len(episodes),
        "longest_underwater_days": max((e["underwater_days"] for e in episodes), default=0),
        "avg_recovery_days": float(np.mean([e["recovery_days"] for e in recovered])) if recovered else None,
        "longest_recovery_days": max((e["recovery_days"] for e in recovered), default=None),
        "time_underwater_pct": float((dd < -0.001).mean()),
        "series": dd,
    }


# =============================================================================

# BENCHMARK ANALYSIS
# =============================================================================

def benchmark_stats(port_returns, bench_returns, rf: float = DEFAULT_RF) -> dict:
    """
    Regression and capture statistics of the portfolio against a benchmark.

    Beta/alpha come from an OLS fit of excess daily returns; alpha is annualised.
    Capture ratios are computed on the benchmark's up and down days separately.
    """
    joined = pd.concat([port_returns, bench_returns], axis=1, join="inner").dropna()
    if len(joined) < 20:
        return {}
    joined.columns = ["p", "b"]
    p, b = joined["p"], joined["b"]

    rf_daily = rf / TRADING_DAYS
    slope, intercept, r_value, _, _ = _stats.linregress(b - rf_daily, p - rf_daily)

    active = p - b
    tracking_error = float(active.std() * np.sqrt(TRADING_DAYS))

    p_stats, b_stats = perf_stats(p, rf), perf_stats(b, rf)
    active_return = p_stats["cagr"] - b_stats["cagr"]

    up, down = b > 0, b < 0
    up_capture = _safe_div(
        (1 + p[up]).prod() - 1, (1 + b[up]).prod() - 1, 0.0) if up.any() else 0.0
    down_capture = _safe_div(
        (1 + p[down]).prod() - 1, (1 + b[down]).prod() - 1, 0.0) if down.any() else 0.0

    return {
        "beta": float(slope),
        "alpha": float(intercept * TRADING_DAYS),
        "r_squared": float(r_value ** 2),
        "correlation": float(r_value),
        "tracking_error": tracking_error,
        "information_ratio": _safe_div(active_return, tracking_error),
        "active_return": float(active_return),
        "up_capture": float(up_capture),
        "down_capture": float(down_capture),
        "portfolio": p_stats,
        "benchmark": b_stats,
        "n_days": len(joined),
    }


# =============================================================================

# PERFORMANCE ATTRIBUTION
# =============================================================================

def return_contribution(returns_df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    """
    Per-asset contribution to the portfolio's total return over the window.

    Uses arithmetic linking: each day's weighted asset return is compounded forward
    by the portfolio's growth up to the previous day. Under the daily-rebalanced
    constant-weight assumption the contributions sum exactly to the portfolio's
    total return, so the bars add up to the headline number.
    """
    tickers = [t for t in returns_df.columns if t in weights]
    if not tickers or len(returns_df) < 2:
        return pd.DataFrame()

    w = np.array([weights[t] for t in tickers], dtype=float)
    if w.sum() <= 0:
        return pd.DataFrame()
    w = w / w.sum()

    asset_returns = returns_df[tickers].fillna(0.0)
    port_daily = asset_returns.to_numpy() @ w
    growth = np.concatenate([[1.0], np.cumprod(1 + port_daily)[:-1]])   # value before day t

    contributions = (asset_returns.to_numpy() * w * growth[:, None]).sum(axis=0)
    total = float(np.prod(1 + port_daily) - 1)

    out = pd.DataFrame({
        "ticker": tickers,
        "weight": w,
        "asset_return": [(1 + asset_returns[t]).prod() - 1 for t in tickers],
        "contribution": contributions,
    })
    out["share"] = out["contribution"] / total if abs(total) > 1e-9 else 0.0
    return out.sort_values("contribution", ascending=False).reset_index(drop=True)
