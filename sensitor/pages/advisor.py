"""
ADVISOR — every client book side by side.

Reads from the saved portfolios that carry a client name, using each one's most
recent snapshot. That is a deliberate choice rather than a shortcut: refetching
live prices for every client on every page load would be slow and would hit the
data provider's rate limit within a few clients. The page says plainly that the
figures are as of each snapshot, and refreshing one is a button away.
"""

from __future__ import annotations

import streamlit as st

from ..ui.components import (
    data_table, empty_state, metric_card, money, note, num, page_header, pct,
    pill_html, section, spacer,
)
from ..ui.themes import INK, INK_MUTED, STATUS, html
from ..core.i18n import tr
from ._shared import require_store_and_user, snapshot_metrics


def render_advisor(ctx) -> None:
    lang = ctx.lang if ctx else st.session_state.get("language", "en")

    page_header(tr("nav_advisor", lang), tr("advisor_sub", lang),
                eyebrow=tr("product_short", lang))

    store, email = require_store_and_user(lang)
    if store is None:
        return

    summaries = store.portfolio_summaries(email, clients_only=True)
    if not summaries:
        empty_state(tr("no_clients", lang), tr("no_clients_body", lang), icon="◍")
        note(tr("storage_note", lang))
        return

    _headline(summaries, lang)
    _table(summaries, lang)
    _cards(ctx, summaries, lang, store)
    note(tr("advisor_note", lang))


def _headline(summaries, lang) -> None:
    section(tr("clients", lang).upper(), f"{len(summaries)}")

    values = [s["total_value"] for s in summaries if s["total_value"] is not None]
    healths = [s["metrics"].get("health") for s in summaries
               if s["metrics"].get("health") is not None]
    currency = summaries[0]["portfolio"].currency if summaries else "$"

    weakest = None
    if healths:
        weakest = min(summaries,
                      key=lambda s: s["metrics"].get("health", 101))

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        metric_card(tr("clients", lang), str(len(summaries)), bar=1.0,
                    caption=f"{len(values)} {tr('with_snapshot', lang)}")
    with c2:
        metric_card(tr("total_aum", lang),
                    money(sum(values), currency) if values else "—",
                    bar=1.0 if values else 0,
                    caption=tr("as_of_snapshot", lang))
    with c3:
        average = sum(healths) / len(healths) if healths else None
        metric_card(tr("avg_health", lang),
                    f"{average:.0f}" if average is not None else "—",
                    bar=(average or 0) / 100,
                    status=_tone(average))
    with c4:
        if weakest and weakest["metrics"].get("health") is not None:
            metric_card(tr("lowest_health", lang),
                        weakest["portfolio"].client_name or weakest["portfolio"].name,
                        bar=weakest["metrics"]["health"] / 100,
                        status=_tone(weakest["metrics"]["health"]),
                        caption=f"{tr('health_score', lang)} "
                                f"{weakest['metrics']['health']:.0f}",
                        compact=True)
        else:
            metric_card(tr("lowest_health", lang), "—", caption=tr("stale_snapshot", lang))


def _table(summaries, lang) -> None:
    rows = []
    for entry in summaries:
        portfolio = entry["portfolio"]
        metrics = entry["metrics"] or {}
        snapshot = entry["snapshot"]
        rows.append([
            portfolio.client_name or "—",
            portfolio.name,
            money(entry["total_value"], portfolio.currency)
            if entry["total_value"] is not None else "—",
            pct(metrics.get("total_return")) if metrics.get("total_return") is not None else "—",
            pct(metrics.get("volatility")) if metrics.get("volatility") is not None else "—",
            num(metrics.get("sharpe")) if metrics.get("sharpe") is not None else "—",
            f"{metrics.get('health'):.0f}" if metrics.get("health") is not None else "—",
            snapshot.taken_at[:10] if snapshot else tr("stale_snapshot", lang),
        ])

    data_table(
        [tr("clients", lang), tr("portfolio", lang), tr("value", lang),
         tr("total_return", lang), tr("volatility", lang), tr("sharpe_ratio", lang),
         tr("health_score", lang), tr("taken_at", lang)],
        rows, align="llrrrrrl",
    )


def _cards(ctx, summaries, lang, store) -> None:
    section(tr("clients", lang).upper() + " — " + tr("holdings", lang).upper())

    for index, entry in enumerate(summaries):
        portfolio = entry["portfolio"]
        metrics = entry["metrics"] or {}
        tone = _tone(metrics.get("health"))
        color = STATUS.get(tone, INK_MUTED)

        holdings_line = " · ".join(
            f"{ticker} {weight * 100:.0f}%"
            for ticker, weight in sorted(portfolio.holdings.items(),
                                         key=lambda kv: -kv[1])[:7]
        )
        badges = [pill_html(f"{tr('health_score', lang)} "
                            f"{metrics['health']:.0f}", tone)] if metrics.get("health") is not None else []
        badges.append(pill_html(f"{entry['n_snapshots']} {tr('snapshots', lang).lower()}",
                                "neutral", icon=False))

        html(
            f'<div class="snr-card" style="border-left:3px solid {color};margin-bottom:6px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">'
            f'<div><div style="font-size:0.95rem;font-weight:700;color:{INK};">'
            f'{portfolio.client_name or portfolio.name}</div>'
            f'<div style="font-size:0.75rem;color:{INK_MUTED};margin-top:3px;">'
            f'{portfolio.name}</div></div>'
            f'<div style="text-align:right;">'
            f'<div style="font-size:1.1rem;font-weight:700;color:{INK};">'
            f'{money(entry["total_value"], portfolio.currency) if entry["total_value"] else "—"}</div>'
            f'<div style="display:flex;gap:6px;margin-top:6px;justify-content:flex-end;">'
            f'{"".join(badges)}</div></div></div>'
            f'<div style="font-size:0.76rem;color:{INK_MUTED};margin-top:10px;">'
            f'{holdings_line}</div></div>'
        )

        refresh_col, spacer_col = st.columns([1, 3], gap="small")
        with refresh_col:
            disabled = ctx is None or not ctx.has_history
            if st.button(tr("take_snapshot", lang), key=f"adv_snap_{index}",
                         width="stretch", disabled=disabled):
                # Snapshots the *currently loaded* portfolio against this client's
                # row, which is only meaningful when the advisor has loaded that
                # client's book first — hence the caption on the page.
                store.add_snapshot(email, portfolio.id, total_value=ctx.end_value,
                                   weights=ctx.weights, metrics=snapshot_metrics(ctx))
                st.success(tr("snapshot_taken", lang))
                st.rerun()
        spacer(6)


def _tone(score) -> str:
    if score is None:
        return "neutral"
    if score >= 65:
        return "good"
    if score >= 50:
        return "warning"
    if score >= 35:
        return "serious"
    return "critical"
