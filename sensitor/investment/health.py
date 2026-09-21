"""
Portfolio Health Score.

A composite 0-100 score built from five components, each derived from a stated
metric through a published mapping. The design goals, in order:

1. **Explainable.** Every component returns the metric that drove it and the
   threshold it was measured against, so the UI can answer "why is this 82?"
   without the user trusting a black box.
2. **Continuous.** Components interpolate rather than bucket, so a portfolio does
   not jump four points because volatility moved by 0.1pp.
3. **Profile-aware.** Risk tolerance comes from the user's stated profile, so an
   aggressive investor is not marked down for holding aggressive assets. This is
   what the safe/balanced/aggressive selector actually drives.

The score is a structural diagnostic of a portfolio's shape — diversification,
concentration, realised risk and risk-adjusted return over the sample. It is not a
forecast, not a rating, and not advice; the weights below are a reasoned editorial
choice, not an industry standard, and are exposed here so they can be argued with.
"""

from __future__ import annotations

import numpy as np

from . import analytics as A

# Component weights — must sum to 100.
WEIGHTS = {
    "performance": 25,
    "risk": 25,
    "diversification": 20,
    "concentration": 20,
    "liquidity": 10,
}

# Volatility and drawdown tolerated before a profile starts losing points.
# (comfortable, stretched) — inside `comfortable` scores 100, past `stretched` scores 0.
RISK_TOLERANCE = {
    "safe":       {"vol": (0.06, 0.20), "dd": (0.08, 0.30)},
    "balanced":   {"vol": (0.10, 0.30), "dd": (0.12, 0.45)},
    "aggressive": {"vol": (0.16, 0.45), "dd": (0.20, 0.65)},
}


def _interp(x: float, points: list[tuple[float, float]]) -> float:
    """Piecewise-linear map through (input, score) knots, clamped at both ends."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return float(np.clip(np.interp(x, xs, ys), 0, 100))


def _band(score: float) -> tuple[str, str]:
    """(status tone, label key) for a 0-100 score."""
    if score >= 80:
        return "good", "excellent"
    if score >= 65:
        return "good", "solid"
    if score >= 50:
        return "warning", "mixed"
    if score >= 35:
        return "serious", "fragile"
    return "critical", "weak"


# =============================================================================
# COMPONENTS
# =============================================================================

def _performance_component(stats: dict) -> dict:
    """Risk-adjusted return. Sharpe is the driver; raw return is deliberately not."""
    sharpe = stats.get("sharpe", 0.0)
    score = _interp(sharpe, [(-1.0, 0), (0.0, 25), (0.5, 48), (1.0, 68),
                             (1.5, 84), (2.0, 93), (3.0, 100)])
    return {
        "score": score,
        "metric": sharpe,
        "metric_label": "Sharpe",
        "metric_text": f"{sharpe:.2f}",
        "reference": "1.00",
    }


def _risk_component(stats: dict, profile: str) -> dict:
    """Realised volatility and max drawdown, scored against the profile's tolerance."""
    tol = RISK_TOLERANCE.get(profile, RISK_TOLERANCE["balanced"])
    vol = stats.get("volatility", 0.0)
    max_dd = abs(stats.get("max_drawdown", 0.0))

    vol_lo, vol_hi = tol["vol"]
    dd_lo, dd_hi = tol["dd"]
    vol_score = _interp(vol, [(vol_lo, 100), (vol_hi, 0)])
    dd_score = _interp(max_dd, [(dd_lo, 100), (dd_hi, 0)])
    score = 0.5 * vol_score + 0.5 * dd_score

    return {
        "score": score,
        "metric": vol,
        "metric_label": "Volatility / Max DD",
        "metric_text": f"{vol * 100:.1f}% / {max_dd * 100:.1f}%",
        "reference": f"{vol_hi * 100:.0f}% / {dd_hi * 100:.0f}%",
        "vol_score": vol_score,
        "dd_score": dd_score,
        "profile": profile,
    }


def _diversification_component(returns_df, weights: dict, n_classes: int) -> dict:
    """
    Whether the holdings actually behave differently from one another.

    Average pairwise correlation carries most of the weight: ten holdings that all
    move together are not ten sources of return. The diversification ratio adds the
    volatility-damping view, and asset-class breadth a small structural bonus.
    """
    avg_corr = A.avg_pairwise_correlation(returns_df) if returns_df is not None else 0.0
    div_ratio = A.diversification_ratio(returns_df, weights) if returns_df is not None else 1.0

    corr_score = _interp(avg_corr, [(0.0, 100), (0.3, 82), (0.5, 62),
                                    (0.7, 38), (0.85, 18), (1.0, 0)])
    ratio_score = _interp(div_ratio, [(1.0, 0), (1.15, 40), (1.35, 70),
                                      (1.6, 88), (2.0, 100)])
    class_score = _interp(n_classes, [(1, 20), (2, 55), (3, 78), (4, 92), (5, 100)])

    score = 0.50 * corr_score + 0.30 * ratio_score + 0.20 * class_score
    return {
        "score": score,
        "metric": avg_corr,
        "metric_label": "Avg correlation",
        "metric_text": f"{avg_corr:.2f}",
        "reference": "< 0.50",
        "avg_correlation": avg_corr,
        "diversification_ratio": div_ratio,
        "n_classes": n_classes,
    }


def _concentration_component(conc: dict) -> dict:
    """
    How much of the book sits in its largest positions.

    Driven by effective assets (1/HHI), which captures the whole weight
    distribution, with the largest single position as a separate check so one
    oversized holding cannot hide behind a long tail.
    """
    if not conc:
        return {"score": 50.0, "metric": 0, "metric_label": "Effective assets",
                "metric_text": "—", "reference": "—"}

    eff = conc["effective_assets"]
    top1 = conc["top1"]
    eff_score = _interp(eff, [(1, 0), (2, 25), (3, 45), (5, 68),
                              (8, 86), (12, 96), (20, 100)])
    top1_score = _interp(top1, [(0.10, 100), (0.20, 85), (0.30, 65),
                                (0.45, 35), (0.60, 12), (1.0, 0)])
    score = 0.60 * eff_score + 0.40 * top1_score
    return {
        "score": score,
        "metric": eff,
        "metric_label": "Effective assets",
        "metric_text": f"{eff:.1f} / {conc['n_assets']}",
        "reference": "> 5",
        "effective_assets": eff,
        "top1": top1,
    }


def _liquidity_component(weights: dict, asset_info: dict) -> dict:
    """
    Weight-averaged liquidity of the holdings.

    Uses the 0-100 liquidity field already carried in the asset library. Holdings
    with no entry are assumed reasonably liquid (70) rather than penalised, and the
    coverage ratio is reported so a thin-data portfolio is visible as such.
    """
    total = sum(weights.values()) or 1.0
    known, score_sum = 0.0, 0.0
    for ticker, weight in weights.items():
        info = asset_info.get(ticker, {})
        liquidity = info.get("liquidity")
        if liquidity is None:
            liquidity = 70
        else:
            known += weight / total
        score_sum += (weight / total) * float(liquidity)

    return {
        "score": float(np.clip(score_sum, 0, 100)),
        "metric": score_sum,
        "metric_label": "Weighted liquidity",
        "metric_text": f"{score_sum:.0f}/100",
        "reference": "> 80",
        "coverage": known,
    }


# =============================================================================
# COMPOSITE
# =============================================================================

def compute_health(
    *,
    portfolio_returns,
    returns_df,
    weights: dict,
    asset_info: dict,
    n_asset_classes: int,
    profile: str = "balanced",
    rf: float = A.DEFAULT_RF,
) -> dict:
    """
    Compute the composite score and every component behind it.

    Returns a dict carrying `total`, a `components` mapping (each with its own
    score, weight, driving metric and reference threshold) and the underlying
    stats, so the UI can render the breakdown without recomputing anything.
    """
    stats = A.perf_stats(portfolio_returns, rf)
    conc = A.concentration(weights)

    components = {
        "performance": _performance_component(stats),
        "risk": _risk_component(stats, profile),
        "diversification": _diversification_component(returns_df, weights, n_asset_classes),
        "concentration": _concentration_component(conc),
        "liquidity": _liquidity_component(weights, asset_info),
    }

    total = sum(c["score"] * WEIGHTS[key] for key, c in components.items()) / 100.0

    for key, component in components.items():
        component["weight"] = WEIGHTS[key]
        component["tone"], component["band"] = _band(component["score"])
        component["contribution"] = component["score"] * WEIGHTS[key] / 100.0

    tone, band = _band(total)
    ranked = sorted(components.items(), key=lambda kv: kv[1]["score"])

    return {
        "total": float(total),
        "tone": tone,
        "band": band,
        "components": components,
        "weakest": ranked[0][0],
        "strongest": ranked[-1][0],
        "stats": stats,
        "concentration": conc,
    }


# =============================================================================
# PORTFOLIO DNA
# =============================================================================

DNA_AXES = ["growth", "risk", "diversification", "liquidity", "income", "defensive"]


def portfolio_dna(*, health: dict, xray: dict, stats: dict, weights: dict,
                  asset_info: dict) -> dict:
    """
    Six-axis profile of the portfolio's character, each on a 0-100 scale.

    A shape, not a grade: a concentrated growth book and a defensive income book
    both trace a legitimate profile — they simply trace different ones. Axes reuse
    health components where they mean the same thing so the two views never
    disagree with each other.
    """
    components = health.get("components", {})
    style = xray.get("style", {}) or {}
    classes = xray.get("asset_class", {}) or {}

    growth = _interp(
        style.get("Growth", 0.0) + 0.5 * style.get("High Volatility", 0.0),
        [(0.0, 5), (0.2, 30), (0.4, 55), (0.6, 75), (0.8, 90), (1.0, 100)],
    )
    risk_taken = 100 - components.get("risk", {}).get("score", 50)
    defensive = _interp(
        classes.get("Bonds", 0.0) + classes.get("Cash", 0.0)
        + 0.5 * classes.get("Commodities", 0.0) + 0.4 * style.get("Value", 0.0),
        [(0.0, 5), (0.15, 32), (0.30, 55), (0.50, 78), (0.75, 95), (1.0, 100)],
    )

    total = sum(weights.values()) or 1.0
    income_exposure = 0.0
    for ticker, weight in weights.items():
        raw = str(asset_info.get(ticker, {}).get("dividend_yield", "") or "")
        digits = "".join(ch for ch in raw if ch.isdigit() or ch == ".")
        try:
            yield_pct = float(digits) if digits else 0.0
        except ValueError:
            yield_pct = 0.0
        income_exposure += (weight / total) * yield_pct
    income = _interp(income_exposure, [(0.0, 5), (1.0, 35), (2.0, 60),
                                       (3.5, 85), (5.0, 100)])

    return {
        "growth": growth,
        "risk": risk_taken,
        "diversification": components.get("diversification", {}).get("score", 50),
        "liquidity": components.get("liquidity", {}).get("score", 70),
        "income": income,
        "defensive": defensive,
    }
