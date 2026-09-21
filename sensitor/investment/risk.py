"""
Risk measurement.

Tail risk, return distribution, risk decomposition, correlation, concentration
and diversification. Split out of `analytics` in the V2 restructure; `analytics`
re-exports everything here, so existing call sites are unaffected.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as _stats

from ._base import TRADING_DAYS, _safe_div


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
