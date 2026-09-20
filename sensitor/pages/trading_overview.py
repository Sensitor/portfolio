"""
TRADING OVERVIEW — the hero dashboard for the trading side.

Its job mirrors the investment Overview: within a few seconds the reader knows
what the book made, how often it wins, what one trade is worth on average, how
deep the worst stretch went, and which parts of their own method are carrying
the result. Every figure is a visual component — a number with a meter, a
benchmark and a shape behind it, never a line of text.

Two figures on this page carry a caveat rather than a value when the data does
not support one: profit factor with no losses, and R when there was no stop.
Both are rendered as such instead of quietly becoming a number.
"""

from __future__ import annotations

import streamlit as st

from ..trading import performance as P
from ..ui import charts as C
from ..ui.components import (
    alert, data_table, metric_card, money, note, num, page_header, pct,
    section, spacer,
)
from ..ui.themes import ACCENT, PALETTE, PLOTLY_CONFIG, PLOTLY_CONFIG_ZOOM, STATUS
from ..core.i18n import tr
from ._trading_shared import (
    account_selector, duration_text, filtered_badge, guard, period_selector,
    pf_text, r_text, trading_context,
)

DIMENSIONS = ["symbol", "setup", "session", "weekday", "hour", "timeframe",
              "direction", "combination", "regime", "risk_band", "month"]


def render_trading_overview(ctx=None) -> None:
    lang = st.session_state.get("language", "en")
    page_header(
        f"{tr('nav_trading', lang)} · {tr('nav_trading_overview', lang)}",
        tr("trading_overview_sub", lang),
        eyebrow=tr("product_trading", lang),
    )

    tctx = trading_context(lang)
    if not guard(tctx, lang):
        return

    # ── Controls ─────────────────────────────────────────────────────────────
    left, right = st.columns([3, 1.4])
    with left:
        period_selector(tctx, "tov_period")
    with right:
        account_selector(tctx, "tov_account")

    if tctx.is_filtered:
        filtered_badge(tctx)

    metrics = tctx.metrics
    currency = tctx.currency

    _kpi_rows(tctx, metrics, lang, currency)
    _equity_block(tctx, metrics, lang, currency)
    _breakdown_block(tctx, lang, currency)
    _recent_block(tctx, lang, currency)


# =============================================================================
# KPIs
# =============================================================================

def _kpi_rows(tctx, metrics, lang, currency) -> None:
    equity = tctx.equity_curve
    spark = [p["equity"] for p in equity]

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        net = metrics["net_pnl"]
        metric_card(
            tr("net_pnl", lang),
            money(net, currency, decimals=2),
            spark=spark,
            spark_color=STATUS["good"] if net >= 0 else STATUS["critical"],
            caption=f"{metrics['n']} {tr('trades', lang).lower()}",
        )

    with c2:
        win_rate = metrics["win_rate"]
        # The meter runs 0-100% with the coin-flip line as the reference a reader
        # already has. A high win rate is not by itself good — a 70% win rate with
        # a 0.3 payoff ratio loses money — so the colour follows expectancy, which
        # is the figure that decides it, not the win rate on its own.
        metric_card(
            tr("win_rate", lang),
            pct(win_rate, 1) if win_rate is not None else "—",
            bar=win_rate if win_rate is not None else None,
            bar_color=(STATUS["good"] if metrics["expectancy"] and metrics["expectancy"] > 0
                       else STATUS["warning"]),
            caption=(f"{metrics['n_wins']}W / {metrics['n_losses']}L"
                     + (f" / {metrics['n_scratch']}S" if metrics["n_scratch"] else "")),
        )

    with c3:
        pf = metrics["profit_factor"]
        metric_card(
            tr("profit_factor", lang),
            pf_text(pf, lang),
            bar=min(pf / 3.0, 1.0) if pf is not None else None,
            bar_color=(STATUS["good"] if pf and pf >= 1.5 else
                       STATUS["warning"] if pf and pf >= 1.0 else STATUS["critical"]),
            caption=(f"{money(metrics['gross_profit'], currency)} / "
                     f"{money(abs(metrics['gross_loss']), currency)}"
                     if pf is not None else tr("no_losses_yet", lang)),
        )

    with c4:
        expectancy = metrics["expectancy"]
        avg_win, avg_loss = metrics["avg_win"], metrics["avg_loss"]
        span = max(abs(avg_win or 0), abs(avg_loss or 0)) or 1
        metric_card(
            tr("expectancy", lang),
            money(expectancy, currency, decimals=2) if expectancy is not None else "—",
            bar=min(max((expectancy or 0) / span, -1), 1) * 0.5 + 0.5,
            bar_color=STATUS["good"] if (expectancy or 0) >= 0 else STATUS["critical"],
            caption=f"{tr('per_trade', lang)}",
        )

    spacer(14)
    d1, d2, d3, d4 = st.columns(4, gap="medium")

    with d1:
        avg_r = metrics["avg_r"]
        coverage = metrics["r_coverage"]
        metric_card(
            tr("average_r", lang),
            r_text(avg_r),
            bar=min(max((avg_r or 0) / 1.0, -1), 1) * 0.5 + 0.5,
            bar_color=STATUS["good"] if (avg_r or 0) >= 0 else STATUS["critical"],
            spark=[p["equity"] for p in tctx.r_curve],
            spark_color=ACCENT,
            # R covers only the trades that had a stop, and the share is on the
            # card rather than in a footnote: a 0.4R average over a fifth of the
            # book must never be read as the whole picture.
            caption=f"{pct(coverage, 0)} {tr('with_stop', lang)}",
        )

    with d2:
        depth = metrics["max_drawdown"]
        peaks, running, series = [], None, [p["equity"] for p in tctx.equity_curve]
        for value in series:
            running = value if running is None else max(running, value)
            peaks.append(value - running)
        # The drawdown is shown in money and in R, never as a percentage. The
        # equity curve here is cumulative P&L from zero, so a "percent of peak"
        # is a percentage of whatever the running total happened to be — an
        # early $19 peak followed by a $135 decline reads as -703%, which is
        # arithmetically correct and completely meaningless. A percentage
        # drawdown needs an account balance, which the journal does not hold.
        metric_card(
            tr("max_drawdown", lang),
            money(depth, currency, decimals=2) if depth is not None else "—",
            spark=peaks,
            spark_color=STATUS["critical"],
            caption=(r_text(metrics["max_drawdown_r"])
                     if metrics["max_drawdown_r"] is not None
                     else f"{metrics['n']} {tr('trades', lang).lower()}"),
        )

    with d3:
        payoff = metrics["payoff_ratio"]
        metric_card(
            tr("payoff_ratio", lang),
            f"{payoff:.2f}x" if payoff else "—",
            bar=min(payoff / 3.0, 1.0) if payoff else None,
            bar_color=(STATUS["good"] if payoff and payoff >= 1.5 else
                       STATUS["warning"] if payoff and payoff >= 1 else STATUS["critical"]),
            caption=(f"{money(metrics['avg_win'], currency)} / "
                     f"{money(abs(metrics['avg_loss'] or 0), currency)}"),
        )

    with d4:
        # `current_streak` is signed: positive for a run of wins, negative for a
        # run of losses, zero when the last trade was flat and broke both.
        streak = metrics["current_streak"]
        kind = "win" if streak > 0 else ("loss" if streak < 0 else None)
        peak = f"max {metrics['max_win_streak']}W / {metrics['max_loss_streak']}L"
        metric_card(
            tr("current_streak", lang),
            f"{abs(streak)}" if streak else "—",
            status="good" if kind == "win" else ("critical" if kind == "loss" else None),
            caption=(f"{tr('win_streak', lang) if kind == 'win' else tr('loss_streak', lang)}"
                     f" · {peak}" if kind else peak),
            compact=True,
        )

    if metrics["r_coverage"] < 1:
        note(tr("r_coverage_note", lang))


# =============================================================================
# CURVES
# =============================================================================

def _equity_block(tctx, metrics, lang, currency) -> None:
    section(tr("equity_curve", lang).upper(),
            f"{metrics['n']} {tr('trades', lang).lower()} · {tctx.period}")

    st.plotly_chart(
        C.trading_equity(tctx.equity_curve, height=380, currency=currency, lang=lang),
        width="stretch", config=PLOTLY_CONFIG_ZOOM, key="tov_equity",
    )

    spacer(6)
    left, right = st.columns([1.3, 1], gap="large")

    with left:
        section(tr("daily_pnl", lang).upper())
        st.plotly_chart(
            C.trading_daily_pnl(tctx.daily_pnl, height=250, currency=currency),
            width="stretch", config=PLOTLY_CONFIG, key="tov_daily",
        )

    with right:
        section(tr("r_distribution", lang).upper())
        dist = tctx.r_distribution
        if dist and dist.get("counts"):
            st.plotly_chart(
                C.trading_r_distribution(dist, height=250, lang=lang),
                width="stretch", config=PLOTLY_CONFIG, key="tov_rdist",
            )
        else:
            note(tr("r_coverage_note", lang))


# =============================================================================
# BREAKDOWN
# =============================================================================

def _breakdown_block(tctx, lang, currency) -> None:
    section(tr("performance_by", lang).upper())

    labels = [tr(f"d_{d}", lang) for d in DIMENSIONS]
    chosen = st.selectbox(tr("performance_by", lang), labels, index=0,
                          key="tov_dim", label_visibility="collapsed")
    dimension = DIMENSIONS[labels.index(chosen)]

    rows = tctx.breakdown(dimension)
    if not rows:
        note(tr("not_enough_data", lang))
        return

    chart_col, table_col = st.columns([1.15, 1], gap="large")

    with chart_col:
        st.plotly_chart(
            C.trading_breakdown(rows, metric="net_pnl", currency=currency, lang=lang),
            width="stretch", config=PLOTLY_CONFIG, key=f"tov_bd_{dimension}",
        )

    with table_col:
        max_n = max(r["n"] for r in rows) or 1
        table_rows = []
        for row in rows[:12]:
            table_rows.append([
                row["label"],
                (str(row["n"]), float(row["n"])),
                pct(row["win_rate"], 0) if row["win_rate"] is not None else "—",
                money(row["net_pnl"], currency),
                r_text(row["avg_r"]),
            ])
        data_table(
            [chosen, tr("trades", lang), tr("win_rate", lang),
             tr("net_pnl", lang), tr("average_r", lang)],
            table_rows, align="lrrrr",
            bars={1: (max_n, PALETTE[1])},
        )

    note(tr("sample_note", lang))

    # ── Best and worst, threshold-respecting ─────────────────────────────────
    best = P.best(rows, "expectancy")
    worst = P.worst(rows, "expectancy")
    if best and worst and best["key"] != worst["key"]:
        spacer(4)
        alert(
            "good",
            f"{tr('best_bucket', lang)}: {best['label']}",
            f"{tr('expectancy', lang)} {money(best['expectancy'], currency, decimals=2)} "
            f"{tr('per_trade', lang)} · {tr('win_rate', lang).lower()} "
            f"{pct(best['win_rate'], 0) if best['win_rate'] is not None else '—'}",
            footnote=f"{best['n']} {tr('trades', lang).lower()} — "
                     f"{tr('above_threshold', lang)}",
        )
        alert(
            "warning",
            f"{tr('weakest_bucket', lang)}: {worst['label']}",
            f"{tr('expectancy', lang)} {money(worst['expectancy'], currency, decimals=2)} "
            f"{tr('per_trade', lang)} · {tr('win_rate', lang).lower()} "
            f"{pct(worst['win_rate'], 0) if worst['win_rate'] is not None else '—'}",
            footnote=f"{worst['n']} {tr('trades', lang).lower()} — "
                     f"{tr('above_threshold', lang)}",
        )


# =============================================================================
# RECENT
# =============================================================================

def _recent_block(tctx, lang, currency) -> None:
    recent = tctx.scoped.closed().recent(10)
    if not recent:
        return

    section(tr("recent_trades", lang).upper())
    rows = []
    for trade in recent:
        rows.append([
            trade.closed_at.strftime("%Y-%m-%d %H:%M") if trade.closed_at else "—",
            trade.symbol,
            tr("long", lang) if trade.direction.value == "long" else tr("short", lang),
            money(trade.pnl, currency, decimals=2),
            r_text(trade.r_multiple),
            duration_text(trade.duration_minutes, lang),
        ])
    data_table(
        [tr("closed_at", lang), tr("symbol", lang), tr("direction_label", lang),
         tr("net_pnl", lang), tr("r_multiple", lang), tr("duration", lang)],
        rows, align="llrrrr",
    )
