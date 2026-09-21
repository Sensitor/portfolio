"""
COPILOT — patterns worth examining, each with a change you can simulate.

Every item carries four actions, matching the brief:

* **Why?**     the mechanism behind the observation
* **Show me**  the numbers that triggered it, with the threshold
* **Simulate** the impact of the proposed change on every metric
* **Ignore**   sets it aside for this session

The impact table is the honest part. A proposed change is a hypothesis, not a
recommendation, and trimming a volatile holding usually costs past return as well
as risk — the table shows both directions rather than only the flattering one.
"""

from __future__ import annotations

import streamlit as st

from ..ai import copilot as CP
from ..investment import simulate as SI
from ..ui.components import (
    data_table, empty_state, note, num, page_header, pct, pill_html, section, spacer,
)
from ..ui.themes import BORDER, INK, INK_2, INK_FAINT, STATUS, html
from ..core.i18n import tr
from ._shared import guard, period_selector

DISMISSED_KEY = "sensitor_copilot_dismissed"
SIM_KEY = "sensitor_sim_weights"

_METRIC_LABELS = {
    "cagr": "annualized_return", "volatility": "volatility", "sharpe": "sharpe_ratio",
    "max_drawdown": "max_drawdown", "var_95": "var_95",
    "effective_assets": "effective_assets", "health": "health_score",
}


def render_copilot(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_copilot", lang), tr("copilot_sub", lang),
                eyebrow=tr("product_short", lang))
    if not guard(ctx, lang):
        return

    period_selector(ctx, "copilot_period")

    dismissed = st.session_state.setdefault(DISMISSED_KEY, set())
    items = CP.diagnose(
        weights=ctx.weights,
        returns_df=ctx.returns_df,
        risk_contribution=ctx.risk_contribution,
        concentration=ctx.concentration,
        xray=ctx.xray,
        asset_info=ctx.asset_info,
        sector_map=ctx.sector_map,
        dismissed=dismissed,
    )

    header, restore = st.columns([3, 1])
    with header:
        count = len(items)
        label = (f"{count} " + ("item" if count == 1 else "items")) if lang == "en" \
            else (f"{count} " + ("élément" if count == 1 else "éléments"))
        section(tr("things_to_review", lang).upper(), label)
    with restore:
        if dismissed:
            if st.button(f"{tr('restore_ignored', lang)} ({len(dismissed)})",
                         key="cp_restore", width="stretch"):
                st.session_state[DISMISSED_KEY] = set()
                st.rerun()

    if not items:
        empty_state(tr("nothing_flagged", lang), tr("nothing_flagged_body", lang), icon="✓")
        note(tr("copilot_note", lang))
        return

    bundle_kwargs = dict(
        asset_info=ctx.asset_info, sector_map=ctx.sector_map,
        geo_map=ctx.geo_map, profile=ctx.profile,
    )
    before = SI.evaluate_weights(ctx.returns_df, ctx.weights, **bundle_kwargs)

    for index, item in enumerate(items):
        _render_item(ctx, lang, item, index, before, bundle_kwargs)

    note(tr("copilot_note", lang))


def _render_item(ctx, lang, item, index, before, bundle_kwargs) -> None:
    key = item["key"]
    level = item["level"]
    color = STATUS[level]

    html(
        f'<div class="snr-card" style="border-left:3px solid {color};margin-bottom:6px;">'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<span style="color:{color};font-size:0.9rem;">●</span>'
        f'<span style="font-size:0.95rem;font-weight:700;color:{INK};">'
        f'{item["title"][lang]}</span></div>'
        f'<div style="font-size:0.84rem;color:{INK_2};line-height:1.6;margin-top:10px;">'
        f'{item["change"][lang]}</div></div>'
    )

    why, show, simulate, ignore = st.columns(4, gap="small")
    state_key = f"cp_state_{key}"
    state = st.session_state.get(state_key)

    with why:
        if st.button(tr("why_question", lang), key=f"cp_why_{index}", width="stretch"):
            st.session_state[state_key] = None if state == "why" else "why"
            st.rerun()
    with show:
        if st.button(tr("show_me", lang), key=f"cp_show_{index}", width="stretch"):
            st.session_state[state_key] = None if state == "show" else "show"
            st.rerun()
    with simulate:
        if st.button(tr("simulate", lang), key=f"cp_sim_{index}",
                     type="primary", width="stretch"):
            st.session_state[state_key] = None if state == "simulate" else "simulate"
            st.rerun()
    with ignore:
        if st.button(tr("ignore", lang), key=f"cp_ign_{index}", width="stretch"):
            st.session_state[DISMISSED_KEY] = set(st.session_state[DISMISSED_KEY]) | {key}
            st.session_state.pop(state_key, None)
            st.rerun()

    if state == "why":
        html(
            f'<div style="background:rgba(154,168,191,0.04);border:1px solid {BORDER};'
            f'border-radius:9px;padding:14px 16px;margin:4px 0 14px 0;'
            f'font-size:0.84rem;color:{INK_2};line-height:1.65;">'
            f'{item["why"][lang]}</div>'
        )
    elif state == "show":
        rows = [
            [e["label_fr"] if lang == "fr" else e["label_en"], e["value"]]
            for e in item["evidence"]
        ]
        data_table([tr("evidence", lang), ""], rows, align="lr")
        spacer(10)
    elif state == "simulate":
        _render_impact(ctx, lang, item, index, before, bundle_kwargs)

    spacer(6)


def _render_impact(ctx, lang, item, index, before, bundle_kwargs) -> None:
    """Before/after on every metric, with the trade-off visible in both directions."""
    proposed = item["proposed_weights"]
    after = SI.evaluate_weights(ctx.returns_df, proposed, **bundle_kwargs)
    if not after or not before:
        note(tr("short_history_body", lang))
        return

    impact = CP.impact(before, after)

    rows = []
    for row in impact:
        metric = row["metric"]
        if row["is_pct"]:
            before_text, after_text = pct(row["before"], 1), pct(row["after"], 1)
        elif metric == "health":
            before_text, after_text = f"{row['before']:.0f}", f"{row['after']:.0f}"
        else:
            before_text, after_text = num(row["before"], 2), num(row["after"], 2)

        if row["improved"] is None:
            verdict = "—"
        else:
            verdict = tr("improves" if row["improved"] else "worsens", lang)

        rows.append([
            tr(_METRIC_LABELS.get(metric, metric), lang),
            before_text, after_text, verdict,
        ])

    data_table(
        [tr("impact", lang), tr("current", lang), tr("simulated", lang), ""],
        rows, align="lrrl",
    )

    improved = sum(1 for r in impact if r["improved"] is True)
    worsened = sum(1 for r in impact if r["improved"] is False)
    improved_pill = pill_html(f"{improved} {tr('improves', lang)}", "good")
    worsened_pill = pill_html(f"{worsened} {tr('worsens', lang)}", "warning")
    change_text = item["change"][lang]
    html(
        f'<div style="display:flex;gap:8px;align-items:center;margin:10px 0 4px 0;">'
        f'{improved_pill}{worsened_pill}'
        f'<span style="font-size:0.72rem;color:{INK_FAINT};margin-left:6px;">'
        f'{tr("proposed_change", lang)}: {change_text}</span></div>'
    )

    if st.button(tr("apply_to_simulator", lang), key=f"cp_apply_{index}"):
        st.session_state[SIM_KEY] = dict(proposed)
        for ticker, weight in proposed.items():
            st.session_state[f"sim_w_{ticker}"] = float(round(weight * 100, 1))
        st.session_state.page = "simulator"
        st.rerun()

    spacer(8)
