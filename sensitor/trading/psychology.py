"""
Behavioural patterns in trading data.

Compares what a trader recorded about themselves — emotions, discipline ratings,
mistakes — and what their behaviour did around losses, with how the trades
turned out.

What this module is not
-----------------------
It is not a diagnosis and it does not establish cause. Every output is a
comparison between two groups of the trader's own trades, with both sample sizes
attached. Two reasons that matters, and both are real rather than legal
throat-clearing:

**The direction of the arrow is unknown.** "Trades marked anxious lost more" is
equally consistent with anxiety causing bad trades and with bad trades — taken
in poor conditions, on a thin setup — causing anxiety. The data cannot separate
them.

**Self-reported fields are recorded after the fact.** A trader labelling a trade
"confident" after it won, and "anxious" after it lost, produces a perfect
correlation that means nothing. Recording discipline before the outcome is known
is the only thing that fixes that, and the journal cannot enforce it.

So every finding here carries `interpretation: "correlation"` and phrasing built
around "your data shows", never "this causes". The UI is expected to keep that
framing rather than shortening it into a verdict.

No Streamlit, no database.
"""

from __future__ import annotations

import statistics

from .analytics import closed, losing_streak_positions
from .setups import EMOTIONS, canonical_mistakes, mistake_label

# A comparison needs this many trades on each side before it is worth showing.
MIN_GROUP = 5


def _outcome_stats(trades) -> dict:
    """Net P&L, win rate and average R for a group, with its size."""
    trades = [t for t in trades if t.pnl is not None]
    if not trades:
        return {"n": 0}
    pnls = [t.pnl for t in trades]
    wins = [p for p in pnls if p > 0]
    decided = [p for p in pnls if p != 0]
    rs = [t.r_multiple for t in trades if t.r_multiple is not None]
    risks = [t.risk_amount for t in trades if t.risk_amount is not None]

    return {
        "n": len(trades),
        "net_pnl": sum(pnls),
        "avg_pnl": statistics.fmean(pnls),
        "win_rate": (len(wins) / len(decided)) if decided else None,
        "avg_r": statistics.fmean(rs) if rs else None,
        "n_with_r": len(rs),
        "avg_risk": statistics.fmean(risks) if risks else None,
        "n_with_risk": len(risks),
    }


def _comparison(label: str, group, rest, *, lang_labels=None) -> dict | None:
    """
    One group against the remainder, in the module's standard shape.

    Returns None when either side is too small — showing a difference computed
    from three trades would be worse than showing nothing.
    """
    inside = _outcome_stats(group)
    outside = _outcome_stats(rest)
    if inside["n"] < MIN_GROUP or outside["n"] < MIN_GROUP:
        return None

    return {
        "label": label,
        "labels": lang_labels or {},
        "group": inside,
        "rest": outside,
        "avg_pnl_delta": inside["avg_pnl"] - outside["avg_pnl"],
        "win_rate_delta": (
            inside["win_rate"] - outside["win_rate"]
            if inside["win_rate"] is not None and outside["win_rate"] is not None
            else None
        ),
        "avg_r_delta": (
            inside["avg_r"] - outside["avg_r"]
            if inside["avg_r"] is not None and outside["avg_r"] is not None
            else None
        ),
        "interpretation": "correlation",
    }


# =============================================================================
# SELF-REPORTED FIELDS
# =============================================================================

def by_emotion(trades, phase: str = "before", lang: str = "en") -> list[dict]:
    """
    Outcomes grouped by the emotion recorded at a phase of the trade.

    `phase` is "before", "during" or "after". Only "before" is worth much: an
    emotion recorded after the outcome is known is partly a reaction to it.
    """
    field = f"emotion_{phase}"
    trades = [t for t in closed(trades) if getattr(t, field, None)]
    if not trades:
        return []

    groups: dict = {}
    for trade in trades:
        groups.setdefault(getattr(trade, field), []).append(trade)

    rows = []
    for emotion, group in groups.items():
        rest = [t for t in trades if t not in group]
        row = _comparison(emotion, group, rest,
                          lang_labels=EMOTIONS.get(emotion, {}))
        if row:
            row["display"] = EMOTIONS.get(emotion, {}).get(lang, emotion.title())
            row["phase"] = phase
            rows.append(row)

    rows.sort(key=lambda r: r["group"]["avg_pnl"], reverse=True)
    return rows


def by_discipline(trades) -> list[dict]:
    """
    Outcomes grouped by the self-rated discipline score (1-5).

    Scores are grouped into low (1-2), medium (3) and high (4-5) rather than
    kept separate: five buckets over a few hundred trades leaves too few in each
    to compare.
    """
    rated = [t for t in closed(trades) if t.discipline is not None]
    if len(rated) < MIN_GROUP * 2:
        return []

    bands = {
        "low": [t for t in rated if t.discipline <= 2],
        "medium": [t for t in rated if t.discipline == 3],
        "high": [t for t in rated if t.discipline >= 4],
    }
    labels = {"low": {"en": "Low discipline (1-2)", "fr": "Discipline faible (1-2)"},
              "medium": {"en": "Medium discipline (3)", "fr": "Discipline moyenne (3)"},
              "high": {"en": "High discipline (4-5)", "fr": "Discipline élevée (4-5)"}}

    rows = []
    for band, group in bands.items():
        rest = [t for t in rated if t not in group]
        row = _comparison(band, group, rest, lang_labels=labels[band])
        if row:
            rows.append(row)
    return rows


def by_mistake(trades, lang: str = "en") -> list[dict]:
    """
    Outcomes on trades where the trader flagged a given mistake.

    The most directly actionable comparison in the module — and still a
    correlation. A trader flags a mistake more readily on a losing trade, which
    inflates the gap on its own.
    """
    all_closed = closed(trades)
    tagged = [t for t in all_closed if t.mistakes]
    if not tagged:
        return []

    counts: dict = {}
    for trade in tagged:
        for mistake in canonical_mistakes(trade.mistakes):
            counts.setdefault(mistake, []).append(trade)

    rows = []
    for mistake, group in counts.items():
        rest = [t for t in all_closed if t not in group]
        row = _comparison(mistake, group, rest)
        if row:
            row["display"] = mistake_label(mistake, lang)
            rows.append(row)

    rows.sort(key=lambda r: r["group"]["n"], reverse=True)
    return rows


def mistake_frequency(trades, lang: str = "en") -> list[dict]:
    """How often each mistake is flagged, as a share of all trades."""
    all_closed = closed(trades)
    if not all_closed:
        return []

    counts: dict = {}
    for trade in all_closed:
        for mistake in canonical_mistakes(trade.mistakes):
            counts[mistake] = counts.get(mistake, 0) + 1

    rows = [
        {"key": key, "label": mistake_label(key, lang),
         "count": count, "share": count / len(all_closed)}
        for key, count in counts.items()
    ]
    rows.sort(key=lambda r: r["count"], reverse=True)
    return rows


# =============================================================================
# BEHAVIOUR AROUND LOSSES
# =============================================================================

def behaviour_after_losses(trades, streak: int = 2) -> dict:
    """
    Risk taken immediately after consecutive losses, against the rest.

    This is the module's most useful comparison because neither side is
    self-reported: both the losing run and the position size are facts the broker
    recorded. It still shows correlation — a losing run and a larger next trade
    can share a cause — but it is not vulnerable to the after-the-fact labelling
    problem the emotion fields have.
    """
    ordered = sorted(closed(trades), key=lambda t: t.closed_at)
    positions = set(losing_streak_positions(ordered, streak))
    if not positions:
        return {}

    after = [t for i, t in enumerate(ordered) if i in positions]
    other = [t for i, t in enumerate(ordered) if i not in positions]

    after_risks = [t.risk_amount for t in after if t.risk_amount is not None]
    other_risks = [t.risk_amount for t in other if t.risk_amount is not None]
    if len(after_risks) < MIN_GROUP or len(other_risks) < MIN_GROUP:
        return {}

    after_median = statistics.median(after_risks)
    other_median = statistics.median(other_risks)

    return {
        "streak_length": streak,
        "n_after": len(after),
        "n_after_with_risk": len(after_risks),
        "n_other_with_risk": len(other_risks),
        "median_risk_after": after_median,
        "median_risk_other": other_median,
        "risk_ratio": after_median / other_median if other_median > 0 else None,
        "outcome_after": _outcome_stats(after),
        "outcome_other": _outcome_stats(other),
        "interpretation": "correlation",
    }


def behaviour_after_wins(trades, streak: int = 2) -> dict:
    """The same comparison after consecutive wins."""
    ordered = sorted(closed(trades), key=lambda t: t.closed_at)

    positions, run = [], 0
    for i, trade in enumerate(ordered):
        if run >= streak:
            positions.append(i)
        if trade.is_win is True:
            run += 1
        elif trade.pnl == 0:
            pass
        else:
            run = 0

    if not positions:
        return {}
    marks = set(positions)
    after = [t for i, t in enumerate(ordered) if i in marks]
    other = [t for i, t in enumerate(ordered) if i not in marks]

    after_risks = [t.risk_amount for t in after if t.risk_amount is not None]
    other_risks = [t.risk_amount for t in other if t.risk_amount is not None]
    if len(after_risks) < MIN_GROUP or len(other_risks) < MIN_GROUP:
        return {}

    after_median = statistics.median(after_risks)
    other_median = statistics.median(other_risks)

    return {
        "streak_length": streak,
        "n_after": len(after),
        "median_risk_after": after_median,
        "median_risk_other": other_median,
        "risk_ratio": after_median / other_median if other_median > 0 else None,
        "outcome_after": _outcome_stats(after),
        "outcome_other": _outcome_stats(other),
        "interpretation": "correlation",
    }


def activity_after_losses(trades) -> dict:
    """
    Whether trading gets busier on days that started badly.

    Compares trades taken on days whose first trade lost with days whose first
    trade won. A rough proxy for tilt, and labelled as one.
    """
    by_day: dict = {}
    for trade in closed(trades):
        by_day.setdefault(trade.opened_at.date(), []).append(trade)

    bad_start, good_start = [], []
    for day, day_trades in by_day.items():
        day_trades.sort(key=lambda t: t.opened_at)
        first = day_trades[0]
        if first.is_win is False:
            bad_start.append(len(day_trades))
        elif first.is_win is True:
            good_start.append(len(day_trades))

    if len(bad_start) < MIN_GROUP or len(good_start) < MIN_GROUP:
        return {}

    return {
        "n_bad_start_days": len(bad_start),
        "n_good_start_days": len(good_start),
        "median_trades_bad_start": statistics.median(bad_start),
        "median_trades_good_start": statistics.median(good_start),
        "interpretation": "correlation",
        "proxy": "first trade of the day",
    }


# =============================================================================
# SUMMARY
# =============================================================================

def summary(trades, lang: str = "en") -> dict:
    """Everything in this module, for a caller that wants one call."""
    return {
        "emotions_before": by_emotion(trades, "before", lang),
        "discipline": by_discipline(trades),
        "mistakes": by_mistake(trades, lang),
        "mistake_frequency": mistake_frequency(trades, lang),
        "after_losses": behaviour_after_losses(trades),
        "after_wins": behaviour_after_wins(trades),
        "activity_after_losses": activity_after_losses(trades),
    }


def findings(trades, lang: str = "en", limit: int | None = None) -> list[dict]:
    """
    The comparisons worth surfacing, as sentences the UI can render directly.

    Phrasing is fixed here rather than in the UI so a page cannot accidentally
    turn "your data shows" into "this causes". Each finding carries both sample
    sizes.
    """
    out = []

    after = behaviour_after_losses(trades)
    if after and after.get("risk_ratio") and abs(after["risk_ratio"] - 1) >= 0.15:
        ratio = after["risk_ratio"]
        direction_en = "larger" if ratio > 1 else "smaller"
        direction_fr = "plus grande" if ratio > 1 else "plus petite"
        out.append({
            "key": "risk_after_losses",
            "level": "warning" if ratio > 1.25 else "neutral",
            "en": (f"After {after['streak_length']} consecutive losses your median "
                   f"position risk is {ratio:.2f}x your usual — {direction_en}. "
                   f"Based on {after['n_after_with_risk']} trades after a losing run "
                   f"against {after['n_other_with_risk']} others. This is a "
                   f"correlation in your data, not a demonstrated cause."),
            "fr": (f"Après {after['streak_length']} pertes consécutives, votre risque "
                   f"médian par position vaut {ratio:.2f}x votre habitude — "
                   f"{direction_fr}. Sur {after['n_after_with_risk']} trades après "
                   f"une série perdante contre {after['n_other_with_risk']} autres. "
                   f"C'est une corrélation dans vos données, pas une cause démontrée."),
            "n": after["n_after_with_risk"],
        })

    for row in by_mistake(trades, lang)[:3]:
        if row["avg_pnl_delta"] >= 0:
            continue
        out.append({
            "key": f"mistake:{row['label']}",
            "level": "warning",
            "en": (f"Trades you flagged \"{row.get('display', row['label'])}\" averaged "
                   f"{row['group']['avg_pnl']:.2f} against {row['rest']['avg_pnl']:.2f} "
                   f"on the rest ({row['group']['n']} vs {row['rest']['n']} trades). "
                   f"This is a correlation in your data, not a demonstrated cause, and "
                   f"a mistake is more readily flagged on a losing trade, which widens "
                   f"the gap on its own."),
            "fr": (f"Les trades marqués « {row.get('display', row['label'])} » ont "
                   f"rapporté {row['group']['avg_pnl']:.2f} en moyenne contre "
                   f"{row['rest']['avg_pnl']:.2f} pour les autres "
                   f"({row['group']['n']} contre {row['rest']['n']} trades). "
                   f"C'est une corrélation dans vos données, pas une cause démontrée, et "
                   f"une erreur est plus volontiers signalée sur un trade perdant, ce qui "
                   f"élargit l'écart à soi seul."),
            "n": row["group"]["n"],
        })

    activity = activity_after_losses(trades)
    if activity:
        bad = activity["median_trades_bad_start"]
        good = activity["median_trades_good_start"]
        if bad > good:
            out.append({
                "key": "activity_after_losses",
                "level": "neutral",
                "en": (f"On days that opened with a loss you took a median of {bad:.0f} "
                       f"trades, against {good:.0f} on days that opened with a win "
                       f"({activity['n_bad_start_days']} vs "
                       f"{activity['n_good_start_days']} days). The first trade of the "
                       f"day is a rough proxy; this is a correlation, not a cause."),
                "fr": (f"Les jours ouverts sur une perte, vous avez pris {bad:.0f} trades "
                       f"en médiane, contre {good:.0f} les jours ouverts sur un gain "
                       f"({activity['n_bad_start_days']} contre "
                       f"{activity['n_good_start_days']} jours). Le premier trade du jour "
                       f"est un proxy approximatif ; c'est une corrélation, pas une cause."),
                "n": activity["n_bad_start_days"],
            })

    return out[:limit] if limit else out
