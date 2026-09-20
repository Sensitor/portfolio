"""
Performance breakdowns.

The same metrics as `analytics`, sliced by the dimensions a trader wants to
compare: instrument, setup, setup combination, session, weekday, month,
timeframe, direction, market regime.

Every bucket carries its sample size and a `reliable` flag. That flag is the
point of this module: a breakdown table sorted by win rate will always put a
two-trade bucket at the top, and presenting that as "your best setup" is how a
journal teaches someone the wrong lesson. Ranking helpers here refuse to promote
a bucket below the sample threshold.

No Streamlit, no database.
"""

from __future__ import annotations

from .analytics import MIN_MEANINGFUL_SAMPLE, closed, compute_metrics
from .models import session_label
from .setups import canonical_setups, combination_key, setup_label

WEEKDAYS = {
    0: {"en": "Monday", "fr": "Lundi"},
    1: {"en": "Tuesday", "fr": "Mardi"},
    2: {"en": "Wednesday", "fr": "Mercredi"},
    3: {"en": "Thursday", "fr": "Jeudi"},
    4: {"en": "Friday", "fr": "Vendredi"},
    5: {"en": "Saturday", "fr": "Samedi"},
    6: {"en": "Sunday", "fr": "Dimanche"},
}

MONTHS = {
    1: {"en": "January", "fr": "Janvier"}, 2: {"en": "February", "fr": "Février"},
    3: {"en": "March", "fr": "Mars"}, 4: {"en": "April", "fr": "Avril"},
    5: {"en": "May", "fr": "Mai"}, 6: {"en": "June", "fr": "Juin"},
    7: {"en": "July", "fr": "Juillet"}, 8: {"en": "August", "fr": "Août"},
    9: {"en": "September", "fr": "Septembre"}, 10: {"en": "October", "fr": "Octobre"},
    11: {"en": "November", "fr": "Novembre"}, 12: {"en": "December", "fr": "Décembre"},
}


# =============================================================================
# GENERIC GROUPING
# =============================================================================

def group_by(trades, key_fn, label_fn=None, lang: str = "en") -> list[dict]:
    """
    Bucket trades by any key and compute the full metric set per bucket.

    `key_fn` may return a single key or an iterable of keys — a trade tagged
    "BOS" and "FVG" counts toward both setups, which is what a trader means when
    asking how BOS performs. Buckets are returned sorted by net P&L.
    """
    buckets: dict = {}
    for trade in closed(trades):
        keys = key_fn(trade)
        if keys is None:
            continue
        if isinstance(keys, (str, int)) or not hasattr(keys, "__iter__"):
            keys = [keys]
        for key in keys:
            buckets.setdefault(key, []).append(trade)

    rows = []
    for key, bucket in buckets.items():
        metrics = compute_metrics(bucket)
        rows.append({
            "key": key,
            "label": label_fn(key, lang) if label_fn else str(key),
            "n": metrics["n"],
            "reliable": metrics["n"] >= MIN_MEANINGFUL_SAMPLE,
            "metrics": metrics,
            "net_pnl": metrics["net_pnl"],
            "win_rate": metrics["win_rate"],
            "avg_r": metrics["avg_r"],
            "total_r": metrics["total_r"],
            "profit_factor": metrics["profit_factor"],
            "expectancy": metrics["expectancy"],
        })

    rows.sort(key=lambda r: r["net_pnl"], reverse=True)
    return rows


# =============================================================================
# DIMENSIONS
# =============================================================================

def by_symbol(trades, lang: str = "en") -> list[dict]:
    return group_by(trades, lambda t: t.symbol, lang=lang)


def by_direction(trades, lang: str = "en") -> list[dict]:
    labels = {"long": {"en": "Long", "fr": "Achat"},
              "short": {"en": "Short", "fr": "Vente"}}
    return group_by(trades, lambda t: t.direction.value,
                    lambda k, l: labels[k][l], lang)


def by_setup(trades, lang: str = "en") -> list[dict]:
    """
    One bucket per setup tag.

    A trade with several tags counts in each: the question "how does FVG perform"
    is about every trade involving an FVG, not only the ones where it was the
    sole tag. Use `by_setup_combination` for the confluence view instead.
    """
    return group_by(trades, lambda t: canonical_setups(t.setups) or None,
                    setup_label, lang)


def by_setup_combination(trades, lang: str = "en") -> list[dict]:
    """One bucket per exact combination of tags — the confluence view."""
    from .setups import combination_label
    return group_by(trades, lambda t: combination_key(t.setups),
                    combination_label, lang)


def by_session(trades, lang: str = "en") -> list[dict]:
    return group_by(trades, lambda t: t.session,
                    lambda k, l: session_label(k, l), lang)


def by_weekday(trades, lang: str = "en") -> list[dict]:
    rows = group_by(trades, lambda t: t.opened_at.weekday(),
                    lambda k, l: WEEKDAYS[k][l], lang)
    rows.sort(key=lambda r: r["key"])          # chronological, not by P&L
    return rows


def by_month(trades, lang: str = "en") -> list[dict]:
    rows = group_by(trades, lambda t: (t.closed_at.year, t.closed_at.month),
                    lambda k, l: f"{MONTHS[k[1]][l]} {k[0]}", lang)
    rows.sort(key=lambda r: r["key"])
    return rows


def by_hour(trades, lang: str = "en") -> list[dict]:
    rows = group_by(trades, lambda t: t.opened_at.hour,
                    lambda k, l: f"{k:02d}:00", lang)
    rows.sort(key=lambda r: r["key"])
    return rows


def by_timeframe(trades, lang: str = "en") -> list[dict]:
    return group_by(trades, lambda t: t.timeframe or None, lang=lang)


def by_regime(trades, lang: str = "en") -> list[dict]:
    from .setups import MARKET_REGIMES
    return group_by(trades, lambda t: t.market_regime or None,
                    lambda k, l: MARKET_REGIMES.get(k, {}).get(l, str(k)), lang)


def by_risk_band(trades, lang: str = "en") -> list[dict]:
    """
    Buckets of risk taken, as a share of the risk the trader usually takes.

    Absolute percentages need account equity, which the journal does not
    necessarily have. Comparing each trade's risk with the median risk answers
    the useful question — "how do I do when I size up?" — without it.
    """
    risks = [t.risk_amount for t in closed(trades) if t.risk_amount is not None]
    if len(risks) < 5:
        return []
    median = sorted(risks)[len(risks) // 2]
    if median <= 0:
        return []

    bands = [
        ("much_smaller", "Well below usual", "Bien sous l'habitude", lambda r: r < 0.5),
        ("smaller", "Below usual", "Sous l'habitude", lambda r: 0.5 <= r < 0.9),
        ("usual", "Usual size", "Taille habituelle", lambda r: 0.9 <= r <= 1.1),
        ("larger", "Above usual", "Au-dessus de l'habitude", lambda r: 1.1 < r <= 2.0),
        ("much_larger", "Well above usual", "Bien au-dessus", lambda r: r > 2.0),
    ]
    labels = {key: {"en": en, "fr": fr} for key, en, fr, _ in bands}

    def band_for(trade):
        if trade.risk_amount is None:
            return None
        ratio = trade.risk_amount / median
        for key, _, _, test in bands:
            if test(ratio):
                return key
        return None

    rows = group_by(trades, band_for, lambda k, l: labels[k][l], lang)
    order = {key: i for i, (key, *_) in enumerate(bands)}
    rows.sort(key=lambda r: order.get(r["key"], 99))
    return rows


# =============================================================================
# RANKING
# =============================================================================

def best(rows, metric: str = "expectancy", minimum: int = MIN_MEANINGFUL_SAMPLE):
    """
    The best bucket by a metric, among those with enough trades.

    The sample filter is not optional. Sorting by win rate without it reliably
    returns a bucket of two winning trades, and calling that "your best setup" is
    a claim the data does not support.
    """
    eligible = [r for r in rows
                if r["n"] >= minimum and r.get(metric) is not None]
    if not eligible:
        return None
    return max(eligible, key=lambda r: r[metric])


def worst(rows, metric: str = "expectancy", minimum: int = MIN_MEANINGFUL_SAMPLE):
    eligible = [r for r in rows
                if r["n"] >= minimum and r.get(metric) is not None]
    if not eligible:
        return None
    return min(eligible, key=lambda r: r[metric])


def concentration(rows) -> dict:
    """
    How much of the activity and the result sits in the top bucket.

    Answers "am I really a multi-instrument trader, or an XAUUSD trader with
    distractions?" — a question the raw list of buckets does not.
    """
    if not rows:
        return {}
    total_trades = sum(r["n"] for r in rows)
    profits = [r["net_pnl"] for r in rows if r["net_pnl"] > 0]
    total_profit = sum(profits)

    by_volume = max(rows, key=lambda r: r["n"])
    by_profit = max(rows, key=lambda r: r["net_pnl"])

    return {
        "n_buckets": len(rows),
        "busiest": by_volume["label"],
        "busiest_share": by_volume["n"] / total_trades if total_trades else None,
        "most_profitable": by_profit["label"],
        "profit_share": (by_profit["net_pnl"] / total_profit
                         if total_profit > 0 and by_profit["net_pnl"] > 0 else None),
        "reliable_buckets": sum(1 for r in rows if r["reliable"]),
    }
