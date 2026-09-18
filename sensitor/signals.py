"""
Threshold-based observation engine.

Produces the visual alerts shown across the app. Three rules govern everything
here, and they are the reason this is a separate, auditable module:

1. **Every signal states its threshold.** A signal carries the measured value and
   the level it crossed, so the reader can see why it fired and disagree with it.
2. **Observations, never conclusions.** Signals describe what the data shows
   ("NVDA is 17.4% of the book and 31% of its volatility"), not what to do about
   it. No signal tells anyone to buy or sell anything.
3. **Thresholds are configuration, not magic numbers.** They live in `THRESHOLDS`,
   documented, and can be tuned per deployment without touching the logic.

Levels map to the design system's status roles: critical, serious, warning, good.
"""

from __future__ import annotations

from . import analytics as A

# =============================================================================
# CONFIGURABLE THRESHOLDS
# =============================================================================

THRESHOLDS = {
    # Single position as a share of the portfolio.
    "position_critical": 0.30,
    "position_serious": 0.20,
    # One asset's share of total portfolio volatility.
    "risk_share_critical": 0.40,
    "risk_share_serious": 0.28,
    # Risk share divided by capital weight — how much risk each euro carries.
    "risk_ratio_flag": 1.8,
    # Average pairwise correlation across holdings.
    "correlation_high": 0.70,
    "correlation_elevated": 0.55,
    "correlation_good": 0.35,
    # Effective assets (1/HHI) relative to holdings count.
    "effective_ratio_low": 0.45,
    # Single look-through exposure bucket.
    "exposure_critical": 0.55,
    "exposure_serious": 0.40,
    # Annualised volatility.
    "volatility_high": 0.30,
    "volatility_elevated": 0.22,
    # Max drawdown depth.
    "drawdown_severe": 0.40,
    "drawdown_deep": 0.25,
    # Diversification ratio — 1.0 means correlations gave you nothing.
    "div_ratio_good": 1.35,
}

_ORDER = {"critical": 0, "serious": 1, "warning": 2, "good": 3}


def _signal(level, key, title_en, title_fr, body_en, body_fr, footnote_en, footnote_fr):
    return {
        "level": level, "key": key,
        "title": {"en": title_en, "fr": title_fr},
        "body": {"en": body_en, "fr": body_fr},
        "footnote": {"en": footnote_en, "fr": footnote_fr},
    }


# =============================================================================
# RULES
# =============================================================================

def _concentration_signals(conc, weights, out):
    if not conc:
        return
    top1 = conc["top1"]
    top_ticker = max(weights, key=weights.get) if weights else "—"
    t = THRESHOLDS

    if top1 >= t["position_critical"]:
        level, limit = "critical", t["position_critical"]
    elif top1 >= t["position_serious"]:
        level, limit = "serious", t["position_serious"]
    else:
        level, limit = None, None

    if level:
        out.append(_signal(
            level, "concentration",
            "High single-position concentration",
            "Forte concentration sur une position",
            f"{top_ticker} represents {top1 * 100:.1f}% of the portfolio. A move in this "
            f"one holding drives a correspondingly large share of portfolio value.",
            f"{top_ticker} représente {top1 * 100:.1f}% du portefeuille. Un mouvement sur "
            f"cette seule position entraîne une part proportionnellement large de la valeur.",
            f"Threshold: {limit * 100:.0f}% of portfolio in a single position.",
            f"Seuil : {limit * 100:.0f}% du portefeuille sur une seule position.",
        ))

    eff_ratio = conc["effective_assets"] / conc["n_assets"] if conc["n_assets"] else 1
    if eff_ratio < t["effective_ratio_low"] and conc["n_assets"] >= 4:
        out.append(_signal(
            "warning", "effective_assets",
            "Holdings count overstates diversification",
            "Le nombre de lignes surestime la diversification",
            f"{conc['n_assets']} holdings, but the weight distribution is as concentrated "
            f"as an equal-weight portfolio of {conc['effective_assets']:.1f}.",
            f"{conc['n_assets']} lignes, mais la répartition des poids est aussi concentrée "
            f"qu'un portefeuille équipondéré de {conc['effective_assets']:.1f} actifs.",
            f"Threshold: effective assets below {t['effective_ratio_low'] * 100:.0f}% of holdings count (1/HHI).",
            f"Seuil : actifs effectifs sous {t['effective_ratio_low'] * 100:.0f}% du nombre de lignes (1/HHI).",
        ))


def _risk_signals(rc_df, out):
    if rc_df is None or rc_df.empty:
        return
    t = THRESHOLDS
    top = rc_df.iloc[0]

    if top["pct_contribution"] >= t["risk_share_critical"]:
        level, limit = "critical", t["risk_share_critical"]
    elif top["pct_contribution"] >= t["risk_share_serious"]:
        level, limit = "serious", t["risk_share_serious"]
    else:
        level, limit = None, None

    if level:
        out.append(_signal(
            level, "risk_concentration",
            "Risk concentrated in one holding",
            "Risque concentré sur une position",
            f"{top['ticker']} carries {top['pct_contribution'] * 100:.0f}% of total portfolio "
            f"volatility while holding {top['weight'] * 100:.1f}% of the capital.",
            f"{top['ticker']} porte {top['pct_contribution'] * 100:.0f}% de la volatilité "
            f"totale pour {top['weight'] * 100:.1f}% du capital.",
            f"Threshold: {limit * 100:.0f}% of portfolio volatility from one asset (Euler decomposition).",
            f"Seuil : {limit * 100:.0f}% de la volatilité du portefeuille sur un actif (décomposition d'Euler).",
        ))

    stretched = rc_df[(rc_df["risk_ratio"] >= t["risk_ratio_flag"]) & (rc_df["weight"] >= 0.03)]
    if not stretched.empty and (not level or stretched.iloc[0]["ticker"] != top["ticker"]):
        row = stretched.iloc[0]
        out.append(_signal(
            "warning", "risk_ratio",
            "Weight understates risk",
            "Le poids sous-estime le risque",
            f"{row['ticker']} is {row['weight'] * 100:.1f}% of capital but "
            f"{row['pct_contribution'] * 100:.0f}% of risk — {row['risk_ratio']:.1f}x its weight.",
            f"{row['ticker']} pèse {row['weight'] * 100:.1f}% du capital mais "
            f"{row['pct_contribution'] * 100:.0f}% du risque — soit {row['risk_ratio']:.1f}x son poids.",
            f"Threshold: risk share at least {t['risk_ratio_flag']}x capital weight.",
            f"Seuil : part de risque au moins {t['risk_ratio_flag']}x le poids en capital.",
        ))


def _correlation_signals(avg_corr, div_ratio, n_assets, out):
    t = THRESHOLDS
    if n_assets < 2:
        return
    if avg_corr >= t["correlation_high"]:
        out.append(_signal(
            "serious", "correlation",
            "Holdings move together",
            "Les positions évoluent ensemble",
            f"Average pairwise correlation is {avg_corr:.2f}. Holdings this correlated tend "
            f"to decline together, so the position count provides less cushion than it appears to.",
            f"La corrélation moyenne entre positions est de {avg_corr:.2f}. Des actifs aussi "
            f"corrélés baissent généralement ensemble : le nombre de lignes protège moins qu'il n'y paraît.",
            f"Threshold: average pairwise correlation above {t['correlation_high']:.2f}.",
            f"Seuil : corrélation moyenne supérieure à {t['correlation_high']:.2f}.",
        ))
    elif avg_corr >= t["correlation_elevated"]:
        out.append(_signal(
            "warning", "correlation",
            "Elevated correlation between holdings",
            "Corrélation élevée entre les positions",
            f"Average pairwise correlation is {avg_corr:.2f}, and the diversification ratio "
            f"is {div_ratio:.2f} (1.00 would mean correlations provide no volatility reduction).",
            f"La corrélation moyenne est de {avg_corr:.2f}, et le ratio de diversification "
            f"de {div_ratio:.2f} (1,00 signifierait que les corrélations n'apportent aucune réduction de volatilité).",
            f"Threshold: average pairwise correlation above {t['correlation_elevated']:.2f}.",
            f"Seuil : corrélation moyenne supérieure à {t['correlation_elevated']:.2f}.",
        ))
    elif avg_corr <= t["correlation_good"] and div_ratio >= t["div_ratio_good"]:
        out.append(_signal(
            "good", "correlation",
            "Holdings are genuinely diversifying",
            "Les positions se diversifient réellement",
            f"Average pairwise correlation is {avg_corr:.2f} and the diversification ratio is "
            f"{div_ratio:.2f} — the mix is measurably damping portfolio volatility.",
            f"La corrélation moyenne est de {avg_corr:.2f} et le ratio de diversification de "
            f"{div_ratio:.2f} — le mélange réduit effectivement la volatilité du portefeuille.",
            f"Threshold: correlation below {t['correlation_good']:.2f} and diversification ratio above {t['div_ratio_good']:.2f}.",
            f"Seuil : corrélation sous {t['correlation_good']:.2f} et ratio de diversification au-dessus de {t['div_ratio_good']:.2f}.",
        ))


def _exposure_signals(xray, out):
    t = THRESHOLDS
    for dim, label_en, label_fr in (
        ("sector", "sector", "secteur"),
        ("geography", "geographic", "géographique"),
        ("style", "style", "style"),
    ):
        buckets = {k: v for k, v in (xray.get(dim) or {}).items()
                   if k not in ("Not applicable", "Unclassified")}
        if not buckets:
            continue
        bucket, share = next(iter(buckets.items()))
        if share >= t["exposure_critical"]:
            level, limit = "serious", t["exposure_critical"]
        elif share >= t["exposure_serious"]:
            level, limit = "warning", t["exposure_serious"]
        else:
            continue
        out.append(_signal(
            level, f"exposure_{dim}",
            f"Concentrated {label_en} exposure",
            f"Exposition {label_fr} concentrée",
            f"Looking through funds to their underlying holdings, {share * 100:.0f}% of the "
            f"portfolio sits in {bucket} — more than the ticker list alone suggests.",
            f"En analysant les fonds jusqu'à leurs sous-jacents, {share * 100:.0f}% du "
            f"portefeuille se trouve en {bucket} — davantage que ne le suggère la liste des tickers.",
            f"Threshold: {limit * 100:.0f}% in one {label_en} bucket. Look-through data is indicative.",
            f"Seuil : {limit * 100:.0f}% dans un seul bucket {label_fr}. Données de transparisation indicatives.",
        ))


def _drawdown_signals(stats, out):
    t = THRESHOLDS
    max_dd = abs(stats.get("max_drawdown", 0.0))
    vol = stats.get("volatility", 0.0)

    if max_dd >= t["drawdown_severe"]:
        out.append(_signal(
            "serious", "drawdown",
            "Deep historical drawdown",
            "Drawdown historique profond",
            f"The portfolio fell {max_dd * 100:.0f}% from peak to trough over the analysed "
            f"period. Recovering a {max_dd * 100:.0f}% decline requires a "
            f"{(1 / (1 - max_dd) - 1) * 100:.0f}% gain.",
            f"Le portefeuille a chuté de {max_dd * 100:.0f}% du sommet au creux sur la période "
            f"analysée. Récupérer une baisse de {max_dd * 100:.0f}% exige un gain de "
            f"{(1 / (1 - max_dd) - 1) * 100:.0f}%.",
            f"Threshold: peak-to-trough decline beyond {t['drawdown_severe'] * 100:.0f}%.",
            f"Seuil : baisse pic-creux supérieure à {t['drawdown_severe'] * 100:.0f}%.",
        ))

    if vol >= t["volatility_high"]:
        out.append(_signal(
            "warning", "volatility",
            "High realised volatility",
            "Volatilité réalisée élevée",
            f"Annualised volatility is {vol * 100:.1f}%, measured over {stats.get('n_days', 0)} "
            f"trading days of the selected history.",
            f"La volatilité annualisée est de {vol * 100:.1f}%, mesurée sur "
            f"{stats.get('n_days', 0)} jours de bourse de l'historique sélectionné.",
            f"Threshold: annualised volatility above {t['volatility_high'] * 100:.0f}%.",
            f"Seuil : volatilité annualisée supérieure à {t['volatility_high'] * 100:.0f}%.",
        ))


# =============================================================================
# ENTRY POINT
# =============================================================================

def evaluate(*, weights, returns_df, portfolio_returns, xray, stats=None,
             rc_df=None, conc=None, limit: int | None = None) -> list[dict]:
    """
    Run every rule and return signals ordered by severity.

    Each signal carries bilingual title/body/footnote dicts; the caller picks the
    language. Pass `limit` to take only the most severe N.
    """
    stats = stats if stats is not None else A.perf_stats(portfolio_returns)
    conc = conc if conc is not None else A.concentration(weights)
    if rc_df is None and returns_df is not None:
        rc_df = A.risk_contribution(returns_df, weights)

    avg_corr = A.avg_pairwise_correlation(returns_df) if returns_df is not None else 0.0
    div_ratio = A.diversification_ratio(returns_df, weights) if returns_df is not None else 1.0

    out: list[dict] = []
    _concentration_signals(conc, weights, out)
    _risk_signals(rc_df, out)
    _correlation_signals(avg_corr, div_ratio, len(weights), out)
    _exposure_signals(xray or {}, out)
    _drawdown_signals(stats, out)

    out.sort(key=lambda s: _ORDER.get(s["level"], 9))
    return out[:limit] if limit else out
