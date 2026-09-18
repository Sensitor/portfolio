"""
Mean-variance optimisation and the efficient frontier.

Builds the frontier by minimising portfolio variance for a grid of target
returns, then locates the three portfolios worth naming: minimum volatility,
maximum Sharpe, and where the user actually is.

What the frontier is
--------------------
A picture of the *past*. Expected returns and the covariance matrix are estimated
from the sample window, and mean-variance optimisation is notoriously sensitive
to the expected-return estimates — small changes in inputs move the optimal
weights a lot. Position bounds are applied by default for exactly this reason:
unconstrained solutions routinely pile the entire book into whichever asset
happened to perform best in the window. Treat the frontier as a way to see the
risk/return geometry of a set of assets, not as an instruction.

No Streamlit here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from . import analytics as A

DEFAULT_BOUNDS = (0.0, 0.40)


def _moments(returns_df: pd.DataFrame, tickers: list[str]):
    expected = returns_df[tickers].mean().to_numpy() * A.TRADING_DAYS
    cov = returns_df[tickers].cov().to_numpy() * A.TRADING_DAYS
    return expected, cov


def _portfolio_stats(w, expected, cov, rf):
    ret = float(w @ expected)
    vol = float(np.sqrt(max(w @ cov @ w, 0.0)))
    sharpe = (ret - rf) / vol if vol > 0 else 0.0
    return ret, vol, sharpe


def _solve(objective, n, constraints, bounds, x0=None):
    result = minimize(
        objective, x0 if x0 is not None else np.full(n, 1 / n),
        method="SLSQP", bounds=[bounds] * n, constraints=constraints,
        options={"maxiter": 400, "ftol": 1e-9},
    )
    return result.x if result.success else None


def _max_attainable_return(expected: np.ndarray, cap: float) -> float:
    """
    Highest expected return reachable under a per-position cap.

    Fills greedily from the best asset down, each at the cap, until fully
    invested — the exact solution for a box-constrained maximum. Averaging the top
    holdings instead (the earlier approach) understates the ceiling and collapses
    the frontier into a stub.
    """
    remaining, total = 1.0, 0.0
    for value in np.sort(expected)[::-1]:
        take = min(cap, remaining)
        total += take * float(value)
        remaining -= take
        if remaining <= 1e-12:
            break
    return total


def efficient_frontier(returns_df: pd.DataFrame, weights: dict,
                       rf: float = A.DEFAULT_RF, points: int = 40,
                       bounds: tuple = DEFAULT_BOUNDS) -> dict:
    """
    Compute the frontier plus the named portfolios.

    Returns None-safe empty dict when there are too few assets or the solver
    cannot find feasible points — a two-asset book has a frontier, a one-asset
    book does not.
    """
    tickers = [t for t in returns_df.columns if t in weights]
    n = len(tickers)
    if n < 2 or len(returns_df) < 60:
        return {}

    expected, cov = _moments(returns_df, tickers)

    # Bounds must be able to reach a fully invested book.
    lower, upper = bounds
    if upper * n < 1.0:
        upper = min(1.0, max(upper, 1.0 / n + 1e-6))
    bounds = (lower, upper)

    budget = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

    min_vol_w = _solve(lambda w: w @ cov @ w, n, [budget], bounds)
    max_sharpe_w = _solve(
        lambda w: -(_portfolio_stats(w, expected, cov, rf)[2]), n, [budget], bounds
    )
    if min_vol_w is None:
        return {}

    lo = float(min_vol_w @ expected)
    hi = _max_attainable_return(expected, upper)
    if hi <= lo:
        hi = lo + abs(lo) * 0.5 + 0.02

    frontier = []
    for target in np.linspace(lo, hi, points):
        constraints = [budget, {"type": "eq",
                                "fun": lambda w, t=target: w @ expected - t}]
        w = _solve(lambda w: w @ cov @ w, n, constraints, bounds, x0=min_vol_w)
        if w is None:
            continue
        ret, vol, sharpe = _portfolio_stats(w, expected, cov, rf)
        frontier.append({"return": ret, "volatility": vol, "sharpe": sharpe,
                         "weights": dict(zip(tickers, w))})

    # Keep the frontier monotone: drop points the solver placed left of a
    # lower-return neighbour, which show up as a hook at the bottom of the curve.
    frontier.sort(key=lambda p: p["volatility"])
    cleaned, best_return = [], -np.inf
    for point in frontier:
        if point["return"] > best_return:
            cleaned.append(point)
            best_return = point["return"]

    current_w = np.array([weights[t] for t in tickers], dtype=float)
    current_w = current_w / current_w.sum() if current_w.sum() > 0 else current_w
    current_ret, current_vol, current_sharpe = _portfolio_stats(current_w, expected, cov, rf)

    out = {
        "tickers": tickers,
        "frontier": cleaned,
        "current": {"return": current_ret, "volatility": current_vol,
                    "sharpe": current_sharpe, "weights": dict(zip(tickers, current_w))},
        "assets": [
            {"ticker": t, "return": float(expected[i]),
             "volatility": float(np.sqrt(cov[i, i])), "weight": float(current_w[i])}
            for i, t in enumerate(tickers)
        ],
        "bounds": bounds,
        "rf": rf,
        "n_days": len(returns_df),
    }

    if min_vol_w is not None:
        ret, vol, sharpe = _portfolio_stats(min_vol_w, expected, cov, rf)
        out["min_volatility"] = {"return": ret, "volatility": vol, "sharpe": sharpe,
                                 "weights": dict(zip(tickers, min_vol_w))}
    if max_sharpe_w is not None:
        ret, vol, sharpe = _portfolio_stats(max_sharpe_w, expected, cov, rf)
        out["max_sharpe"] = {"return": ret, "volatility": vol, "sharpe": sharpe,
                             "weights": dict(zip(tickers, max_sharpe_w))}
    return out


def weight_changes(current: dict, target: dict, threshold: float = 0.005) -> list[dict]:
    """Per-asset deltas between two allocations, largest move first."""
    tickers = sorted(set(current) | set(target))
    changes = []
    for ticker in tickers:
        before = current.get(ticker, 0.0)
        after = target.get(ticker, 0.0)
        if abs(after - before) < threshold:
            continue
        changes.append({"ticker": ticker, "before": before, "after": after,
                        "delta": after - before})
    changes.sort(key=lambda c: abs(c["delta"]), reverse=True)
    return changes
