"""
TRADING PSYCHOLOGY — what the records and the behaviour line up with.

The most dangerous page in the product, and the one that needs the most
restraint. Every comparison here is between two groups of the same trader's own
trades, and none of it establishes cause. Two reasons, both stated on the page:

* The arrow's direction is unknown. Anxiety may produce bad trades; bad trades
  certainly produce anxiety.
* The self-reported fields are usually filled in once the outcome is known,
  which manufactures a correlation on its own. A trader flags "FOMO entry" far
  more readily on a loser.

The wording of every finding is fixed in `trading/psychology.py`, not here, so
this page cannot shorten "your data shows a correlation" into a verdict. The
test suite asserts that every finding names itself a correlation in both
languages, carries its sample size in the sentence, and contains no causal verb.
This page's job is to render them and to show the sample sizes beside every bar.

The comparison that is worth the most is the one neither side self-reported:
position risk after consecutive losses. Both the losing run and the size are
facts the broker recorded.
"""

from __future__ import annotations

import streamlit as st

from ..core.i18n import tr
from ..trading.psychology import MIN_GROUP
from ..ui import charts as C
from ..ui.components import (
    alert, data_table, empty_state, metric_card, money, note, page_header, pct,
    pill_html, section, spacer,
)
from ..ui.themes import INK_2, INK_FAINT, INK_MUTED, PALETTE, PLOTLY_CONFIG, STATUS, html
from ._trading_shared import (
    account_selector, filter_panel, guard, period_selector, r_text, sample_pill,
    trading_context,
)


def render_trading_psychology(ctx=None) -> None:
    lang = st.session_state.get("language", "en")
    page_header(
        f"{tr('nav_trading', lang)} · {tr('nav_trading_psychology', lang)}",
        tr("trading_psychology_sub", lang),
        eyebrow=tr("product_trading", lang),
    )

    tctx = trading_context(lang)
    if not guard(tctx, lang):
        return

    left, right = st.columns([3, 1.4])
    with left:
        period_selector(tctx, "tps_period")
    with right:
        account_selector(tctx, "tps_account")

    filter_panel(tctx, "tps_filter")

    psych = tctx.psychology

    # The framing comes first, before any number. A reader who scrolls past it
    # should still meet "correlation" inside every finding — but they should not
    # have to, and putting the caveat under the charts would be putting it where
    # it changes nothing.
    note(tr("psychology_note", lang))

    _findings_block(tctx, lang)
    _behaviour_block(tctx, psych, lang)
    _mistakes_block(tctx, psych, lang)
    _self_reported_block(tctx, psych, lang)


# =============================================================================
# FINDINGS
# =============================================================================

def _findings_block(tctx, lang) -> None:
    findings = tctx.findings
    section(tr("what_your_data_shows", lang).upper(), f"{len(findings)}")

    if not findings:
        alert("good", tr("no_patterns_title", lang), tr("no_patterns_body", lang))
        return

    for finding in findings:
        alert(
            finding["level"],
            tr("correlation_in_your_data", lang),
            finding[lang],
            footnote=f"n = {finding['n']} · {tr('correlation_footnote', lang)}",
        )


# =============================================================================
# BEHAVIOUR AROUND STREAKS
# =============================================================================

def _behaviour_block(tctx, psych, lang) -> None:
    after_losses = psych.get("after_losses", {})
    after_wins = psych.get("after_wins", {})
    activity = psych.get("activity_after_losses", {})

    if not (after_losses or after_wins or activity):
        return

    section(tr("behaviour_around_streaks", lang).upper(),
            tr("behaviour_around_streaks_sub", lang))

    columns = st.columns(3, gap="medium")

    with columns[0]:
        _streak_card(tr("after_losses", lang), after_losses, tctx, lang, "warning")
    with columns[1]:
        _streak_card(tr("after_wins", lang), after_wins, tctx, lang, "neutral")
    with columns[2]:
        if activity:
            bad = activity["median_trades_bad_start"]
            good = activity["median_trades_good_start"]
            # Centred at 0.5, so an equal comparison draws a half-full meter
            # instead of a full one. A bar at 100% next to the words "1 vs 1"
            # reads as a finding where the data says there is none.
            total = bad + good
            metric_card(
                tr("activity_after_losses", lang),
                f"{bad:.0f} {tr('vs', lang)} {good:.0f}",
                bar=(bad / total) if total else 0.5,
                bar_color=STATUS["warning"] if bad > good else STATUS["neutral"],
                caption=((tr("no_difference", lang) + " · " if bad == good else "")
                         + f"{activity['n_bad_start_days']} {tr('vs', lang)} "
                           f"{activity['n_good_start_days']} {tr('days', lang)}"),
                compact=True,
            )
            html(
                f'<div style="margin-top:8px;font-size:0.72rem;color:{INK_MUTED};'
                f'line-height:1.55;">{tr("activity_proxy_note", lang)}</div>'
            )
        else:
            metric_card(tr("activity_after_losses", lang), "—",
                        caption=f"{tr('needs_n', lang)} {MIN_GROUP}", compact=True)


def _streak_card(label, data, tctx, lang, tone) -> None:
    """
    One streak comparison: median risk taken after a run, against the rest.

    The ratio is the headline because it is scale-free — a reader does not need
    to know what a normal position is on this account to read 1.4x.
    """
    if not data or data.get("risk_ratio") is None:
        metric_card(label, "—", caption=f"{tr('needs_n', lang)} {MIN_GROUP}",
                    compact=True)
        return

    ratio = data["risk_ratio"]
    outcome_after = data.get("outcome_after", {})
    # The caller's `tone` decides whether a departure from 1.0 is coloured as a
    # concern. Sizing up after a losing run is the pattern worth flagging;
    # sizing up after a winning run is a different behaviour, and painting both
    # amber would be the page passing a judgement the data does not carry.
    if tone == "warning":
        colour = (STATUS["warning"] if ratio > 1.25 else
                  STATUS["good"] if ratio < 0.9 else STATUS["neutral"])
    else:
        colour = STATUS["neutral"]
    metric_card(
        label,
        f"{ratio:.2f}x",
        bar=min(ratio / 2.5, 1.0),
        bar_color=colour,
        caption=(f"{money(data['median_risk_after'], tctx.currency, decimals=2)} "
                 f"{tr('vs', lang)} "
                 f"{money(data['median_risk_other'], tctx.currency, decimals=2)} · "
                 f"n={data.get('n_after_with_risk', data.get('n_after', 0))}"),
        compact=True,
    )
    avg_pnl = outcome_after.get("avg_pnl")
    if avg_pnl is not None:
        html(
            f'<div style="margin-top:8px;font-size:0.72rem;color:{INK_MUTED};'
            f'line-height:1.55;">{tr("avg_result_in_group", lang)} '
            f'{money(avg_pnl, tctx.currency, decimals=2)} · '
            f'{pct(outcome_after["win_rate"], 0) if outcome_after.get("win_rate") is not None else "—"} '
            f'{tr("win_rate", lang).lower()}</div>'
        )


# =============================================================================
# MISTAKES
# =============================================================================

def _mistakes_block(tctx, psych, lang) -> None:
    by_mistake = psych.get("mistakes", [])
    frequency = psych.get("mistake_frequency", [])

    if not (by_mistake or frequency):
        return

    section(tr("by_mistake", lang).upper())
    left, right = st.columns([1.4, 1], gap="large")

    with left:
        if by_mistake:
            st.plotly_chart(
                C.trading_comparison(by_mistake, lang=lang),
                width="stretch", config=PLOTLY_CONFIG, key="tps_mistakes",
            )
        else:
            note(tr("not_enough_data", lang))

    with right:
        if frequency:
            max_count = max(r["count"] for r in frequency) or 1
            rows = [[r["label"], (str(r["count"]), float(r["count"])), pct(r["share"], 0)]
                    for r in frequency[:10]]
            data_table(
                [tr("mistake_frequency", lang), tr("trades", lang), tr("share", lang)],
                rows, align="lrr", bars={1: (max_count, PALETTE[3])},
            )

    note(tr("mistake_flagging_note", lang))


# =============================================================================
# SELF-REPORTED
# =============================================================================

def _self_reported_block(tctx, psych, lang) -> None:
    emotions = psych.get("emotions_before", [])
    discipline = psych.get("discipline", [])

    if not (emotions or discipline):
        section(tr("by_emotion", lang).upper())
        empty_state(tr("nothing_recorded_title", lang),
                    tr("nothing_recorded_body", lang), icon="◌")
        return

    if emotions:
        section(tr("by_emotion", lang).upper(),
                f"{sum(r['group']['n'] for r in emotions)} {tr('trades', lang).lower()}")
        st.plotly_chart(
            C.trading_comparison(emotions, lang=lang),
            width="stretch", config=PLOTLY_CONFIG, key="tps_emotions",
        )
        _comparison_table(emotions, tr("emotion_before", lang), tctx, lang)

    if discipline:
        section(tr("by_discipline", lang).upper())
        rows = []
        for row in discipline:
            rows.append({**row, "display": row["labels"].get(lang, row["label"])})
        st.plotly_chart(
            C.trading_comparison(rows, lang=lang),
            width="stretch", config=PLOTLY_CONFIG, key="tps_discipline",
        )
        _comparison_table(rows, tr("discipline_label", lang), tctx, lang)

    note(tr("self_report_note", lang))


def _comparison_table(rows, label, tctx, lang) -> None:
    currency = tctx.currency
    table = []
    for row in rows:
        group, rest = row["group"], row["rest"]
        table.append([
            row.get("display", row["label"]),
            f"{group['n']} / {rest['n']}",
            money(group["avg_pnl"], currency, decimals=2),
            money(rest["avg_pnl"], currency, decimals=2),
            pct(group["win_rate"], 0) if group["win_rate"] is not None else "—",
            r_text(row.get("avg_r_delta")),
        ])
    data_table(
        [label, f"{tr('flagged', lang)} / {tr('the_rest', lang)}",
         f"{tr('avg', lang)} — {tr('flagged', lang)}",
         f"{tr('avg', lang)} — {tr('the_rest', lang)}",
         tr("win_rate", lang), f"Δ {tr('average_r', lang)}"],
        table, align="lrrrrr",
    )
