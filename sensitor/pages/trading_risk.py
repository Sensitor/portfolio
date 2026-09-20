"""
TRADING RISK — how much is risked, how consistently, and how much at once.

The page a trader should read before the one with the P&L on it. Four questions,
in the order they matter:

1. **How much goes on a trade, and does that number hold?** Sizing consistency,
   as the spread of position risk relative to its average.
2. **Is it drifting?** Rolling median risk over time, against its own median.
3. **Do the stops hold?** Measured on *gross* R — the price-based figure. Judged
   on net R, any trader paying commission looks like one whose stops never work;
   that mistake was live in this engine until the output was read.
4. **How bad can a losing run get?** The observed worst run against the one a win
   rate like this produces by chance, because the most common reason a trader
   abandons a working method is a run that was statistically unremarkable.

Nothing here tells anyone what to risk. The page reports what they do risk and
what it implies; the number itself is theirs.
"""

from __future__ import annotations

import streamlit as st

from ..core.i18n import tr
from ..trading.risk import MIN_SAMPLE, risk_over_time
from ..ui import charts as C
from ..ui.components import (
    alert, data_table, metric_card, money, note, page_header, pct, pill_html,
    section, spacer, stat_card,
)
from ..ui.themes import ACCENT, INK_MUTED, PALETTE, PLOTLY_CONFIG, STATUS, html
from ._trading_shared import (
    account_selector, filter_panel, guard, period_selector, r_text,
    trading_context,
)


def render_trading_risk(ctx=None) -> None:
    lang = st.session_state.get("language", "en")
    page_header(
        f"{tr('nav_trading', lang)} · {tr('nav_trading_risk', lang)}",
        tr("trading_risk_sub", lang),
        eyebrow=tr("product_trading", lang),
    )

    tctx = trading_context(lang)
    if not guard(tctx, lang):
        return

    left, right = st.columns([3, 1.4])
    with left:
        period_selector(tctx, "trk_period")
    with right:
        account_selector(tctx, "trk_account")

    filter_panel(tctx, "trk_filter")

    risk = tctx.risk
    _sizing_block(tctx, risk, lang)
    _drift_block(tctx, risk, lang)
    _stops_block(tctx, risk, lang)
    _exposure_block(tctx, risk, lang)
    _streak_block(tctx, risk, lang)


# =============================================================================
# SIZING
# =============================================================================

def _sizing_block(tctx, risk, lang) -> None:
    profile = risk.get("profile", {})
    currency = tctx.currency

    section(tr("risk_per_trade", lang).upper())

    if not profile.get("n_with_stop"):
        alert("warning", tr("stop_coverage", lang), tr("no_stops_at_all", lang),
              footnote=tr("r_coverage_note", lang))
        return

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        # The meter places the median inside the trader's own observed range, so
        # the card answers "and how typical is that?" rather than leaving the
        # figure alone on a card next to three that carry one.
        span = profile["max_risk"] - profile["min_risk"]
        position = ((profile["median_risk"] - profile["min_risk"]) / span
                    if span > 0 else 0.5)
        metric_card(
            tr("median_risk", lang),
            money(profile["median_risk"], currency, decimals=2),
            bar=position,
            bar_style="track",
            bar_color=ACCENT,
            caption=(f"{money(profile['min_risk'], currency, decimals=2)} – "
                     f"{money(profile['max_risk'], currency, decimals=2)}"),
        )

    with c2:
        consistency = profile.get("consistency")
        # The coefficient of variation: spread over mean, so it compares across
        # accounts and currencies. Withheld below the sample threshold rather
        # than shown with a caveat nobody reads.
        metric_card(
            tr("risk_consistency", lang),
            f"{consistency:.2f}" if consistency is not None else "—",
            bar=min(consistency / 1.0, 1.0) if consistency is not None else None,
            bar_color=(STATUS["good"] if consistency is not None and consistency < 0.25
                       else STATUS["warning"] if consistency is not None and consistency < 0.6
                       else STATUS["critical"]),
            caption=(tr("lower_is_steadier", lang) if consistency is not None
                     else f"{tr('needs_n', lang)} {MIN_SAMPLE}"),
        )

    with c3:
        coverage = profile["coverage"]
        metric_card(
            tr("stop_coverage", lang),
            pct(coverage, 0),
            bar=coverage,
            bar_color=(STATUS["good"] if coverage >= 0.95 else
                       STATUS["warning"] if coverage >= 0.7 else STATUS["critical"]),
            caption=f"{profile['no_stop_count']} {tr('without_stop', lang)}",
        )

    with c4:
        largest = profile.get("largest_vs_median")
        metric_card(
            tr("largest_vs_median", lang),
            f"{largest:.1f}x" if largest else "—",
            bar=min((largest or 1) / 5.0, 1.0),
            bar_color=(STATUS["good"] if largest and largest < 2 else
                       STATUS["warning"] if largest and largest < 4 else STATUS["critical"]),
            caption=f"{money(profile['max_risk'], currency, decimals=2)} "
                    f"{tr('vs', lang)} "
                    f"{money(profile['median_risk'], currency, decimals=2)}",
        )

    note(tr("consistency_note", lang))


# =============================================================================
# DRIFT
# =============================================================================

def _drift_block(tctx, risk, lang) -> None:
    series = risk_over_time(tctx.trades)
    drift = risk.get("drift", {})

    if not series:
        return

    section(tr("risk_drift", lang).upper(),
            f"{len(series)} {tr('rolling_windows', lang)}")

    chart_col, stat_col = st.columns([2.2, 1], gap="large")
    with chart_col:
        st.plotly_chart(
            C.trading_risk_over_time(series, height=250, currency=tctx.currency,
                                     lang=lang),
            width="stretch", config=PLOTLY_CONFIG, key="trk_drift",
        )

    with stat_col:
        if drift:
            change = drift["change"]
            direction = drift["direction"]
            tone = "neutral" if direction == "stable" else (
                "warning" if direction == "up" else "good")
            metric_card(
                tr("risk_drift", lang),
                f"{change * 100:+.0f}%",
                status=tone,
                bar=min(abs(change) / 1.0, 1.0),
                caption=f"{money(drift['start_median'], tctx.currency, decimals=2)} → "
                        f"{money(drift['end_median'], tctx.currency, decimals=2)}",
                compact=True,
            )
            html(
                f'<div style="margin-top:8px;font-size:0.73rem;color:{INK_MUTED};'
                f'line-height:1.55;">{tr(f"drift_{direction}", lang)}</div>'
            )
        else:
            note(tr("not_enough_data", lang))

    note(tr("drift_note", lang))


# =============================================================================
# STOPS
# =============================================================================

def _stops_block(tctx, risk, lang) -> None:
    stops = risk.get("stops", {})
    if not stops.get("n_losses"):
        return

    section(tr("stop_discipline", lang).upper())

    c1, c2, c3 = st.columns(3, gap="medium")
    share = stops["share_beyond_stop"]

    with c1:
        metric_card(
            tr("beyond_stop", lang),
            f"{stops['n_beyond_stop']} / {stops['n_losses']}",
            bar=share,
            bar_color=(STATUS["good"] if share <= 0.05 else
                       STATUS["warning"] if share <= 0.2 else STATUS["critical"]),
            caption=(tr("every_stop_held", lang) if share == 0
                     else f"{pct(share, 0)} {tr('of_losses', lang)}"),
        )
    with c2:
        metric_card(
            tr("worst_loss_r", lang),
            r_text(stops["worst_loss_r"]),
            bar=min(abs(stops["worst_loss_r"]) / 3.0, 1.0),
            bar_color=(STATUS["good"] if abs(stops["worst_loss_r"]) <= 1.1 else
                       STATUS["warning"] if abs(stops["worst_loss_r"]) <= 2
                       else STATUS["critical"]),
            caption=f"{tr('measured_gross', lang)}",
        )
    with c3:
        metric_card(
            tr("avg_loss_r", lang),
            r_text(stops["avg_loss_r"]),
            caption=f"{stops['n_losses']} {tr('losses', lang).lower()}",
        )

    dist = tctx.r_distribution
    if dist and dist.get("counts"):
        st.plotly_chart(
            C.trading_r_distribution(dist, height=250, lang=lang),
            width="stretch", config=PLOTLY_CONFIG, key="trk_rdist",
        )

    note(tr("stop_note", lang))


# =============================================================================
# EXPOSURE
# =============================================================================

def _exposure_block(tctx, risk, lang) -> None:
    exposure = risk.get("exposure", {})
    activity = risk.get("activity", {})
    if not exposure and not activity:
        return

    section(tr("simultaneous_risk", lang).upper())
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        count = exposure.get("max_concurrent")
        symbols = exposure.get("max_concurrent_symbols") or []
        metric_card(
            tr("max_concurrent", lang),
            f"{count}" if count else "—",
            bar=min((count or 0) / 8.0, 1.0),
            bar_color=(STATUS["good"] if (count or 0) <= 2 else
                       STATUS["warning"] if (count or 0) <= 5 else STATUS["critical"]),
            caption=", ".join(symbols[:4]) if symbols else "—",
            compact=True,
        )
    with c2:
        peak = exposure.get("max_simultaneous_risk")
        median_risk = risk.get("profile", {}).get("median_risk")
        metric_card(
            tr("simultaneous_risk", lang),
            money(peak, tctx.currency, decimals=2) if peak else "—",
            caption=(f"{peak / median_risk:.1f}x {tr('usual_risk', lang)}"
                     if peak and median_risk else "—"),
            compact=True,
        )
    with c3:
        metric_card(
            tr("trades_per_day", lang),
            f"{activity.get('median_per_day', 0):.0f}" if activity else "—",
            caption=(f"{tr('max_word', lang)} {activity.get('max_per_day', 0)} · "
                     f"{activity.get('n_days', 0)} {tr('days', lang)}"
                     if activity else "—"),
            compact=True,
        )

    note(tr("exposure_note", lang))


# =============================================================================
# STREAKS
# =============================================================================

def _streak_block(tctx, risk, lang) -> None:
    streaks = risk.get("streaks", {})
    if not streaks:
        return

    section(tr("expected_streak", lang).upper())

    observed = streaks["observed_max_losses"]
    expected = streaks["expected_max_losses"]
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        metric_card(
            tr("observed_streak", lang), f"{observed}",
            bar=min(observed / max(expected * 2, 1), 1.0),
            bar_color=STATUS["critical"] if streaks["unusual"] else STATUS["neutral"],
            caption=f"{streaks['n']} {tr('trades', lang).lower()}",
            compact=True,
        )
    with c2:
        metric_card(
            tr("expected_streak", lang), f"{expected}",
            bar=min(expected / max(expected * 2, 1), 1.0),
            bar_color=ACCENT,
            caption=f"{pct(streaks['win_rate'], 0)} {tr('win_rate', lang).lower()}",
            compact=True,
        )
    with c3:
        metric_card(
            tr("unusual_run", lang),
            tr("yes", lang) if streaks["unusual"] else tr("no", lang),
            status="warning" if streaks["unusual"] else "good",
            caption=tr("threshold_1_5x", lang),
            compact=True,
        )

    if not streaks["unusual"]:
        alert("good", tr("run_within_expectation", lang),
              tr("run_within_expectation_body", lang).format(
                  observed=observed, expected=expected),
              footnote=tr("streak_note", lang))
    else:
        alert("warning", tr("run_beyond_expectation", lang),
              tr("run_beyond_expectation_body", lang).format(
                  observed=observed, expected=expected),
              footnote=tr("streak_note", lang))
