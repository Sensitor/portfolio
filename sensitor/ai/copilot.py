"""
Portfolio Copilot — observations paired with a change you can simulate.

Each item this module produces has three parts:

1. **An observation** about the current allocation, with the numbers that
   triggered it and the threshold they crossed.
2. **A mechanism** — why that pattern matters, in terms of how portfolios behave,
   not in terms of what markets will do.
3. **A concrete, simulatable change** — a complete weight vector the caller can
   run through `simulate.evaluate_weights` to see the effect on every metric.

Framing rules, deliberately strict
----------------------------------
Nothing here is advice and nothing is stated as certain. An item says what the
data shows and offers a hypothesis to test; it never claims the change would
improve outcomes, because the simulation can only restate the past under
different weights. The proposed change exists so the user can *see* the
trade-off — trimming a volatile winner reduces risk and usually reduces past
return too, and the impact table will show both.

Thresholds come from `signals.THRESHOLDS`, so the Copilot and the alert badges
elsewhere in the app never disagree about what counts as concentrated.

No Streamlit here.
"""

from __future__ import annotations

import numpy as np

from ..investment import analytics as A
from ..investment import simulate as SI
from .signals import THRESHOLDS, position_thresholds

# Minimum weight a position needs before a change to it is worth proposing.
MIN_MATERIAL_WEIGHT = 0.03

# Minimum size of a proposed move, in weight. Below this the change is noise: it
# would not survive a rebalance and presenting it as a finding overstates it.
MIN_MATERIAL_CHANGE = 0.03


def _item(key, level, title_en, title_fr, why_en, why_fr, evidence, proposed,
          change_en, change_fr):
    return {
        "key": key,
        "level": level,
        "title": {"en": title_en, "fr": title_fr},
        "why": {"en": why_en, "fr": why_fr},
        "change": {"en": change_en, "fr": change_fr},
        "evidence": evidence,
        "proposed_weights": proposed,
    }


# =============================================================================
# RULES
# =============================================================================

def _oversized_position(weights, conc, out, asset_info=None, sector_map=None):
    if not conc:
        return
    top1 = conc["top1"]
    ticker = max(weights, key=weights.get)

    # A broad index fund is judged against a much wider limit than a single name.
    critical_limit, limit = position_thresholds(ticker, asset_info, sector_map, {})
    if top1 < limit:
        return

    target = limit
    if top1 - target < MIN_MATERIAL_CHANGE:
        return
    proposed = SI.cap_position(weights, ticker, target)

    out.append(_item(
        f"position:{ticker}", "critical" if top1 >= critical_limit else "serious",
        "Large single position", "Position unique importante",
        (f"{ticker} is {top1 * 100:.1f}% of the portfolio. At this size its individual "
         f"moves drive a large share of total portfolio value, so the book's outcome "
         f"depends heavily on one company or fund."),
        (f"{ticker} représente {top1 * 100:.1f}% du portefeuille. À cette taille, ses "
         f"mouvements propres déterminent une large part de la valeur totale : le résultat "
         f"du portefeuille dépend donc fortement d'une seule entreprise ou d'un seul fonds."),
        [
            {"label_en": "Current weight", "label_fr": "Poids actuel",
             "value": f"{top1 * 100:.1f}%"},
            {"label_en": "Threshold", "label_fr": "Seuil",
             "value": f"{limit * 100:.0f}%"},
        ],
        proposed,
        f"Reduce {ticker} to {target * 100:.0f}%, redistributing proportionally",
        f"Réduire {ticker} à {target * 100:.0f}%, en redistribuant proportionnellement",
    ))


def _risk_concentration(weights, rc, out):
    if rc is None or rc.empty:
        return
    top = rc.iloc[0]
    ticker = str(top["ticker"])
    risk_share = float(top["pct_contribution"])
    weight = float(top["weight"])

    if weight < MIN_MATERIAL_WEIGHT:
        return

    ratio = float(top["risk_ratio"]) if weight > 0 else 1.0

    # Two distinct situations are worth raising, and "largest holding" is not one
    # of them. In any book the biggest position naturally carries the biggest
    # share of risk; that is proportionality, not concentration. What matters is
    # either an outright dominant share, or a share clearly out of line with the
    # capital behind it.
    dominant = risk_share >= THRESHOLDS["risk_share_critical"]
    disproportionate = (risk_share >= THRESHOLDS["risk_share_serious"]
                        and ratio >= THRESHOLDS["risk_ratio_flag"])
    if not (dominant or disproportionate):
        return

    # Trim toward the weight at which this holding's risk share would sit near
    # the serious threshold, approximating the relationship as linear in weight.
    scale = risk_share / weight if weight > 0 else 1.0
    target = max(0.02, min(weight, THRESHOLDS["risk_share_serious"] / max(scale, 1e-6)))
    if weight - target < MIN_MATERIAL_CHANGE:
        return

    out.append(_item(
        f"risk:{ticker}",
        "critical" if risk_share >= THRESHOLDS["risk_share_critical"] else "serious",
        "Risk concentrated in one holding", "Risque concentré sur une position",
        (f"{ticker} carries {risk_share * 100:.0f}% of total portfolio volatility from "
         f"{weight * 100:.1f}% of the capital — {top['risk_ratio']:.1f} times its weight. "
         f"That gap comes from its own volatility and from how closely it moves with the "
         f"rest of the book, so its weight alone understates how much it drives outcomes."),
        (f"{ticker} porte {risk_share * 100:.0f}% de la volatilité totale pour "
         f"{weight * 100:.1f}% du capital — soit {top['risk_ratio']:.1f} fois son poids. "
         f"Cet écart vient de sa volatilité propre et de sa co-évolution avec le reste du "
         f"portefeuille : son poids seul sous-estime son influence sur le résultat."),
        [
            {"label_en": "Risk contribution", "label_fr": "Contribution au risque",
             "value": f"{risk_share * 100:.0f}%"},
            {"label_en": "Capital weight", "label_fr": "Poids en capital",
             "value": f"{weight * 100:.1f}%"},
            {"label_en": "Asset volatility", "label_fr": "Volatilité de l'actif",
             "value": f"{float(top['asset_volatility']) * 100:.1f}%"},
        ],
        SI.apply_change(weights, ticker, target),
        f"Reduce {ticker} from {weight * 100:.0f}% to {target * 100:.0f}%",
        f"Réduire {ticker} de {weight * 100:.0f}% à {target * 100:.0f}%",
    ))


def _correlated_pair(weights, returns_df, out):
    tickers = [t for t in returns_df.columns
               if weights.get(t, 0) >= MIN_MATERIAL_WEIGHT]
    if len(tickers) < 2:
        return

    # .to_numpy() can hand back a read-only view of pandas' own buffer, so the
    # diagonal mask has to be written into a copy.
    corr = returns_df[tickers].corr().to_numpy().astype(float).copy()
    np.fill_diagonal(corr, np.nan)
    if np.all(np.isnan(corr)):
        return

    i, j = np.unravel_index(np.nanargmax(corr), corr.shape)
    value = float(corr[i, j])
    if value < THRESHOLDS["correlation_high"]:
        return

    a, b = tickers[i], tickers[j]
    # Trim the one contributing less return per unit of risk over the window.
    stats_a = A.perf_stats(returns_df[a])
    stats_b = A.perf_stats(returns_df[b])
    weaker = a if stats_a["sharpe"] <= stats_b["sharpe"] else b
    stronger = b if weaker == a else a

    weight = weights.get(weaker, 0.0)
    target = max(0.02, weight * 0.5)
    if weight - target < MIN_MATERIAL_CHANGE:
        return

    out.append(_item(
        f"correlation:{weaker}", "warning",
        "Two holdings move almost together", "Deux positions évoluent presque ensemble",
        (f"{a} and {b} have a correlation of {value:.2f} over this period. Holding both at "
         f"size adds capital to the same underlying exposure without adding a distinct "
         f"source of return, so the position count overstates how diversified the book is. "
         f"{weaker} has the lower Sharpe of the two over this window."),
        (f"{a} et {b} affichent une corrélation de {value:.2f} sur la période. Détenir les "
         f"deux en taille ajoute du capital à la même exposition sous-jacente sans ajouter "
         f"de source de rendement distincte : le nombre de lignes surestime donc la "
         f"diversification réelle. {weaker} a le Sharpe le plus faible des deux sur cette fenêtre."),
        [
            {"label_en": "Correlation", "label_fr": "Corrélation", "value": f"{value:.2f}"},
            {"label_en": f"Sharpe {a}", "label_fr": f"Sharpe {a}",
             "value": f"{stats_a['sharpe']:.2f}"},
            {"label_en": f"Sharpe {b}", "label_fr": f"Sharpe {b}",
             "value": f"{stats_b['sharpe']:.2f}"},
        ],
        SI.apply_change(weights, weaker, target),
        f"Halve {weaker} to {target * 100:.0f}% (keeping {stronger})",
        f"Diviser {weaker} par deux à {target * 100:.0f}% (en conservant {stronger})",
    ))


def _exposure_concentration(weights, xray, asset_info, sector_map, out):
    buckets = {k: v for k, v in (xray.get("sector") or {}).items()
               if k not in ("Not applicable", "Unclassified")}
    if not buckets:
        return
    bucket, share = next(iter(buckets.items()))
    if share < THRESHOLDS["exposure_serious"]:
        return

    # Attribute the bucket to the holding contributing most of it.
    from ..investment import xray as X
    contributions = {}
    total = sum(weights.values()) or 1.0
    for ticker, weight in weights.items():
        profile = X.resolve_profile(ticker, asset_info, sector_map, {})
        contributions[ticker] = (weight / total) * profile.get("sector", {}).get(bucket, 0.0)

    driver = max(contributions, key=contributions.get)
    driver_share = contributions[driver]
    if driver_share <= 0 or weights.get(driver, 0) < MIN_MATERIAL_WEIGHT:
        return

    weight = weights[driver]
    target = max(0.02, weight * 0.6)
    if weight - target < MIN_MATERIAL_CHANGE:
        return

    out.append(_item(
        f"exposure:{bucket}", "warning",
        f"Concentrated {bucket} exposure", f"Exposition {bucket} concentrée",
        (f"Once funds are resolved into their underlying holdings, {share * 100:.0f}% of the "
         f"portfolio sits in {bucket}. {driver} accounts for {driver_share * 100:.0f} "
         f"percentage points of that, more than its ticker weight suggests, because the "
         f"exposure arrives through several holdings at once."),
        (f"Une fois les fonds décomposés en leurs sous-jacents, {share * 100:.0f}% du "
         f"portefeuille se trouve en {bucket}. {driver} en représente "
         f"{driver_share * 100:.0f} points, davantage que ne le suggère son poids de ticker, "
         f"car l'exposition arrive par plusieurs positions à la fois."),
        [
            {"label_en": "Resolved exposure", "label_fr": "Exposition résolue",
             "value": f"{share * 100:.0f}%"},
            {"label_en": "Largest source", "label_fr": "Source principale", "value": driver},
            {"label_en": "Threshold", "label_fr": "Seuil",
             "value": f"{THRESHOLDS['exposure_serious'] * 100:.0f}%"},
        ],
        SI.apply_change(weights, driver, target),
        f"Reduce {driver} from {weight * 100:.0f}% to {target * 100:.0f}%",
        f"Réduire {driver} de {weight * 100:.0f}% à {target * 100:.0f}%",
    ))


def _uneven_weights(weights, conc, out):
    if not conc or conc["n_assets"] < 4:
        return
    efficiency = conc.get("diversification_efficiency", 1.0)
    if efficiency >= THRESHOLDS["effective_ratio_low"]:
        return

    equal = {t: 1 / len(weights) for t in weights}
    out.append(_item(
        "equalise", "warning",
        "Weights are heavily uneven", "Les poids sont très inégaux",
        (f"The book holds {conc['n_assets']} positions but is as concentrated as an "
         f"equal-weight portfolio of {conc['effective_assets']:.1f}. Most of the capital sits "
         f"in a few names, so the smaller positions have little influence on the outcome "
         f"either way."),
        (f"Le portefeuille compte {conc['n_assets']} positions mais est aussi concentré "
         f"qu'un portefeuille équipondéré de {conc['effective_assets']:.1f}. L'essentiel du "
         f"capital se trouve sur quelques lignes : les petites positions n'influencent donc "
         f"presque pas le résultat, dans un sens comme dans l'autre."),
        [
            {"label_en": "Holdings", "label_fr": "Positions", "value": str(conc["n_assets"])},
            {"label_en": "Effective assets", "label_fr": "Actifs effectifs",
             "value": f"{conc['effective_assets']:.1f}"},
            {"label_en": "Largest position", "label_fr": "Position la plus grande",
             "value": f"{conc['top1'] * 100:.0f}%"},
        ],
        equal,
        "Equal-weight every holding",
        "Équipondérer toutes les positions",
    ))


# =============================================================================
# ENTRY POINT
# =============================================================================

_ORDER = {"critical": 0, "serious": 1, "warning": 2, "good": 3}


def diagnose(*, weights, returns_df, risk_contribution, concentration, xray,
             asset_info, sector_map, dismissed=(), limit: int | None = None) -> list[dict]:
    """
    Produce the Copilot's items, most severe first.

    `dismissed` is a collection of item keys the user has set aside; they are
    filtered out here rather than hidden in the UI, so a dismissed item cannot
    reappear through a different code path.
    """
    out: list[dict] = []
    _oversized_position(weights, concentration, out, asset_info, sector_map)
    _risk_concentration(weights, risk_contribution, out)
    _correlated_pair(weights, returns_df, out)
    _exposure_concentration(weights, xray, asset_info, sector_map, out)
    _uneven_weights(weights, concentration, out)

    dismissed = set(dismissed)
    out = [item for item in out if item["key"] not in dismissed]
    out.sort(key=lambda i: _ORDER.get(i["level"], 9))
    out = _deduplicate(out)
    return out[:limit] if limit else out


def _deduplicate(items: list[dict], tolerance: float = 0.01) -> list[dict]:
    """
    Drop items whose proposed allocation matches one already kept.

    Different rules legitimately converge on the same change — trimming the top
    risk contributor and trimming the driver of a concentrated sector are often
    the same trade. Showing it twice would imply two independent findings, and
    simulating it twice would show identical impact tables. The more severe item
    survives, since the list is already sorted by severity.
    """
    kept: list[dict] = []
    for item in items:
        proposal = item["proposed_weights"]
        duplicate = any(
            _same_allocation(proposal, existing["proposed_weights"], tolerance)
            for existing in kept
        )
        if not duplicate:
            kept.append(item)
    return kept


def _same_allocation(a: dict, b: dict, tolerance: float) -> bool:
    tickers = set(a) | set(b)
    return all(abs(a.get(t, 0.0) - b.get(t, 0.0)) <= tolerance for t in tickers)


def impact(before: dict, after: dict) -> list[dict]:
    """
    Metric-by-metric before/after for a proposed change.

    Direction is carried per metric (lower volatility is an improvement, lower
    return is not), so the UI never has to guess which way is better.
    """
    if not before or not after:
        return []

    rows = [
        ("cagr", before["stats"]["cagr"], after["stats"]["cagr"], True, True),
        ("volatility", before["stats"]["volatility"], after["stats"]["volatility"], True, False),
        ("sharpe", before["stats"]["sharpe"], after["stats"]["sharpe"], False, True),
        ("max_drawdown", before["stats"]["max_drawdown"], after["stats"]["max_drawdown"], True, True),
        ("var_95", -before["var"].get("historical_var", 0.0),
         -after["var"].get("historical_var", 0.0), True, True),
        ("effective_assets", before["concentration"].get("effective_assets", 0),
         after["concentration"].get("effective_assets", 0), False, True),
    ]
    if before.get("health") and after.get("health"):
        rows.append(("health", before["health"]["total"], after["health"]["total"], False, True))

    out = []
    for key, before_value, after_value, is_pct, higher_better in rows:
        delta = after_value - before_value

        # A verdict on a change too small to show at the displayed precision is
        # noise dressed as a finding — "-1.5% -> -1.5% worsens" reads as a defect
        # when nothing moved. Anything under half a percent of the starting value
        # (or under the display floor) is reported as unchanged.
        floor = max(abs(before_value) * 0.005, 5e-4 if is_pct else 5e-3)
        if abs(delta) < floor:
            improved = None
        else:
            improved = (delta > 0) if higher_better else (delta < 0)

        out.append({
            "metric": key,
            "before": float(before_value),
            "after": float(after_value),
            "delta": float(delta),
            "is_pct": is_pct,
            "higher_is_better": higher_better,
            "improved": improved,
        })
    return out
