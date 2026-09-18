"""
Quantitative engine for Sensitor Portfolio Intelligence.

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
from scipy import stats as _stats

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
# TAIL RISK
# =============================================================================

def var_cvar(returns, level: float = 0.95, horizon_days: int = 1) -> dict:
    """
    Value at Risk and Conditional VaR (Expected Shortfall).

    Returned as positive loss magnitudes. `historical` is the empirical quantile;
    `parametric` assumes normally distributed returns, which understates tail loss
    for the fat-tailed series typical of equities and crypto — both are reported so
    the gap between them is visible rather than hidden behind one number.
    """
    returns = returns.dropna()
    if len(returns) < 20:
        return {}
    alpha = 1 - level
    scale = np.sqrt(horizon_days)

    hist_var = float(-np.percentile(returns, alpha * 100)) * scale
    tail = returns[returns <= np.percentile(returns, alpha * 100)]
    hist_cvar = float(-tail.mean()) * scale if len(tail) else hist_var

    mu, sigma = float(returns.mean()), float(returns.std())
    z = _stats.norm.ppf(alpha)
    param_var = float(-(mu + z * sigma)) * scale
    param_cvar = float(-(mu - sigma * _stats.norm.pdf(z) / alpha)) * scale

    return {
        "level": level,
        "horizon_days": horizon_days,
        "historical_var": hist_var,
        "historical_cvar": hist_cvar,
        "parametric_var": param_var,
        "parametric_cvar": param_cvar,
    }


def distribution_stats(returns) -> dict:
    """Shape of the daily return distribution — what the averages hide."""
    returns = returns.dropna()
    if len(returns) < 20:
        return {}
    arr = returns.to_numpy()
    return {
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "std": float(arr.std(ddof=1)),
        "skewness": float(_stats.skew(arr)),
        "kurtosis": float(_stats.kurtosis(arr)),   # excess: 0 == normal
        "p1": float(np.percentile(arr, 1)),
        "p5": float(np.percentile(arr, 5)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "n": len(arr),
    }


# =============================================================================
# RISK DECOMPOSITION — where the risk actually comes from
# =============================================================================

def risk_contribution(returns_df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    """
    Decompose portfolio volatility into per-asset contributions.

    marginal  (MCTR) = d(sigma_p)/d(w_i) = (Sigma w)_i / sigma_p
                       how much portfolio vol moves per unit of extra weight
    component (CCTR) = w_i * MCTR_i, and sum(CCTR) == sigma_p exactly (Euler)
    percent   (PCTR) = CCTR_i / sigma_p

    The gap between `weight` and `pct_contribution` is the point of the table: a
    10% position in a volatile, highly-correlated asset can carry a far larger
    share of total risk than its weight suggests.
    """
    tickers = [t for t in returns_df.columns if t in weights]
    if not tickers:
        return pd.DataFrame()

    w = np.array([weights[t] for t in tickers], dtype=float)
    if w.sum() <= 0:
        return pd.DataFrame()
    w = w / w.sum()

    cov = returns_df[tickers].cov().to_numpy() * TRADING_DAYS
    port_var = float(w @ cov @ w)
    port_vol = np.sqrt(port_var)
    if port_vol <= 0:
        return pd.DataFrame()

    mctr = (cov @ w) / port_vol
    cctr = w * mctr
    pctr = cctr / port_vol

    asset_vol = np.sqrt(np.diag(cov))
    out = pd.DataFrame({
        "ticker": tickers,
        "weight": w,
        "asset_volatility": asset_vol,
        "marginal": mctr,
        "component": cctr,
        "pct_contribution": pctr,
        "risk_ratio": np.divide(pctr, w, out=np.zeros_like(pctr), where=w > 0),
    })
    return out.sort_values("pct_contribution", ascending=False).reset_index(drop=True)


def correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    return returns_df.corr()


def avg_pairwise_correlation(returns_df: pd.DataFrame) -> float:
    if returns_df.shape[1] < 2:
        return 0.0
    corr = returns_df.corr().to_numpy()
    upper = corr[np.triu_indices_from(corr, k=1)]
    return float(np.nanmean(upper)) if len(upper) else 0.0


# =============================================================================
# CONCENTRATION & DIVERSIFICATION
# =============================================================================

def concentration(weights: dict) -> dict:
    """
    Concentration metrics.

    HHI is the Herfindahl-Hirschman Index (sum of squared weights): 1/n for an
    equal-weight book, 1.0 for a single position. `effective_assets` = 1/HHI is the
    equal-weight portfolio size that would be equally concentrated — so 10 holdings
    with an effective count of 4.8 are concentrated like an equal-weight book of ~5.
    """
    w = np.array([v for v in weights.values() if v is not None], dtype=float)
    if w.size == 0 or w.sum() <= 0:
        return {}
    w = np.sort(w / w.sum())[::-1]
    hhi = float((w ** 2).sum())
    n = len(w)
    return {
        "n_assets": n,
        "top1": float(w[0]),
        "top3": float(w[:3].sum()),
        "top5": float(w[:5].sum()),
        "hhi": hhi,
        "effective_assets": 1 / hhi if hhi > 0 else 0.0,
        "diversification_efficiency": (1 / hhi) / n if hhi > 0 and n else 0.0,
        "sorted_weights": w.tolist(),
    }


def diversification_ratio(returns_df: pd.DataFrame, weights: dict) -> float:
    """
    (weighted average of asset vols) / (portfolio vol).

    1.0 means correlations gave you nothing; higher means the mix is genuinely
    damping risk. This is the correlation-aware complement to 1/HHI, which only
    looks at weights.
    """
    tickers = [t for t in returns_df.columns if t in weights]
    if len(tickers) < 2:
        return 1.0
    w = np.array([weights[t] for t in tickers], dtype=float)
    if w.sum() <= 0:
        return 1.0
    w = w / w.sum()
    cov = returns_df[tickers].cov().to_numpy() * TRADING_DAYS
    port_vol = np.sqrt(float(w @ cov @ w))
    weighted_vol = float(w @ np.sqrt(np.diag(cov)))
    return _safe_div(weighted_vol, port_vol, 1.0)


def exposure_breakdown(weights: dict, mapping: dict, default: str = "Other") -> dict:
    """Aggregate weights by any {ticker: category} mapping, largest first."""
    out: dict[str, float] = {}
    for ticker, weight in weights.items():
        key = mapping.get(ticker, default)
        out[key] = out.get(key, 0.0) + float(weight)
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))


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
