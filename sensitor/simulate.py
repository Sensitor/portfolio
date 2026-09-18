"""
Allocation evaluation — one weight vector in, a full metric bundle out.

The What-if simulator, the portfolio comparison and the Copilot's impact
estimates all need the same question answered: *if the book looked like this
instead, what would every headline number be?* Rather than each feature growing
its own partial version, they all call `evaluate_weights`.

Two properties matter here:

* **Purity.** No Streamlit, no fetching, no session state. The same weights and
  the same returns always produce the same bundle, which is what makes the
  before/after comparisons trustworthy.
* **Same code path as the real portfolio.** The bundle is computed with the same
  functions that produce the live figures, so a simulated Sharpe and a displayed
  Sharpe are never computed two different ways.

What this cannot tell you: every figure is the historical behaviour of a
*fixed* allocation over the sampled window, daily rebalanced. It is a restatement
of the past under different weights, not a projection.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import analytics as A
from . import health as H
from . import xray as X


def normalise(weights: dict, drop_zero: bool = True) -> dict:
    """Rescale to sum to 1, optionally dropping empty positions."""
    cleaned = {k: max(0.0, float(v)) for k, v in weights.items()}
    if drop_zero:
        cleaned = {k: v for k, v in cleaned.items() if v > 1e-9}
    total = sum(cleaned.values())
    if total <= 0:
        return {}
    return {k: v / total for k, v in cleaned.items()}


def portfolio_returns(returns_df: pd.DataFrame, weights: dict) -> pd.Series | None:
    """Daily-rebalanced portfolio returns for an arbitrary weight vector."""
    tickers = [t for t in returns_df.columns if t in weights and weights[t] > 0]
    if not tickers:
        return None
    w = np.array([weights[t] for t in tickers], dtype=float)
    if w.sum() <= 0:
        return None
    w = w / w.sum()
    return returns_df[tickers].fillna(0.0) @ w


def evaluate_weights(
    returns_df: pd.DataFrame,
    weights: dict,
    *,
    asset_info: dict | None = None,
    sector_map: dict | None = None,
    geo_map: dict | None = None,
    profile: str = "balanced",
    rf: float = A.DEFAULT_RF,
    with_health: bool = True,
) -> dict:
    """
    Full metric bundle for one allocation.

    Returns an empty dict when the weights select nothing usable, so callers can
    guard on truthiness rather than on a partially-filled structure.
    """
    # Restrict to tickers the data actually has before anything else. A portfolio
    # can legitimately carry a holding whose download failed, and every downstream
    # call that indexes returns_df by the weight keys would otherwise raise.
    available = set(returns_df.columns)
    weights = normalise({k: v for k, v in weights.items() if k in available})
    if not weights:
        return {}

    returns = portfolio_returns(returns_df, weights)
    if returns is None or len(returns) < 20:
        return {}

    stats = A.perf_stats(returns, rf)
    var = A.var_cvar(returns, 0.95)
    rc = A.risk_contribution(returns_df, weights)
    conc = A.concentration(weights)

    bundle = {
        "weights": weights,
        "returns": returns,
        "stats": stats,
        "var": var,
        "risk_contribution": rc,
        "concentration": conc,
        "avg_correlation": A.avg_pairwise_correlation(returns_df[list(weights)])
        if len(weights) > 1 else 0.0,
        "diversification_ratio": A.diversification_ratio(returns_df, weights),
        "top_risk": (rc.iloc[0].to_dict() if rc is not None and not rc.empty else None),
    }

    if with_health and asset_info is not None:
        xray = X.look_through(weights, asset_info, sector_map or {}, geo_map or {})
        n_classes = max(len({k: v for k, v in xray.get("asset_class", {}).items()
                             if v > 0.01}), 1)
        bundle["xray"] = xray
        bundle["health"] = H.compute_health(
            portfolio_returns=returns,
            returns_df=returns_df[list(weights)],
            weights=weights,
            asset_info=asset_info,
            n_asset_classes=n_classes,
            profile=profile,
            rf=rf,
        )

    return bundle


# =============================================================================
# COMPARISON
# =============================================================================

# Each row: (key, accessor, is_percentage, higher_is_better)
COMPARE_METRICS = [
    ("total_return", lambda b: b["stats"]["total_return"], True, True),
    ("cagr", lambda b: b["stats"]["cagr"], True, True),
    ("volatility", lambda b: b["stats"]["volatility"], True, False),
    ("sharpe", lambda b: b["stats"]["sharpe"], False, True),
    ("sortino", lambda b: b["stats"]["sortino"], False, True),
    ("max_drawdown", lambda b: b["stats"]["max_drawdown"], True, True),
    ("var_95", lambda b: -(b["var"].get("historical_var", 0.0)), True, True),
    ("effective_assets", lambda b: b["concentration"].get("effective_assets", 0), False, True),
    ("health", lambda b: b.get("health", {}).get("total", 0.0), False, True),
]


def compare(bundles: dict) -> list[dict]:
    """
    Line up several evaluated allocations metric by metric.

    `bundles` is {label: bundle}. Returns one row per metric with each label's
    value plus which label leads it, so the UI can mark the leader without
    re-deriving direction per metric.
    """
    labels = [label for label, bundle in bundles.items() if bundle]
    if not labels:
        return []

    rows = []
    for key, accessor, is_pct, higher_better in COMPARE_METRICS:
        values = {}
        for label in labels:
            try:
                values[label] = float(accessor(bundles[label]))
            except (KeyError, TypeError, IndexError):
                continue
        if not values:
            continue
        best = (max(values, key=values.get) if higher_better
                else min(values, key=values.get))
        rows.append({
            "metric": key, "values": values, "best": best,
            "is_pct": is_pct, "higher_is_better": higher_better,
        })
    return rows


def equity_curves(bundles: dict, base: float = 100_000) -> dict:
    """Growth-of-capital series per allocation, all from the same starting base."""
    out = {}
    for label, bundle in bundles.items():
        if not bundle:
            continue
        out[label] = base * A.cumulative(bundle["returns"])
    return out


# =============================================================================
# WEIGHT EDITS
# =============================================================================

def apply_change(weights: dict, ticker: str, new_weight: float,
                 mode: str = "proportional") -> dict:
    """
    Change one position and rebalance the rest back to 100%.

    "proportional" spreads the freed (or required) weight across the other
    holdings in proportion to their current size, which preserves the shape of
    the rest of the book — the sensible default when the point of the change is
    the single position, not a wholesale reallocation.
    """
    weights = dict(weights)
    if ticker not in weights:
        return normalise(weights)

    new_weight = max(0.0, min(1.0, float(new_weight)))
    others = {k: v for k, v in weights.items() if k != ticker}
    others_total = sum(others.values())
    remaining = 1.0 - new_weight

    if others_total <= 0 or not others:
        return {ticker: 1.0}

    if mode == "equal":
        share = remaining / len(others)
        rebalanced = {k: share for k in others}
    else:
        rebalanced = {k: v / others_total * remaining for k, v in others.items()}

    rebalanced[ticker] = new_weight
    return normalise(rebalanced, drop_zero=False)


def cap_position(weights: dict, ticker: str, cap: float) -> dict:
    """Trim a holding down to a cap, leaving it alone if already below."""
    if weights.get(ticker, 0.0) <= cap:
        return dict(weights)
    return apply_change(weights, ticker, cap)


def scale_toward(current: dict, target: dict, fraction: float) -> dict:
    """
    Blend two allocations — `fraction` 0 is current, 1 is target.

    Used to show a partial move toward a suggestion, since the interesting
    question is usually "what would half of this change do?" rather than an
    all-or-nothing switch.
    """
    fraction = max(0.0, min(1.0, float(fraction)))
    tickers = set(current) | set(target)
    blended = {
        t: current.get(t, 0.0) * (1 - fraction) + target.get(t, 0.0) * fraction
        for t in tickers
    }
    return normalise(blended)
