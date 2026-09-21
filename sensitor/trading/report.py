"""
Weekly Trading Review.

One self-contained HTML document covering a week of trading: what happened, what
it cost, how it was risked, and what the week's data lines up with. Built from
the same primitives as the portfolio report, so the two read as one product.

What a review is for, and what it is not
----------------------------------------
A trading week is a small sample. Twenty trades is not enough to conclude
anything about a method, and a document that reads like a verdict on twenty
trades teaches its reader to over-interpret noise — which is the expensive
mistake a review is supposed to prevent, not cause.

So this document is built to be read as a log with arithmetic attached:

* **Every grouped figure carries its sample size**, and buckets below the
  engine's threshold are marked rather than ranked.
* **The week is compared against the trader's own baseline**, not against zero.
  A −1.2R week means nothing until you know the usual week; the comparison is
  what makes it legible.
* **Nothing is called a cause.** The psychology section passes the engine's own
  sentences through verbatim, each naming itself a correlation and carrying its
  sample size.
* **A short week says so.** Under ten closed trades the document leads with the
  fact that most of what follows is unreliable, rather than burying it.

No Streamlit import. `build_weekly_html` takes a list of trades and a window.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..core.document import (
    ACCENT, INK, INK_2, INK_3, NEG, POS, RULE, SURFACE_2, _STYLE, _esc, _kpi,
    _money, _num, _pct, _table, svg_bars, svg_diverging_bars, svg_lines,
)
from ..core.i18n import tr
from . import analytics as A
from . import performance as P
from . import psychology as PSY
from . import risk as R
from . import setups as taxonomy
from .journal import TradeJournal
from .models import session_label

# The sample below which a week's statistics describe the week and nothing more.
THIN_WEEK = 10

SECTIONS = ["summary", "trades", "breakdown", "risk", "psychology", "baseline"]

TITLES = {
    "summary": {"en": "The Week", "fr": "La Semaine"},
    "trades": {"en": "Every Trade", "fr": "Chaque Trade"},
    "breakdown": {"en": "Where It Came From", "fr": "D'où Cela Vient"},
    "risk": {"en": "How It Was Risked", "fr": "Comment le Risque A Été Pris"},
    "psychology": {"en": "What the Data Lines Up With",
                   "fr": "Ce Avec Quoi les Données Coïncident"},
    "baseline": {"en": "Against Your Own Baseline",
                 "fr": "Face à Votre Propre Référence"},
}

DISCLAIMER = {
    "en": (
        "This review describes a single week of trading. A week is a small sample: "
        "the figures below are an accurate record of what happened and a poor basis "
        "for conclusions about a method. Sample sizes are shown beside every grouped "
        "figure for that reason, and groups too small to compare are marked rather "
        "than ranked. Nothing here is advice, a recommendation, or a forecast. The "
        "behavioural section reports correlations between groups of your own trades "
        "and establishes no cause in either direction."
    ),
    "fr": (
        "Ce bilan décrit une seule semaine de trading. Une semaine est un petit "
        "échantillon : les chiffres ci-dessous sont un relevé exact de ce qui s'est "
        "passé et une base médiocre pour conclure quoi que ce soit sur une méthode. "
        "C'est pourquoi les tailles d'échantillon figurent à côté de chaque chiffre "
        "groupé, et les groupes trop petits pour être comparés sont signalés plutôt "
        "que classés. Rien ici n'est un conseil, une recommandation ou une prévision. "
        "La section comportementale rapporte des corrélations entre groupes de vos "
        "propres trades et n'établit aucune cause, dans un sens ou dans l'autre."
    ),
}

THIN_NOTICE = {
    "en": ("Only {n} closed trades this week. Most figures below describe these {n} "
           "trades and should not be read as describing your method — a win rate "
           "over a handful of trades moves by tens of points on one outcome."),
    "fr": ("Seulement {n} trades clôturés cette semaine. La plupart des chiffres "
           "ci-dessous décrivent ces {n} trades et ne doivent pas être lus comme "
           "décrivant votre méthode — un taux de réussite sur une poignée de trades "
           "bouge de dizaines de points sur un seul résultat."),
}


# =============================================================================
# WINDOW
# =============================================================================

def week_bounds(reference: datetime | None = None) -> tuple[datetime, datetime]:
    """
    Monday 00:00 to the following Monday 00:00, containing `reference`.

    Half-open on purpose: a trade closing at 23:59:59 on Sunday belongs to the
    week, and one closing at 00:00:00 on Monday belongs to the next. An
    inclusive end would put a midnight close in both.
    """
    reference = reference or datetime.now()
    start = (reference - timedelta(days=reference.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=7)


def trades_in_week(trades, start: datetime, end: datetime) -> list:
    """
    The trades that *closed* in the window.

    By close rather than open: a review is about results, and a position opened
    on Friday and closed on Tuesday produced its result in the following week.
    """
    return [t for t in A.closed(trades) if t.closed_at and start <= t.closed_at < end]


# =============================================================================
# SECTIONS
# =============================================================================

def _summary(week, previous, lang, currency) -> str:
    metrics = A.compute_metrics(week)
    n = metrics.get("n", 0)
    if not n:
        return f'<p class="note">{_esc(tr("review_no_trades", lang))}</p>'

    curve = A.equity_curve(week)
    cards = [
        _kpi(tr("net_pnl", lang), _money(metrics["net_pnl"], currency),
             f'{n} {tr("trades", lang).lower()}'),
        _kpi(tr("win_rate", lang),
             _pct(metrics["win_rate"]) if metrics["win_rate"] is not None else "—",
             f'{metrics["n_wins"]}W / {metrics["n_losses"]}L'),
        _kpi(tr("profit_factor", lang),
             _num(metrics["profit_factor"]) if metrics["profit_factor"] is not None
             else tr("undefined", lang),
             tr("no_losses_yet", lang) if metrics["profit_factor"] is None else ""),
        _kpi(tr("total_r", lang),
             f'{metrics["total_r"]:+.2f}R' if metrics["total_r"] is not None else "—",
             f'{_pct(metrics["r_coverage"], 0)} {tr("with_stop", lang)}'),
    ]

    body = [f'<div class="kpi-grid wide">{"".join(cards)}</div>']

    # A short week is announced before its numbers, not after them.
    if n < THIN_WEEK:
        body.append(f'<p class="warn">{_esc(THIN_NOTICE[lang].format(n=n))}</p>')

    if len(curve) > 1:
        body.append(svg_lines({tr("equity_curve", lang): [p["equity"] for p in curve]},
                              width=720, height=200))

    daily = A.daily_pnl(week)
    if daily:
        body.append(svg_diverging_bars(
            [(d["date"].strftime("%a %d"), d["pnl"]) for d in daily],
            width=460, label_width=72, as_pct=False, currency=currency))
        body.append(f'<p class="note">{_esc(tr("review_daily_note", lang))}</p>')

    return "".join(body)


def _trades(week, lang, currency) -> str:
    if not week:
        return ""
    rows = []
    for trade in sorted(week, key=lambda t: t.closed_at):
        rows.append([
            trade.closed_at.strftime("%a %d %H:%M"),
            trade.symbol,
            tr("long", lang) if trade.direction.value == "long" else tr("short", lang),
            _money(trade.pnl, currency),
            f"{trade.r_multiple:+.2f}R" if trade.r_multiple is not None else "—",
            A.format_duration(trade.duration_minutes, lang),
            ", ".join(taxonomy.setup_label(s, lang)
                      for s in taxonomy.canonical_setups(trade.setups)) or "—",
        ])
    return _table(
        [tr("closed_at", lang), tr("symbol", lang), tr("direction_label", lang),
         tr("net_pnl", lang), tr("r_multiple", lang), tr("duration", lang),
         tr("setups_label", lang)],
        rows, align="llrrrll",
    ) + f'<p class="note">{_esc(tr("r_coverage_note", lang))}</p>'


# The label width the breakdown charts use, less the room a count needs.
_LABEL_PX = 112
_COUNT_PX = 26


def _with_count(label: str, n: int) -> str:
    """`Break of Structur… (7)` — the name gives way, the sample size does not."""
    from ..core.document import _fit
    return f"{_fit(label, _LABEL_PX - _COUNT_PX)} ({n})"


def _breakdown(week, lang, currency) -> str:
    if not week:
        return ""
    blocks = []
    for key, rows in (("d_symbol", P.by_symbol(week, lang)),
                      ("d_setup", P.by_setup(week, lang)),
                      ("d_session", P.by_session(week, lang))):
        if not rows:
            continue
        # The label carries the count, and the count is what gets protected when
        # the name has to be shortened: "Break of Structur…" still says (7),
        # whereas truncating the whole string would drop the sample size — the
        # one number that must never be the thing that falls off.
        items = [(_with_count(r["label"], r["n"]), r["net_pnl"]) for r in rows[:6]]
        blocks.append(
            f'<div class="col"><h3>{_esc(tr(key, lang))}</h3>'
            f'{svg_diverging_bars(items, width=340, label_width=112, as_pct=False, currency=currency)}</div>')

    note = f'<p class="note">{_esc(tr("review_sample_note", lang))}</p>'
    return f'<div class="cols">{"".join(blocks)}</div>{note}' if blocks else ""


def _risk(week, lang, currency) -> str:
    if not week:
        return ""
    summary = R.summary(week)
    profile = summary.get("profile", {})
    stops = summary.get("stops", {})
    exposure = summary.get("exposure", {})

    if not profile.get("n_with_stop"):
        return f'<p class="warn">{_esc(tr("no_stops_at_all", lang))}</p>'

    consistency = profile.get("consistency")
    cards = [
        _kpi(tr("median_risk", lang), _money(profile["median_risk"], currency),
             f'{_money(profile["min_risk"], currency)} – '
             f'{_money(profile["max_risk"], currency)}'),
        _kpi(tr("risk_consistency", lang),
             _num(consistency) if consistency is not None else "—",
             tr("lower_is_steadier", lang) if consistency is not None
             else f'{tr("needs_n", lang)} {R.MIN_SAMPLE}'),
        _kpi(tr("stop_coverage", lang), _pct(profile["coverage"], 0),
             f'{profile["no_stop_count"]} {tr("without_stop", lang)}'),
    ]
    if stops.get("n_losses"):
        cards.append(_kpi(
            tr("beyond_stop", lang),
            f'{stops["n_beyond_stop"]} / {stops["n_losses"]}',
            tr("every_stop_held", lang) if stops["n_beyond_stop"] == 0
            else tr("measured_gross", lang)))

    body = [f'<div class="kpi-grid wide">{"".join(cards)}</div>']

    if exposure.get("max_concurrent"):
        body.append(
            f'<p class="note">{_esc(tr("max_concurrent", lang))}: '
            f'<strong>{exposure["max_concurrent"]}</strong>'
            f'{_esc(" — " + ", ".join(exposure.get("max_concurrent_symbols") or []))}'
            f'</p>')
    body.append(f'<p class="note">{_esc(tr("stop_note", lang))}</p>')
    return "".join(body)


def _psychology(week, lang) -> str:
    """
    The engine's own sentences, passed through unchanged.

    Not reworded here, and deliberately so: each one states that it is a
    correlation and carries its sample size, and the test suite asserts both in
    both languages. A document that paraphrased them into findings would be the
    one place that safeguard did not reach.
    """
    findings = PSY.findings(week, lang)
    if not findings:
        return (f'<p class="note">{_esc(tr("review_no_patterns", lang))}</p>')

    items = "".join(
        f'<li><strong>{_esc(tr("correlation_in_your_data", lang))}</strong> — '
        f'{_esc(f[lang])} <span class="dim">(n = {f["n"]})</span></li>'
        for f in findings
    )
    return (f'<ul class="findings">{items}</ul>'
            f'<p class="note">{_esc(tr("psychology_note", lang))}</p>')


def _baseline(week, history, lang, currency) -> str:
    """
    This week against the trader's own usual week.

    A −1.2R week means nothing against zero and a great deal against a baseline
    of +0.4R. The comparison is what makes a single week legible at all, which
    is why it is a section rather than a footnote — and why the baseline is the
    trader's own history rather than any external standard.
    """
    if not history:
        return f'<p class="note">{_esc(tr("review_no_baseline", lang))}</p>'

    week_metrics = A.compute_metrics(week)
    base_metrics = A.compute_metrics(history)
    weeks = _distinct_weeks(history)
    if not base_metrics.get("n") or weeks < 2:
        return f'<p class="note">{_esc(tr("review_no_baseline", lang))}</p>'

    per_week_pnl = base_metrics["net_pnl"] / weeks
    per_week_trades = base_metrics["n"] / weeks

    rows = [
        [tr("net_pnl", lang), _money(week_metrics.get("net_pnl"), currency),
         _money(per_week_pnl, currency)],
        [tr("total_trades", lang), str(week_metrics.get("n", 0)),
         f"{per_week_trades:.1f}"],
        [tr("win_rate", lang),
         _pct(week_metrics.get("win_rate")) if week_metrics.get("win_rate") is not None else "—",
         _pct(base_metrics.get("win_rate")) if base_metrics.get("win_rate") is not None else "—"],
        [tr("expectancy", lang),
         _money(week_metrics.get("expectancy"), currency),
         _money(base_metrics.get("expectancy"), currency)],
        [tr("average_r", lang),
         f'{week_metrics["avg_r"]:+.2f}R' if week_metrics.get("avg_r") is not None else "—",
         f'{base_metrics["avg_r"]:+.2f}R' if base_metrics.get("avg_r") is not None else "—"],
    ]

    table = _table([tr("metric", lang), tr("review_this_week", lang),
                    tr("review_your_usual", lang)], rows, align="lrr")
    note = tr("review_baseline_note", lang).format(
        weeks=weeks, n=base_metrics["n"])
    return f'{table}<p class="note">{_esc(note)}</p>'


def _distinct_weeks(trades) -> int:
    """How many calendar weeks the baseline actually spans."""
    return len({(t.closed_at.isocalendar()[0], t.closed_at.isocalendar()[1])
                for t in A.closed(trades) if t.closed_at})


# =============================================================================
# DOCUMENT
# =============================================================================

def build_weekly_html(trades, *, week_of: datetime | None = None,
                      lang: str = "en", currency: str = "$",
                      sections=None, trader_name: str | None = None,
                      account_label: str | None = None) -> str:
    """
    Render the review.

    `trades` is the whole journal; the window is selected here so the baseline
    section has the history to compare against. `week_of` is any moment inside
    the week wanted — the bounds are derived from it.
    """
    sections = [s for s in (sections or SECTIONS) if s in SECTIONS]
    start, end = week_bounds(week_of)

    journal = list(trades) if not isinstance(trades, TradeJournal) else list(trades)
    week = trades_in_week(journal, start, end)
    history = [t for t in A.closed(journal) if t.closed_at and t.closed_at < start]

    builders = {
        "summary": lambda: _summary(week, history, lang, currency),
        "trades": lambda: _trades(week, lang, currency),
        "breakdown": lambda: _breakdown(week, lang, currency),
        "risk": lambda: _risk(week, lang, currency),
        "psychology": lambda: _psychology(week, lang),
        "baseline": lambda: _baseline(week, history, lang, currency),
    }

    body = []
    for index, key in enumerate(sections):
        try:
            content = builders[key]()
        except Exception as error:                       # noqa: BLE001
            # One failing section must not cost the whole document, and a gap
            # is labelled rather than silently omitted.
            content = (f'<p class="note">Section unavailable: '
                       f'{_esc(str(error)[:160])}</p>')
        if not content:
            continue
        title = TITLES.get(key, {}).get(lang, key.title())
        cls = "section break" if index > 0 else "section"
        body.append(f'<section class="{cls}"><h2>{_esc(title)}</h2>{content}</section>')

    title = tr("weekly_review", lang)
    window = f'{start.strftime("%Y-%m-%d")} → {(end - timedelta(days=1)).strftime("%Y-%m-%d")}'
    meta_bits = [window]
    if trader_name:
        meta_bits.insert(0, _esc(trader_name))
    if account_label:
        meta_bits.append(_esc(account_label))
    meta_bits.append(datetime.now().strftime("%Y-%m-%d %H:%M"))

    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)} — {window}</title>
<style>{_STYLE}{_EXTRA_STYLE}</style></head>
<body>
<header>
  <div class="brand">{_esc(tr("product_trading", lang))}</div>
  <h1>{_esc(title)}</h1>
  <div class="meta">{" · ".join(meta_bits)}</div>
</header>
{"".join(body)}
<footer><p>{_esc(DISCLAIMER[lang])}</p></footer>
</body></html>"""


_EXTRA_STYLE = f"""
.kpi-grid.wide {{ grid-template-columns: repeat(4, 1fr); }}
.warn {{
  background: #FFF6E5; border-left: 3px solid #B8860B; color: #5C4200;
  padding: 10px 14px; border-radius: 4px; font-size: 0.86rem; margin: 14px 0;
}}
.cols {{ display: flex; gap: 26px; flex-wrap: wrap; }}
.col {{ flex: 1 1 236px; min-width: 210px; }}
.col h3 {{
  font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em;
  color: {INK_3}; margin: 0 0 8px 0; font-weight: 700;
}}
ul.findings {{ list-style: none; padding: 0; margin: 0; }}
ul.findings li {{
  border-left: 3px solid {ACCENT}; background: {SURFACE_2};
  padding: 10px 14px; margin-bottom: 8px; border-radius: 4px;
  font-size: 0.86rem; line-height: 1.55;
}}
.dim {{ color: {INK_3}; }}
"""
