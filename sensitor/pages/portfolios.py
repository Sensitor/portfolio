"""
PORTFOLIOS — save an allocation, reload it, keep its history.

Two things live here that the rest of the app cannot do:

* **Saving.** Everything else in Sensitor is computed fresh from prices each
  session. A saved portfolio is the allocation itself, filed under a name.
* **Snapshots.** Prices can always be re-fetched, but the app cannot recover what
  the allocation *was* three months ago unless that was written down. A snapshot
  freezes the weights and the headline metrics at a moment in time, which is what
  makes the history chart and the advisor view possible.

The storage caveat is stated on the page rather than buried: on Streamlit Cloud
the filesystem is ephemeral and saved data does not survive a restart.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import charts as C
from ..components import (
    data_table, empty_state, money, note, num, page_header, pct,
    pill_html, section, spacer,
)
from ..design import INK, INK_MUTED, PLOTLY_CONFIG, html
from ..i18n import tr
from ._shared import require_store_and_user, snapshot_metrics

LOADED_KEY = "sensitor_loaded_portfolio"


def render_portfolios(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_portfolios", lang), tr("portfolios_sub", lang),
                eyebrow=tr("product_short", lang))

    store, email = require_store_and_user(lang)
    if store is None:
        return

    store.upsert_user(email, st.session_state.get("user_tier", "free"))

    if ctx is not None and ctx.has_history:
        _save_block(ctx, lang, store, email)

    _list_block(ctx, lang, store, email)
    note(tr("storage_note", lang))


# =============================================================================
# SAVE
# =============================================================================

def _save_block(ctx, lang, store, email) -> None:
    section(tr("save_current", lang).upper(),
            f"{len(ctx.tickers)} {tr('assets', lang).lower()} · {ctx.period}")

    name_col, client_col, button_col = st.columns([2, 2, 1], gap="medium")
    with name_col:
        name = st.text_input(tr("portfolio_name", lang), key="pf_name",
                             placeholder="Core" if lang == "en" else "Cœur")
    with client_col:
        client = st.text_input(tr("client_name", lang), key="pf_client")
    with button_col:
        spacer(26)
        save_clicked = st.button(tr("save", lang), key="pf_save",
                                 type="primary", width="stretch")

    notes = st.text_input(tr("notes", lang), key="pf_notes")

    if save_clicked:
        if not name.strip():
            st.warning(tr("portfolio_name", lang))
            return
        portfolio_id = store.save_portfolio(
            email, name, ctx.weights,
            mode=st.session_state.get("analysis_mode", "simulation"),
            currency=ctx.currency, notes=notes or None,
            client_name=client.strip() or None,
        )
        # Save and snapshot together: a saved book with no history is a dead end,
        # and the first snapshot is the only one the user cannot take later.
        store.add_snapshot(portfolio_id, total_value=ctx.end_value,
                           weights=ctx.weights, metrics=snapshot_metrics(ctx))
        st.success(f"{tr('portfolio_saved', lang)} — {name}")
        st.rerun()


# =============================================================================
# LIST
# =============================================================================

def _list_block(ctx, lang, store, email) -> None:
    summaries = store.portfolio_summaries(email)
    section(tr("saved_portfolios", lang).upper(), f"{len(summaries)}")

    if not summaries:
        empty_state(tr("no_saved_portfolios", lang), tr("no_saved_body", lang), icon="◌")
        return

    for index, entry in enumerate(summaries):
        _portfolio_card(ctx, lang, store, entry, index)


def _portfolio_card(ctx, lang, store, entry, index) -> None:
    portfolio = entry["portfolio"]
    metrics = entry["metrics"] or {}

    tone = _health_tone(metrics.get("health"))
    badges = []
    if portfolio.client_name:
        badges.append(pill_html(portfolio.client_name, "neutral", icon=False))
    if metrics.get("health") is not None:
        badges.append(pill_html(f"{tr('health_score', lang)} {metrics['health']:.0f}", tone))
    badges.append(pill_html(f"{entry['n_snapshots']} {tr('snapshots', lang).lower()}",
                            "neutral", icon=False))

    holdings_line = " · ".join(
        f"{ticker} {weight * 100:.0f}%"
        for ticker, weight in sorted(portfolio.holdings.items(), key=lambda kv: -kv[1])[:6]
    )
    if len(portfolio.holdings) > 6:
        holdings_line += " …"

    value_line = (f'<div style="font-size:1.15rem;font-weight:700;color:{INK};'
                  f'margin-top:6px;">{money(entry["total_value"], portfolio.currency)}</div>'
                  ) if entry["total_value"] else ""

    html(
        f'<div class="snr-card" style="margin-bottom:6px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">'
        f'<div><div style="font-size:0.98rem;font-weight:700;color:{INK};">'
        f'{portfolio.name}</div>{value_line}</div>'
        f'<div style="display:flex;gap:6px;flex-wrap:wrap;">{"".join(badges)}</div></div>'
        f'<div style="font-size:0.78rem;color:{INK_MUTED};margin-top:10px;">'
        f'{holdings_line}</div>'
        f'<div style="font-size:0.7rem;color:{INK_MUTED};margin-top:8px;">'
        f'{tr("last_updated", lang)}: {portfolio.updated_at[:16].replace("T", " ")}</div>'
        f'</div>'
    )

    load_col, snap_col, hist_col, delete_col = st.columns(4, gap="small")
    state_key = f"pf_state_{portfolio.id}"
    state = st.session_state.get(state_key)

    with load_col:
        if st.button(tr("load", lang), key=f"pf_load_{index}", width="stretch"):
            _load_portfolio(portfolio)
            st.rerun()
    with snap_col:
        disabled = ctx is None or not ctx.has_history
        if st.button(tr("take_snapshot", lang), key=f"pf_snap_{index}",
                     width="stretch", disabled=disabled):
            store.add_snapshot(portfolio.id, total_value=ctx.end_value,
                               weights=ctx.weights, metrics=snapshot_metrics(ctx))
            st.success(tr("snapshot_taken", lang))
            st.rerun()
    with hist_col:
        if st.button(tr("snapshots", lang), key=f"pf_hist_{index}", width="stretch"):
            st.session_state[state_key] = None if state == "history" else "history"
            st.rerun()
    with delete_col:
        if state == "confirm":
            if st.button(tr("confirm_delete", lang), key=f"pf_del2_{index}",
                         type="primary", width="stretch"):
                store.delete_portfolio(portfolio.id)
                st.session_state.pop(state_key, None)
                st.rerun()
        else:
            if st.button(tr("delete", lang), key=f"pf_del_{index}", width="stretch"):
                st.session_state[state_key] = "confirm"
                st.rerun()

    if state == "history":
        _history(store, portfolio, lang)

    spacer(8)


def _history(store, portfolio, lang) -> None:
    snapshots = store.list_snapshots(portfolio.id, limit=200)
    if len(snapshots) < 1:
        note(tr("no_snapshots", lang))
        return

    ordered = list(reversed(snapshots))
    rows = [
        [s.taken_at[:16].replace("T", " "),
         money(s.total_value, portfolio.currency),
         pct(s.metrics.get("total_return")) if s.metrics.get("total_return") is not None else "—",
         pct(s.metrics.get("volatility")) if s.metrics.get("volatility") is not None else "—",
         num(s.metrics.get("sharpe")) if s.metrics.get("sharpe") is not None else "—",
         f"{s.metrics.get('health'):.0f}" if s.metrics.get("health") is not None else "—"]
        for s in ordered
    ]

    if len(ordered) >= 2:
        values = [s.total_value for s in ordered if s.total_value is not None]
        if len(values) >= 2:
            index = pd.to_datetime([s.taken_at for s in ordered
                                    if s.total_value is not None])
            st.plotly_chart(
                C.cumulative_performance(
                    {tr("portfolio_value", lang): pd.Series(values, index=index)},
                    height=220, value_prefix=portfolio.currency, fill=False),
                width="stretch", config=PLOTLY_CONFIG,
                key=f"pf_hist_chart_{portfolio.id}",
            )

    data_table(
        [tr("taken_at", lang), tr("value", lang), tr("total_return", lang),
         tr("volatility", lang), tr("sharpe_ratio", lang), tr("health_score", lang)],
        rows, align="lrrrrr",
    )
    if len(ordered) == 1:
        # One snapshot is a point, not a history — say why rather than showing a
        # single-point chart that looks like a bug.
        note(tr("no_snapshots", lang))
    spacer(8)


def _load_portfolio(portfolio) -> None:
    """
    Hand a saved allocation back to the app.

    Writes the holdings into the pending-analysis slot rather than fabricating an
    analyzer: the returns still have to be fetched, and the existing new-analysis
    flow is what knows how to do that.
    """
    st.session_state[LOADED_KEY] = {
        "id": portfolio.id,
        "name": portfolio.name,
        "holdings": dict(portfolio.holdings),
        "currency": portfolio.currency,
        "mode": portfolio.mode,
    }
    st.session_state.selected_tickers = list(portfolio.holdings)
    st.session_state.weights = dict(portfolio.holdings)
    st.session_state.analysis_mode = portfolio.mode
    st.session_state.page = "new_analysis"


def _health_tone(score) -> str:
    if score is None:
        return "neutral"
    if score >= 80:
        return "good"
    if score >= 65:
        return "good"
    if score >= 50:
        return "warning"
    if score >= 35:
        return "serious"
    return "critical"
