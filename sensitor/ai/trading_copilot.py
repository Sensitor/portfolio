"""
Trading Copilot — observations about a book, with the arithmetic behind them.

The counterpart to `copilot.py`, and deliberately a weaker instrument. The
portfolio Copilot can offer a change and simulate it, because a weight vector
is a complete description of a portfolio and the past can be replayed under it.
A trading book has no equivalent: there is no "what if I had risked less" that
can be replayed, because the trades taken would have been different ones.

So this module offers **no proposed change and no simulation**. Each item is an
observation, the numbers that triggered it, and the threshold they crossed. That
is a real limit, and pretending otherwise — "reduce your size after losses and
your expectancy would be X" — would be inventing a counterfactual the data
cannot support.

What separates an item from a psychology finding
------------------------------------------------
`psychology.findings()` compares two groups of trades and says they correlate.
The items here are threshold crossings on a single figure: the stop coverage is
below 70%, the sizing varies more than the usual, the worst losing run was
longer than chance explains. Both are descriptive; these carry a threshold that
can be pointed at.

Framing rules, the same as everywhere
--------------------------------------
* Nothing is advice and nothing is certain.
* Every item carries its sample size, and none is raised below the engine's
  threshold for the statistic it rests on.
* Where a figure has a known caveat — R covering only part of the book, stop
  discipline measured gross — the item says so rather than leaving the reader
  to know it.

No Streamlit here.
"""

from __future__ import annotations

from ..trading import analytics as A
from ..trading import performance as P
from ..trading import psychology as PSY
from ..trading import risk as R

# Below this, a book has not said enough for a threshold crossing to mean
# anything. The engine's own sample floor for a meaningful comparison.
MIN_TRADES = A.MIN_MEANINGFUL_SAMPLE

THRESHOLDS = {
    # Share of trades that had a stop. Below this, the R statistics describe a
    # minority of the book and every average built on them is partial.
    "stop_coverage": 0.70,
    # Coefficient of variation of position risk. Above this the size varies
    # enough that "average risk" stops describing a typical trade.
    "sizing_consistency": 0.60,
    # Share of losses that finished worse than the stop, measured on gross R.
    "beyond_stop": 0.15,
    # Change in rolling median risk between the first and last window.
    "risk_drift": 0.30,
    # Observed worst losing run against the one chance alone produces.
    "streak_multiple": 1.5,
    # Share of gross profit sitting in one instrument or setup.
    "concentration": 0.60,
    # Positions open at once.
    "concurrent": 5,
}

_ORDER = {"critical": 0, "serious": 1, "warning": 2, "good": 3, "neutral": 4}


def _item(key, level, title_en, title_fr, why_en, why_fr, evidence,
          footnote_en="", footnote_fr=""):
    return {
        "key": key,
        "level": level,
        "title": {"en": title_en, "fr": title_fr},
        "why": {"en": why_en, "fr": why_fr},
        "footnote": {"en": footnote_en, "fr": footnote_fr},
        "evidence": evidence,
        # Stated explicitly so a caller cannot mistake this for the portfolio
        # Copilot's items, which do carry a simulatable change.
        "proposed_change": None,
    }


# =============================================================================
# RULES
# =============================================================================

def _stop_coverage(profile, out):
    coverage = profile.get("coverage")
    if coverage is None or profile.get("n", 0) < MIN_TRADES:
        return
    if coverage >= THRESHOLDS["stop_coverage"]:
        return

    missing = profile["no_stop_count"]
    out.append(_item(
        "stop_coverage", "warning" if coverage >= 0.4 else "serious",
        "R describes only part of your book",
        "Le R ne décrit qu'une partie de votre carnet",
        f"{missing} of {profile['n']} trades had no stop recorded, so "
        f"{coverage * 100:.0f}% of the book is what every R figure is computed "
        f"from. A trade without a stop has no amount risked and is excluded "
        f"rather than counted as zero — which is correct, and means the average "
        f"R you see is not the average R of your trading.",
        f"{missing} trades sur {profile['n']} n'ont pas de stop enregistré : "
        f"{coverage * 100:.0f}% du carnet sert donc de base à tous les chiffres "
        f"en R. Un trade sans stop n'a pas de montant risqué et est exclu plutôt "
        f"que compté comme zéro — ce qui est correct, et signifie que le R moyen "
        f"affiché n'est pas le R moyen de votre trading.",
        {"coverage": coverage, "missing": missing, "n": profile["n"],
         "threshold": THRESHOLDS["stop_coverage"]},
    ))


def _sizing_consistency(profile, out):
    consistency = profile.get("consistency")
    if consistency is None or consistency <= THRESHOLDS["sizing_consistency"]:
        return

    out.append(_item(
        "sizing_consistency", "warning",
        "Your position size varies a lot",
        "Votre taille de position varie beaucoup",
        f"The spread of position risk is {consistency:.2f} times its own "
        f"average, against a threshold of {THRESHOLDS['sizing_consistency']:.2f}. "
        f"Your largest risk was {profile['largest_vs_median']:.1f}x your median "
        f"one. That is a description of the sizing, not a judgement of it — but "
        f"it does mean every average in the product is an average over trades "
        f"that were not comparable in size.",
        f"La dispersion du risque par position vaut {consistency:.2f} fois sa "
        f"propre moyenne, pour un seuil de {THRESHOLDS['sizing_consistency']:.2f}. "
        f"Votre plus gros risque valait {profile['largest_vs_median']:.1f}x votre "
        f"risque médian. C'est une description du dimensionnement, pas un "
        f"jugement — mais cela signifie que chaque moyenne du produit porte sur "
        f"des trades qui n'étaient pas comparables en taille.",
        {"consistency": consistency,
         "largest_vs_median": profile.get("largest_vs_median"),
         "n": profile.get("n_with_stop"),
         "threshold": THRESHOLDS["sizing_consistency"]},
    ))


def _stop_discipline(stops, out):
    if not stops.get("n_losses") or stops["n_losses"] < MIN_TRADES:
        return
    share = stops.get("share_beyond_stop", 0.0)
    if share <= THRESHOLDS["beyond_stop"]:
        return

    out.append(_item(
        "beyond_stop", "serious" if share > 0.3 else "warning",
        "Some losses finished past the stop",
        "Certaines pertes ont dépassé le stop",
        f"{stops['n_beyond_stop']} of {stops['n_losses']} losing trades closed "
        f"worse than -1R, the worst at {stops['worst_loss_r']:.2f}R. A loss past "
        f"the stop means the stop did not do its job — moved, removed, gapped "
        f"through or slipped. Which of those it was is not in the data.",
        f"{stops['n_beyond_stop']} trades perdants sur {stops['n_losses']} ont "
        f"clôturé au-delà de -1R, le pire à {stops['worst_loss_r']:.2f}R. Une "
        f"perte au-delà du stop signifie que le stop n'a pas fait son travail : "
        f"déplacé, retiré, franchi par un gap ou glissé. Laquelle de ces causes, "
        f"les données ne le disent pas.",
        {"share": share, "beyond": stops["n_beyond_stop"],
         "losses": stops["n_losses"], "worst_r": stops["worst_loss_r"],
         "threshold": THRESHOLDS["beyond_stop"]},
        # The caveat that keeps this from being the false alarm it was before
        # the engine switched to gross R.
        footnote_en="Measured on price movement before commission and swap. A "
                    "trade stopped at exactly -1R lands past -1R on costs alone, "
                    "so judging this on the net figure would flag almost every "
                    "loss. A 5% allowance for slippage is applied.",
        footnote_fr="Mesuré sur le mouvement de prix avant commission et swap. "
                    "Un trade stoppé exactement à -1R passe sous -1R par les "
                    "seuls frais : juger sur le net signalerait presque toutes "
                    "les pertes. Une tolérance de 5% pour le slippage est "
                    "appliquée.",
    ))


def _risk_drift(drift, out):
    change = drift.get("change")
    if change is None or abs(change) < THRESHOLDS["risk_drift"]:
        return
    rising = change > 0

    out.append(_item(
        "risk_drift", "warning" if rising else "neutral",
        "Your position risk has been drifting " + ("up" if rising else "down"),
        "Votre risque par position a " + ("augmenté" if rising else "diminué"),
        f"The rolling median risk moved from {drift['start_median']:.2f} to "
        f"{drift['end_median']:.2f} across {drift['n_points']} windows, a change "
        f"of {change * 100:+.0f}%. This compares the first and last rolling "
        f"window rather than fitting a trend, so read it as a direction and not "
        f"as a rate.",
        f"Le risque médian glissant est passé de {drift['start_median']:.2f} à "
        f"{drift['end_median']:.2f} sur {drift['n_points']} fenêtres, soit "
        f"{change * 100:+.0f}%. Cela compare la première et la dernière fenêtre "
        f"glissante plutôt que d'ajuster une tendance : lisez-le comme une "
        f"direction, pas comme un taux.",
        {"change": change, "start": drift["start_median"],
         "end": drift["end_median"], "n": drift["n_points"],
         "threshold": THRESHOLDS["risk_drift"]},
    ))


def _losing_run(streaks, out):
    if not streaks or not streaks.get("expected_max_losses"):
        return
    observed = streaks["observed_max_losses"]
    expected = streaks["expected_max_losses"]

    if streaks.get("unusual"):
        out.append(_item(
            "losing_run", "warning",
            "Your worst losing run is longer than chance explains",
            "Votre pire série perdante dépasse ce que le hasard explique",
            f"You had {observed} losses in a row. A {streaks['win_rate'] * 100:.0f}% "
            f"win rate over {streaks['n']} trades produces a run of about "
            f"{expected} by chance alone. That is a reason to look at the trades "
            f"in the run, not a conclusion about them.",
            f"Vous avez eu {observed} pertes d'affilée. Un taux de réussite de "
            f"{streaks['win_rate'] * 100:.0f}% sur {streaks['n']} trades produit "
            f"une série d'environ {expected} par simple hasard. C'est une raison "
            f"de regarder les trades de la série, pas une conclusion à leur sujet.",
            {"observed": observed, "expected": expected, "n": streaks["n"],
             "threshold": THRESHOLDS["streak_multiple"]},
            footnote_en="The expected run assumes independent trades. A trader's "
                        "state carries over, so treat it as an order of magnitude.",
            footnote_fr="La série attendue suppose des trades indépendants. "
                        "L'état du trader se reporte d'un trade à l'autre : "
                        "traitez-la comme un ordre de grandeur.",
        ))
        return

    # The reassuring case is worth raising too. The most common reason a trader
    # abandons a method that works is a losing run that was unremarkable.
    out.append(_item(
        "losing_run_normal", "good",
        "Your worst losing run is within what chance produces",
        "Votre pire série perdante reste dans ce que le hasard produit",
        f"Your longest run of losses was {observed}. A "
        f"{streaks['win_rate'] * 100:.0f}% win rate over {streaks['n']} trades "
        f"produces about {expected} by chance alone.",
        f"Votre plus longue série de pertes est de {observed}. Un taux de "
        f"réussite de {streaks['win_rate'] * 100:.0f}% sur {streaks['n']} trades "
        f"en produit environ {expected} par simple hasard.",
        {"observed": observed, "expected": expected, "n": streaks["n"]},
    ))


def _concentration(rows, dimension_key, out):
    summary = P.concentration(rows)
    share = summary.get("profit_share")
    if share is None or share < THRESHOLDS["concentration"]:
        return
    label = summary.get("most_profitable", "—")

    out.append(_item(
        f"concentration:{dimension_key}", "neutral",
        f"Most of the profit came from one {dimension_key}",
        f"L'essentiel du profit vient d'un seul élément ({dimension_key})",
        f"{label} accounts for {share * 100:.0f}% of the gross profit across "
        f"{summary['n_buckets']} groups. This is a description, not a verdict — "
        f"a specialist's book looks like this, and so does one carried by a "
        f"single lucky run. Only a longer history separates them.",
        f"{label} représente {share * 100:.0f}% du profit brut sur "
        f"{summary['n_buckets']} groupes. C'est une description, pas un verdict — "
        f"le carnet d'un spécialiste ressemble à cela, celui porté par une seule "
        f"série chanceuse aussi. Seul un historique plus long les distingue.",
        {"share": share, "label": label, "buckets": summary["n_buckets"],
         "reliable_buckets": summary.get("reliable_buckets"),
         "threshold": THRESHOLDS["concentration"]},
    ))


def _concurrent_exposure(exposure, profile, out):
    count = exposure.get("max_concurrent")
    if not count or count < THRESHOLDS["concurrent"]:
        return
    peak = exposure.get("max_simultaneous_risk")
    median = profile.get("median_risk")
    multiple = (peak / median) if peak and median else None

    out.append(_item(
        "concurrent", "warning",
        "You have held several positions at once",
        "Vous avez détenu plusieurs positions simultanément",
        f"At the busiest moment you had {count} positions open"
        + (f" ({', '.join(exposure['max_concurrent_symbols'][:5])})"
           if exposure.get("max_concurrent_symbols") else "")
        + (f", risking {multiple:.1f}x your usual per-trade amount at once"
           if multiple else "")
        + ". Per-trade risk understates the real figure: several positions taken "
          "together on correlated instruments are not separate bets.",
        f"Au moment le plus chargé, vous aviez {count} positions ouvertes"
        + (f" ({', '.join(exposure['max_concurrent_symbols'][:5])})"
           if exposure.get("max_concurrent_symbols") else "")
        + (f", risquant {multiple:.1f}x votre montant habituel par trade en même "
           f"temps" if multiple else "")
        + ". Le risque par trade sous-estime le chiffre réel : plusieurs "
          "positions prises ensemble sur des instruments corrélés ne sont pas "
          "des paris distincts.",
        {"max_concurrent": count, "peak_risk": peak, "multiple": multiple,
         "symbols": exposure.get("max_concurrent_symbols", []),
         "threshold": THRESHOLDS["concurrent"]},
    ))


def _costs(metrics, out):
    """
    What the costs took, when they took enough to change the picture.

    Raised only when the book is profitable gross and the costs are a large
    share of that — the case where a trader reads a positive net figure and
    does not see how much of the edge went to the broker.
    """
    gross = metrics.get("gross_profit")
    costs = metrics.get("total_costs")
    if not gross or costs is None or costs >= 0:
        return
    share = abs(costs) / gross
    if share < 0.20:
        return

    out.append(_item(
        "costs", "warning" if share >= 0.35 else "neutral",
        "Costs took a large share of the gross profit",
        "Les frais ont pris une part importante du profit brut",
        f"Commission and swap came to {abs(costs):,.2f}, which is "
        f"{share * 100:.0f}% of the {gross:,.2f} gross profit. Net figures "
        f"throughout the product already have this deducted; the point of "
        f"showing it separately is that the gap between gross and net is where "
        f"a thin edge disappears.",
        f"Commission et swap totalisent {abs(costs):,.2f}, soit "
        f"{share * 100:.0f}% du profit brut de {gross:,.2f}. Les chiffres nets "
        f"du produit les déduisent déjà ; l'intérêt de les montrer séparément "
        f"est que l'écart entre brut et net est l'endroit où un avantage mince "
        f"disparaît.",
        {"costs": costs, "gross_profit": gross, "share": share},
    ))


# =============================================================================
# ENTRY POINT
# =============================================================================

def diagnose(trades, *, lang: str = "en", dismissed=(),
             limit: int | None = None) -> list[dict]:
    """
    The Copilot's items for a book, most severe first.

    Returns an empty list below `MIN_TRADES`. A threshold crossing on eight
    trades is a coincidence, and presenting one as an observation is how a tool
    teaches someone to act on noise.

    `dismissed` is a collection of keys the user has set aside; filtered here
    rather than in the UI, so a dismissed item cannot return through another
    code path.
    """
    closed = A.closed(trades)
    if len(closed) < MIN_TRADES:
        return []

    metrics = A.compute_metrics(closed)
    summary = R.summary(closed)
    profile = summary.get("profile", {})

    out: list[dict] = []
    _stop_coverage(profile, out)
    _sizing_consistency(profile, out)
    _stop_discipline(summary.get("stops", {}), out)
    _risk_drift(summary.get("drift", {}), out)
    _losing_run(summary.get("streaks", {}), out)
    _concurrent_exposure(summary.get("exposure", {}), profile, out)
    _concentration(P.by_symbol(closed, lang), "instrument", out)
    _concentration(P.by_setup(closed, lang), "setup", out)
    _costs(metrics, out)

    dismissed = set(dismissed)
    out = [item for item in out if item["key"] not in dismissed]
    out.sort(key=lambda i: _ORDER.get(i["level"], 9))
    return out[:limit] if limit else out


def combined(trades, *, lang: str = "en", dismissed=(),
             limit: int | None = None) -> list[dict]:
    """
    Threshold items and behavioural findings in one list.

    The two come from different places and mean different things — an item is a
    single figure crossing a stated threshold, a finding is a comparison between
    two groups of trades. They are merged here because a reader wants one list,
    and each keeps its own framing: a finding still says it is a correlation,
    an item still carries the threshold it crossed.
    """
    items = diagnose(trades, lang=lang, dismissed=dismissed)

    for finding in PSY.findings(trades, lang):
        if finding["key"] in set(dismissed):
            continue
        items.append({
            "key": finding["key"],
            "level": finding["level"],
            "title": {"en": "A correlation in your data",
                      "fr": "Une corrélation dans vos données"},
            "why": {"en": finding["en"], "fr": finding["fr"]},
            "footnote": {"en": f"n = {finding['n']}. Both groups are your own "
                               f"trades; this establishes no cause.",
                         "fr": f"n = {finding['n']}. Les deux groupes sont vos "
                               f"propres trades ; cela n'établit aucune cause."},
            "evidence": {"n": finding["n"], "interpretation": "correlation"},
            "proposed_change": None,
        })

    items.sort(key=lambda i: _ORDER.get(i["level"], 9))
    return items[:limit] if limit else items
