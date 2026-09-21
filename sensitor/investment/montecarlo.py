"""
Monte Carlo projection.

Draws many possible future paths for a portfolio and summarises them as a
percentile fan plus the probability of hitting chosen thresholds.

Two methods, both offered because they disagree in the way that matters
-----------------------------------------------------------------------
* **Bootstrap** resamples actual historical daily returns. It inherits the real
  distribution's fat tails and skew, which a normal model throws away, but it can
  only ever reshuffle the regime it was given.
* **Parametric** draws from a normal distribution fitted to the same window. It
  is smoother and systematically *understates* extreme outcomes, because daily
  asset returns are not normal.

The gap between the two is informative, so the UI shows which one produced a
result rather than silently picking one.

What this is not
----------------
Neither method predicts anything. Both assume tomorrow's return distribution
resembles the sampled window's — no regime change, no structural break, no
valuation anchor. A ten-year projection from three years of history is an
extrapolation of that window, and the module reports how much history backed the
estimate so the stretch is visible.

No Streamlit here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import analytics as A

MAX_SIMULATIONS = 20_000
MAX_YEARS = 40
PERCENTILES = (10, 25, 50, 75, 90)


def simulate(
    returns,
    *,
    initial_value: float = 100_000.0,
    years: float = 10.0,
    simulations: int = 2_000,
    method: str = "bootstrap",
    contribution_per_year: float = 0.0,
    seed: int | None = 42,
) -> dict:
    """
    Project `years` forward from a daily return history.

    `contribution_per_year` adds a fixed amount, spread evenly across trading
    days, which is how most people actually invest and which changes the outcome
    distribution substantially.

    Returns percentile paths, terminal-value statistics and the inputs used, or
    an empty dict if the history is too short to resample meaningfully.
    """
    returns = returns.dropna() if hasattr(returns, "dropna") else pd.Series(returns)
    if len(returns) < 60:
        return {}

    simulations = int(np.clip(simulations, 100, MAX_SIMULATIONS))
    years = float(np.clip(years, 0.5, MAX_YEARS))
    horizon = max(int(round(years * A.TRADING_DAYS)), 20)

    rng = np.random.default_rng(seed)
    sample = returns.to_numpy()

    if method == "parametric":
        mu, sigma = float(sample.mean()), float(sample.std(ddof=1))
        draws = rng.normal(mu, sigma, size=(simulations, horizon))
    else:
        method = "bootstrap"
        idx = rng.integers(0, len(sample), size=(simulations, horizon))
        draws = sample[idx]

    daily_contribution = contribution_per_year / A.TRADING_DAYS

    if daily_contribution == 0:
        paths = initial_value * np.cumprod(1 + draws, axis=1)
    else:
        # Contributions must be added between compounding steps, so the path has
        # to be walked rather than cumprod'ed in one shot.
        paths = np.empty((simulations, horizon), dtype=float)
        value = np.full(simulations, float(initial_value))
        for day in range(horizon):
            value = value * (1 + draws[:, day]) + daily_contribution
            paths[:, day] = value

    terminal = paths[:, -1]
    invested = initial_value + contribution_per_year * years

    percentile_paths = {
        p: np.percentile(paths, p, axis=0) for p in PERCENTILES
    }

    return {
        "method": method,
        "paths_percentiles": percentile_paths,
        "terminal": terminal,
        "terminal_percentiles": {p: float(np.percentile(terminal, p)) for p in PERCENTILES},
        "median": float(np.median(terminal)),
        "mean": float(terminal.mean()),
        "prob_loss": float((terminal < invested).mean()),
        "prob_below_initial": float((terminal < initial_value).mean()),
        "initial_value": float(initial_value),
        "invested": float(invested),
        "years": years,
        "horizon_days": horizon,
        "simulations": simulations,
        "history_days": len(sample),
        "contribution_per_year": float(contribution_per_year),
    }


def probability_of_reaching(result: dict, targets) -> list[dict]:
    """Share of simulated paths whose terminal value reaches each target."""
    if not result:
        return []
    terminal = result["terminal"]
    out = []
    for target in targets:
        target = float(target)
        out.append({
            "target": target,
            "probability": float((terminal >= target).mean()),
            "reached_by_median": bool(result["median"] >= target),
        })
    return out


def suggest_targets(result: dict, count: int = 4) -> list[float]:
    """
    Round, human-sized thresholds spanning the simulated outcome range.

    Picked from the 10th to 90th percentile so the probabilities shown are
    genuinely uncertain — a target the 10th percentile clears is not a question
    worth asking.
    """
    if not result:
        return []
    low = result["terminal_percentiles"][10]
    high = result["terminal_percentiles"][90]
    if high <= low:
        return []

    raw = np.linspace(low, high, count + 2)[1:-1]
    targets = []
    for value in raw:
        magnitude = 10 ** max(int(np.floor(np.log10(max(value, 1)))) - 1, 0)
        rounded = round(value / magnitude) * magnitude
        if rounded not in targets:
            targets.append(float(rounded))
    return targets


def annualised_outcomes(result: dict) -> dict:
    """Terminal percentiles restated as annualised returns, which compare better."""
    if not result:
        return {}
    years = result["years"]
    initial = result["initial_value"]
    contribution = result["contribution_per_year"]

    # With contributions there is no single rate that maps initial to terminal,
    # so the annualised view is only meaningful for a lump sum.
    if contribution > 0 or initial <= 0 or years <= 0:
        return {}

    return {
        p: (value / initial) ** (1 / years) - 1
        for p, value in result["terminal_percentiles"].items()
    }
