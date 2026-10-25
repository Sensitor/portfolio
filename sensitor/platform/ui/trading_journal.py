"""
The « Journal de trading » space: every trade judged against the member's plan.

Pages: the dashboard, the list of trades, one trade, entering, importing or
synchronising trades from MetaTrader 5, the plan, (in `trade_reviews`) the
requests sent to a coach, and (in `journal_analysis`) the trading analytics:
performance, analysis, risk and behaviour.

Whose data is shown is decided once per run by `_book`: the signed-in member's
own trades, read through the store's user-scoped methods with the address from
the session, or, for a visitor or a member who asks for it, the constructed
demonstration journal, which every page then labels « Exemple synthétique ».
Nothing user-specific is cached between runs.

Every figure carries its sample, and R stays undefined for a trade without a
stop, as everywhere else in the trading engine. The review judges the rules the
member wrote, not their trading ideas; the page never suggests a trade.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

import plotly.graph_objects as go
import streamlit as st

from ...academy.ui.chart_view import style as chart_style
from ...trading import demo, entry as E, performance, review as R
from ...trading.analytics import compute_metrics
from ...trading.models import Trade, on_utc_clock
from ...trading.setups import EMOTIONS, MISTAKES, SETUPS, mistake_label, setup_label
from .. import spaces
from . import runtime as rt
from . import trade_visuals as V
from .. import brand
from .components import (crumbs, date_fr, esc, footer, html, icon, note, notice,
                         page_header, section, tap)

DEMO_KEY = "jr_demo"
PERIODS = {"30": ("30 jours", 30), "90": ("90 jours", 90), "all": ("Tout", None)}
NAV = (("journal", "Tableau de bord"), ("journal_trades", "Trades"), ("journal_performance", "Performance"),
       ("journal_analysis", "Analyse"), ("journal_risk", "Risque"), ("journal_behaviour", "Comportement"),
       ("journal_add", "Saisir"), ("journal_plan", "Mon plan"), ("journal_reviews", "Revues"))
PAGE_SIZE = 30
SETUP_KEYS = tuple(SETUPS)
MISTAKE_KEYS = tuple(MISTAKES)


# =============================================================================
# DATA FOR THIS RUN
# =============================================================================

@dataclass
class Book:
    trades: list[Trade]
    plan: R.TradingPlan
    plan_written: bool
    demo: bool
    reviews: dict[str, R.TradeReview] = field(default_factory=dict)

    @property
    def closed(self) -> list[Trade]:
        return [t for t in self.trades if t.is_closed]

    def trade(self, trade_id: str | None) -> Trade | None:
        return next((t for t in self.trades if t.id == trade_id), None)


def _book(email: str | None) -> Book:
    store = rt.get_store()
    if not email or store is None or st.session_state.get(DEMO_KEY):
        trades = demo.trades()
        book = Book(trades, demo.PLAN, True, True)
    else:
        saved = store.get_trading_plan(email)
        plan = R.TradingPlan.from_dict(saved) if saved else R.DEFAULT_PLAN
        book = Book(on_utc_clock(store.list_trades(email), aware=True), plan, saved is not None, False)
    book.reviews = R.review_journal(book.trades, book.plan)
    return book


def _in_period(trades: list[Trade], period: str) -> list[Trade]:
    days = PERIODS.get(period, PERIODS["all"])[1]
    if not days:
        return trades
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return [t for t in trades if t.closed_at and t.closed_at >= since]


# =============================================================================
# FURNITURE
# =============================================================================

def _header(subtitle: str, title_html: str, lead: str = "") -> None:
    space = spaces.space("journal")
    crumbs("Sensitor", space.label, *( (subtitle,) if subtitle else ()))
    page_header("Journal de trading", title_html, lead)


def nav(page: str, email: str | None) -> None:
    current = "journal_trades" if page == "journal_trade" else page
    store = rt.get_store()
    unseen = store.unseen_reviews(email) if email and store is not None else 0
    with st.container(key="jnav", horizontal=True):
        for target, label in NAV:
            if target == "journal_reviews" and unseen:
                label = f"{label} · {unseen} nouvelle{'s' if unseen > 1 else ''}"
            rt.link(label, target, key=f"jnav_{target}", kind="primary" if current == target else "secondary")
    show_flash()


def flash(message: str) -> None:
    """A confirmation that survives the rerun which follows a save."""
    st.session_state["jr_flash"] = message


def show_flash() -> None:
    message = st.session_state.pop("jr_flash", None)
    if message:
        st.success(message)


def _demo_banner(book: Book, email: str | None, *, key: str) -> None:
    if not book.demo:
        return
    if email:
        html(f'<div class="sx-j-banner">{brand.hook_svg(16)}<div><b>Exemple synthétique</b> Un journal construit '
             'pour montrer la méthode, avec son plan. Vos propres trades ne sont pas affichés.</div></div>')
        if st.button("Revenir à mon journal", key=f"demo_off_{key}", type="secondary"):
            st.session_state[DEMO_KEY] = False
            st.rerun()
    else:
        html(f'<div class="sx-j-banner">{brand.hook_svg(16)}<div><b>Exemple synthétique</b> Ce journal est '
             'construit pour la démonstration : un trader fictif, son plan et neuf semaines de trades. '
             'Créez un compte pour tenir le vôtre.</div></div>')


def _signin_prompt(key: str, title: str) -> None:
    with st.container(key=f"navy_jrsign_{key}"):
        html(f'<div class="sx-kicker on-navy">Réservé aux membres</div><h2 class="sx-h3 on-navy">{esc(title)}</h2>'
             '<p>Le journal et la revue sont personnels : vos trades ne sont visibles que par vous.</p>')
        rt.link("Se connecter ou créer un compte", "account", key=f"signin_{key}", kind="primary")


def _period_picker(key: str) -> str:
    return st.radio("Période", list(PERIODS), format_func=lambda k: PERIODS[k][0], horizontal=True,
                    index=1, key=f"jr_period_{key}", label_visibility="collapsed")


def _setups_text(trade: Trade) -> str:
    return ", ".join(setup_label(s, "fr") for s in trade.setups) or "sans setup"


def _side(trade) -> str:
    direction = trade.direction.value if isinstance(trade, Trade) else trade.get("direction")
    return "Achat" if direction == "long" else "Vente"


def _paris(moment: datetime) -> datetime:
    return E.to_paris(moment)


def _when(moment: datetime) -> str:
    local = _paris(moment)
    return f"{date_fr(local)} · {local:%H:%M}"


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'s' if n > 1 else ''}"


def _count_of(n: int, total: int) -> str:
    return f"{n} trade{'s' if n > 1 else ''} sur {total}"


def _currency(code: str) -> str:
    return {"EUR": "€", "USD": "$", "GBP": "£"}.get(code or "", code or "")


def trade_row(trade: Trade, review: R.TradeReview | None, *, key: str) -> None:
    r = trade.r_multiple
    print_ = V.rule_print(review.checks) if review else ""
    departures = (f'<em>{len(review.failed)} écart{"s" if len(review.failed) > 1 else ""}</em>'
                  if review and review.failed else "")
    tap(f"trade_{key}_{trade.id}",
        f'<div class="sx-c-row"><div><div class="sym">{esc(trade.symbol)}<span>{_side(trade).lower()}</span></div>'
        f'<div class="when">{esc(_when(trade.opened_at))} · {esc(V.SESSION_SHORT.get(trade.session.value, ""))}</div></div>'
        f'<div class="meta2">{esc(_setups_text(trade))}{" · " + departures if departures else ""}</div>'
        f'<div>{print_}</div><div class="r {V.tone(r)}">{esc(V.r_text(r))}</div>'
        f'<span class="go">{icon("arrow")}</span></div>',
        f"{trade.symbol}, {_side(trade).lower()} du {_when(trade.opened_at)}, {V.r_text(r)}",
        "journal_trade", trade=trade.id)


# =============================================================================
# DASHBOARD
# =============================================================================

def dashboard(catalog, email, route) -> None:
    _header("", "Chaque trade, <em>jugé</em> sur votre plan.",
            "Vos trades confrontés aux règles que vous avez écrites : ce que vous avez respecté, ce que "
            "les écarts vous ont coûté en R, et la leçon qui corrige l'écart le plus cher.")
    book = _book(email)
    nav("journal", email)
    _demo_banner(book, email, key="dash")

    if not book.closed:
        _empty_state(email)
        footer()
        return

    period = _period_picker("dash")
    trades = _in_period(book.closed, period)
    if not trades:
        note("Aucun trade clôturé sur cette période. Choisissez une période plus longue.")
        footer()
        return
    reviews = {t.id: book.reviews[t.id] for t in trades if t.id in book.reviews}
    rep = R.report(trades, reviews)
    metrics = compute_metrics(trades)

    _record(book, rep, metrics, trades, reviews, period)
    if not book.plan_written and not book.demo:
        notice("Plan par défaut", "Vos trades sont revus avec un plan de départ (1 % de risque, rapport "
               "de 1,5, trois trades par jour). Écrivez le vôtre dans « Mon plan » : la revue suivra vos règles.",
               "info")

    section(1, "Ce que vos écarts vous ont coûté", "Vos trades tels qu'ils ont été pris, et les mêmes trades si "
            "chaque écart au plan avait été évité. La zone entre les deux, c'est le prix des écarts.")
    _curves(trades, reviews)

    section(2, "Où partent vos R", "Chaque règle de votre plan : une marque par écart, et ce que les trades "
            "concernés ont rapporté ou coûté.")
    _rules(rep, key="dash")

    section(3, "Vos jours, un par un", "Un carré par jour : vert pour un jour gagnant en R, brique pour un jour "
            "perdant. Les semaines se lisent de gauche à droite.")
    _regularity(trades)

    section(4, "Ce qui fonctionne pour vous", "Vos résultats par setup et par séance, avec le nombre de "
            "trades derrière chaque chiffre.")
    _breakdowns(trades)

    section(5, "Vos derniers trades", "À droite de chaque trade, son empreinte : les neuf règles du plan, "
            "toujours dans le même ordre. Une case brique, une règle enfreinte.")
    recent = sorted(trades, key=lambda t: t.closed_at, reverse=True)[:6]
    for t in recent:
        trade_row(t, book.reviews.get(t.id), key="dash")
    rt.link("Voir tous les trades", "journal_trades", key="dash_all_trades")
    footer()


def _empty_state(email: str | None) -> None:
    html('<div class="sx-c-blank"><div class="rub">Votre journal est vide</div><h3>Trois façons de commencer.</h3>'
         '<p>Saisissez un trade en trente secondes, importez un fichier de vos trades, ou explorez d\'abord un '
         'journal d\'exemple pour voir ce que la revue vous apprendra.</p>'
         '<ol><li><b>Un trade suffit</b> pour voir sa revue règle par règle.</li>'
         '<li><b>Dix trades</b> donnent un premier relevé.</li>'
         '<li><b>Trente trades</b> et plus : la marge commence à dire quelque chose de fiable.</li></ol></div>')
    a, b, c = st.columns(3)
    with a:
        rt.link("Saisir un trade", "journal_add", key="empty_add", kind="primary", width="stretch")
    with b:
        rt.link("Importer un fichier", "journal_add", key="empty_import", width="stretch")
    with c:
        if st.button("Explorer l'exemple", key="empty_demo", width="stretch"):
            st.session_state[DEMO_KEY] = True
            st.rerun()
    note("Vos trades MetaTrader 5 se synchronisent depuis « Saisir », et ceux déjà synchronisés dans "
         "l'application d'analyse apparaissent ici : c'est le même compte et le même journal.")


def _streaks(trades: list[Trade], reviews: dict) -> tuple[int, int]:
    """Trades in a row inside the plan: the run still going, and the longest one."""
    current = best = 0
    for t in sorted(trades, key=lambda t: (t.closed_at, t.id)):
        followed = reviews.get(t.id) and reviews[t.id].followed
        if followed:
            current += 1
            best = max(best, current)
        elif followed is False:
            current = 0
    return current, best


def _share(value: float) -> str:
    return f"{round(abs(value) * 100)} %"


def _figure_notes(m: dict, rep: R.PlanReport, currency: str = "") -> dict[str, str]:
    """One sentence per figure, saying what it means for this member, including when it cannot be computed."""
    e, total, pf, win = m.get("expectancy_r"), m.get("total_r"), m.get("profit_factor"), m.get("win_rate")
    payoff, dd = m.get("payoff_ratio"), m.get("max_drawdown_r")
    net = m.get("net_pnl")
    money = f"{V.signed(net)} {currency}".strip() if net is not None else ""
    out = {}
    out["e"] = ("Sans stop, le risque est inconnu : pas d'espérance en R." if e is None else
                f"En moyenne, un trade vous rend {_share(e)} de ce que vous risquez." if e > 0 else
                f"En moyenne, un trade vous coûte {_share(e)} de ce que vous risquez.")
    out["total"] = (f"Sans stop, pas de résultat en R. En argent : {money}." if total is None else
                    f"Soit {V.fr(abs(total), 1)} fois votre risque par trade, {'gagné' if total >= 0 else 'perdu'} sur la période.")
    if win is None:
        out["win"] = "Aucun trade gagnant ou perdant."
    elif payoff:
        out["win"] = f"Avec vos gains moyens, {round(100 / (1 + payoff))} % suffisent pour ne pas perdre d'argent."
    else:
        out["win"] = f"{_plural(m.get('n_wins', 0), 'gagnant')} pour {_plural(m.get('n_losses', 0), 'perdant')}."
    out["pf"] = ("Pas encore de perte pour le calculer." if pf is None else
                 f"Pour 1 perdu, {V.fr(pf)} gagné, en argent.")
    out["dd"] = ("Sans stop, pas de drawdown en R." if dd is None else
                 "Aucun recul : la courbe n'a fait que monter." if not dd else
                 f"Le pire recul, du sommet au creux : l'équivalent de {V.fr(abs(dd), 1)} pertes de 1 R d'affilée.")
    departures = rep.n_checked - rep.n_followed
    if not departures:
        out["dep"] = "Aucun trade hors plan sur la période."
    elif not rep.n_departed_r:
        out["dep"] = (f"{'Les' if departures > 1 else 'Le'} {_plural(departures, 'trade')} hors plan "
                      f"{'n’ont' if departures > 1 else 'n’a'} pas de stop : leur coût en R est inconnu.")
    else:
        unknown = departures - rep.n_departed_r
        out["dep"] = (f"Ce qu'ont {'coûté' if rep.departed_r < 0 else 'rapporté'} les {_plural(rep.n_departed_r, 'trade')} "
                      f"hors plan" + (f", sans compter {unknown} sans stop." if unknown else "."))
    return out


def _sample_note(n: int) -> str:
    if n < 10:
        return (f"Avec {_plural(n, 'trade')}, ces chiffres ne mesurent encore rien de stable : "
                "regardez plutôt la revue de chaque trade.")
    if n < 100:
        return f"Sur {n} trades, ces chiffres donnent un ordre de grandeur, pas encore une certitude."
    return f"Sur {n} trades, l'échantillon permet de comparer un mois à l'autre."


def _record(book: Book, rep: R.PlanReport, m: dict, trades: list[Trade], reviews: dict, period: str) -> None:
    ordered = sorted(trades, key=lambda t: (t.closed_at, t.id))
    marks = []
    for i, t in enumerate(ordered, start=1):
        rv = reviews.get(t.id)
        state = "na" if not rv or rv.followed is None else ("in" if rv.followed else "out")
        what = {"in": "plan suivi", "out": f"{len(rv.failed) if rv else 0} écart(s)", "na": "rien de vérifiable"}[state]
        marks.append((state, f"Trade {i} · {t.symbol} · {V.r_text(t.r_multiple)} · {what}"))
    if rep.n_checked:
        headline = (f"Plan respecté sur <em>{_count_of(rep.n_followed, rep.n_checked)}</em>."
                    if rep.n_followed else f"Plan respecté sur <em>aucun des {rep.n_checked} trades</em>.")
    else:
        headline = "Aucune règle vérifiable : renseignez le stop et le setup de vos trades."
    current, best = _streaks(trades, reviews)
    rows = R.plan_curves(trades, reviews)
    reading = []
    if rows and rep.n_departed_r and rep.departed_r < 0:
        reading.append(f"Sans les {_plural(rep.n_departed_r, 'écart')}, la courbe finirait à "
                       f"{V.r_text(rows[-1]['plan'])} au lieu de {V.r_text(rows[-1]['realise'])}.")
    top = rep.priority
    if top is not None:
        reading.append(f"L'écart qui pèse le plus : {top.label.lower()}, {top.breaches} fois"
                       f"{', pour ' + V.r_text(top.cost_r) if top.cost_r else ''}.")
    if best and current == best:
        reading.append(f"Série en cours : {_plural(current, 'trade')} d'affilée dans le plan, "
                       "votre meilleure à ce jour.")
    elif best and current:
        reading.append(f"Série en cours : {_plural(current, 'trade')} d'affilée dans le plan. "
                       f"Votre meilleure : {best}.")
    elif best:
        reading.append(f"Le dernier trade a rompu la série ; votre meilleure : {best} trades d'affilée dans le plan.")
    if m["n"] and not m.get("n_with_r"):
        reading.insert(0, "Aucun de ces trades n'a de stop : ni le risque ni le résultat en R ne peuvent être "
                          "mesurés. C'est la première règle à tenir.")
    elif m.get("n_with_r", 0) < m["n"]:
        reading.append(f"{_plural(m['n'] - m['n_with_r'], 'trade')} sans stop "
                       f"{'sont' if m['n'] - m['n_with_r'] > 1 else 'est'} hors des chiffres en R.")
    reading.append(_sample_note(m["n"]))
    when = {"30": "les 30 derniers jours", "90": "les 90 derniers jours"}.get(period, "toute la période")
    f = _figure_notes(m, rep, _currency(trades[0].account_currency) if trades else "")

    def figure(label: str, value: str, sentence: str, tone_: str = "") -> str:
        return (f'<div><div class="l">{esc(label)}</div><div class="v {tone_}">{value}</div>'
                f'<div class="s">{esc(sentence)}</div></div>')

    pf, win = m.get("profit_factor"), m.get("win_rate")
    figures = "".join((
        figure("Espérance par trade", esc(V.r_text(m.get("expectancy_r"))), f["e"], V.tone(m.get("expectancy_r"))),
        figure("Résultat total", esc(V.r_text(m.get("total_r"))), f["total"], V.tone(m.get("total_r"))),
        figure("Taux de réussite", "n.d." if win is None else f"{round(win * 100)} %", f["win"]),
        figure("Profit factor", "n.d." if pf is None else esc(V.fr(pf)), f["pf"]),
        figure("Drawdown maximum", esc(V.r_text(m.get("max_drawdown_r"))), f["dd"],
               "down" if (m.get("max_drawdown_r") or 0) < 0 else ""),
        figure("Coût des écarts",
               esc(V.r_text(rep.departed_r)) if rep.n_departed_r else ("aucun" if rep.n_checked == rep.n_followed else "n.d."),
               f["dep"], V.tone(rep.departed_r) if rep.n_departed_r else ""),
    ))
    key = ('<div class="sx-c-key"><span><i style="background:var(--c-ink)"></i>plan suivi</span>'
           '<span><i style="background:var(--c-down);height:16px"></i>écart au plan</span>'
           '<span><i style="border:1px solid var(--c-na);height:8px"></i>rien de vérifiable</span>'
           '<span>une marque par trade, du plus ancien au plus récent</span></div>')
    html(f'<div class="sx-c-record"><div class="body"><div class="rub">Le relevé · {esc(when)}'
         f'{" · exemple synthétique" if book.demo else ""}</div><h3>{headline}</h3>'
         f'<div class="sx-c-count"><div><div class="big">{rep.n_followed}<small> / {rep.n_checked}</small></div>'
         f'<div class="lab">trades dans le plan</div></div>{V.record(marks)}</div>{key}</div>'
         f'<div class="sx-c-margin"><div class="rub">Lecture</div>{V.notes(reading)}</div></div>'
         f'<div class="sx-c-figures">{figures}</div>')


def _curves(trades: list[Trade], reviews: dict) -> None:
    rows = R.plan_curves(trades, reviews)
    if len(rows) < 2:
        note("La courbe apparaîtra à partir de deux trades avec un stop.")
        return
    K = V.K
    xs = [r["n"] for r in rows]
    real, plan = [r["realise"] for r in rows], [r["plan"] for r in rows]
    low, high = min(real + plan + [0]), max(real + plan + [0])
    rug = low - (high - low) * 0.09
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=real, name="Réalisé", line=dict(color=K["ink"], width=2.4),
                             hovertemplate="Trade %{x} · réalisé : %{y:+.2f} R<extra></extra>"))
    # Filled to the curve above: the area between the two is what the departures cost.
    fig.add_trace(go.Scatter(x=xs, y=plan, name="Plan seul", line=dict(color=K["plan"], width=1.5),
                             fill="tonexty", fillcolor="rgba(154,58,44,0.10)",
                             hovertemplate="Trade %{x} · plan seul : %{y:+.2f} R<extra></extra>"))
    off = [r for r in rows if r["ecart"]]
    if off:
        fig.add_trace(go.Scatter(x=[r["n"] for r in off], y=[rug] * len(off), mode="markers", name="Écart",
                                 marker=dict(symbol="line-ns", size=11, line=dict(color=K["down"], width=2.2)),
                                 hovertemplate="Trade %{x} : hors plan<extra></extra>"))
    font = "Schibsted Grotesk, DM Sans, sans-serif"
    last = rows[-1]
    gap = last["plan"] - last["realise"]
    near = abs(gap) < (high - low) * 0.08
    for value, label, color, shift in ((last["plan"], "Plan seul", K["plan"], -9 if near and gap >= 0 else 0),
                                       (last["realise"], "Réalisé", K["ink"], 9 if near and gap >= 0 else 0)):
        fig.add_annotation(x=xs[-1], y=value, text=f"<b>{label}</b> {V.r_text(value)}", showarrow=False,
                           xanchor="left", xshift=8, yshift=shift, font=dict(family=font, size=12.5, color=color))
    if off and abs(gap) > 0.01:
        k = max(1, int(len(xs) * 0.78)) - 1
        mid = (rows[k]["plan"] + rows[k]["realise"]) / 2
        fig.add_annotation(x=xs[k], y=mid, text=f"écart final : {V.fr(abs(gap))} R",
                           showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=K["note"], ax=-52, ay=-30,
                           xanchor="right", font=dict(family="Newsreader, Georgia, serif", size=14, color=K["note"]))
    chart_style(fig, x_label="Trades, dans l'ordre de clôture", y_label="Résultat cumulé, en R",
                numeric_x=True, height=380, legend=False)
    fig.update_layout(font=dict(family=font, color=K["ink-2"]), margin=dict(l=10, r=128, t=24, b=10),
                      xaxis=dict(showgrid=False, tickfont=dict(family=font, size=11.5, color=K["graphite"]),
                                 linecolor=K["rule-strong"], title_font=dict(family=font, size=12.5, color=K["graphite"])),
                      yaxis=dict(gridcolor=K["rule"], zerolinecolor=K["rule-strong"],
                                 tickfont=dict(family=font, size=11.5, color=K["graphite"]),
                                 title_font=dict(family=font, size=12.5, color=K["graphite"])),
                      hoverlabel=dict(font=dict(family=font)))
    with st.container(key="chart_jr_curves"):
        st.plotly_chart(fig, key="plot_jr_curves", theme=None, config={"displayModeBar": False, "responsive": True})
        missing = len([t for t in trades if t.r_multiple is None])
        extra = f" {missing} trade{'s' if missing > 1 else ''} sans stop, donc sans R, n'y figure{'nt' if missing > 1 else ''} pas." if missing else ""
        html(f'<div class="sx-chart-foot"><b>Lecture</b><span>Les traits brique, sous la courbe, marquent les trades hors '
             f'plan. La courbe du plan compte ces trades à zéro : elle montre ce que la discipline seule aurait '
             f'changé, pas un résultat garanti.{esc(extra)}</span></div>')


def _rules(rep: R.PlanReport, *, key: str) -> None:
    if not rep.tallies:
        note("Aucune règle vérifiable sur cette période.")
        return
    left, right = st.columns([1.75, 1], gap="large")
    with left:
        rows = []
        for t in rep.tallies:
            marks = ("".join("<i></i>" for _ in range(min(t.breaches, 24)))
                     + (f"<em>+{t.breaches - 24}</em>" if t.breaches > 24 else "")) if t.breaches else ""
            cost = (f'<span class="cost {V.tone(t.cost_r)}">{esc(V.r_text(t.cost_r))}</span>' if t.breaches
                    else '<span class="cost ok">tenue</span>')
            rows.append(f'<li class="{"" if t.breaches else "clean"}"><span>{esc(t.label)}</span>'
                        f'<span class="marks">{marks}</span><span class="n">{t.breaches} sur {t.checked}</span>{cost}</li>')
        html(f'<ul class="sx-c-ledger">{"".join(rows)}</ul>')
    with right:
        top = rep.priority
        if top is None:
            html(f'<div class="sx-c-todo calm"><div class="rub">Rien à corriger</div>'
                 '<h4>Chaque règle a tenu sur la période.</h4><p>Le plan lui-même se juge à la revue mensuelle, '
                 'sur un échantillon suffisant.</p></div>')
            return
        page, fields = spaces.parse_target(top.lesson)
        html(f'<div class="sx-c-todo"><div class="rub">{brand.hook_svg(13)}À travailler en premier</div>'
             f'<h4>{esc(top.label)}</h4><p>{_plural(top.breaches, "écart")} sur {top.checked} trades, pour '
             f'{esc(V.r_text(top.cost_r))}. La leçon qui traite cet écart :</p></div>')
        rt.link(f"Lire : {top.lesson_title}", page, key=f"priority_{key}", kind="primary", width="stretch",
                **fields)


def _regularity(trades: list[Trade]) -> None:
    daily = R.daily_r(trades)
    end = max(t.closed_at for t in trades).date()
    left, right = st.columns([1.9, 1], gap="large")
    with left:
        html(V.calendar(daily, end=end, weeks=13) + V.calendar_legend())
    with right:
        if not daily:
            note("Aucun jour avec un résultat en R.")
            return
        green = sum(1 for v, _ in daily.values() if v > 0)
        best = max(daily.items(), key=lambda kv: kv[1][0])
        worst = min(daily.items(), key=lambda kv: kv[1][0])
        html('<dl class="sx-facts">'
             f'<div><dt>Jours tradés</dt><dd>{len(daily)}</dd></div>'
             f'<div><dt>Jours gagnants</dt><dd>{green} sur {len(daily)}</dd></div>'
             f'<div><dt>Meilleur jour</dt><dd>{esc(V.r_text(best[1][0]))} · {esc(date_fr(best[0]))}</dd></div>'
             f'<div><dt>Pire jour</dt><dd>{esc(V.r_text(worst[1][0]))} · {esc(date_fr(worst[0]))}</dd></div>'
             '</dl>')


def _breakdowns(trades: list[Trade]) -> None:
    def table(rows, title):
        body = "".join(
            f"<tr><td>{esc(r['label'])}{'' if r['reliable'] else '<small>échantillon faible</small>'}</td>"
            f"<td>{r['n']}</td>"
            f"<td>{'n.d.' if r['win_rate'] is None else str(round(r['win_rate'] * 100)) + ' %'}</td>"
            f"<td><span class='sx-j-r {V.tone(r['avg_r'])}'>{esc(V.r_text(r['avg_r']))}</span></td></tr>"
            for r in rows)
        return (f'<table class="sx-j-table"><thead><tr><th>{esc(title)}</th><th>Trades</th><th>Réussite</th>'
                f'<th>Espérance</th></tr></thead><tbody>{body}</tbody></table>')
    left, right = st.columns(2, gap="large")
    with left:
        html(table(performance.by_setup(trades, "fr"), "Setup"))
    with right:
        rows = performance.by_session(trades, "fr")
        for r in rows:
            r["label"] = V.SESSION_SHORT.get(r["key"].value, r["label"])
        html(table(rows, "Séance"))
    note("Moins de dix trades : un chiffre qui peut changer du tout au tout au trade suivant. "
         "Une espérance se juge sur un échantillon, voir la leçon « Combien de trades pour savoir ? ».")


# =============================================================================
# TRADES
# =============================================================================

def trades_page(catalog, email, route) -> None:
    _header("Trades", "Tous vos <em>trades</em>.", "Du plus récent au plus ancien, avec leur score de "
            "respect du plan et leur résultat en R.")
    book = _book(email)
    nav("journal_trades", email)
    _demo_banner(book, email, key="trades")
    if not book.closed:
        _empty_state(email)
        footer()
        return
    with st.container(key="panel_jr_filters"):
        a, b, c = st.columns(3)
        with a:
            symbols = sorted({t.symbol for t in book.closed})
            symbol = st.selectbox("Actif", [""] + symbols, format_func=lambda s: s or "Tous", key="jr_f_symbol")
        with b:
            result = st.selectbox("Résultat", ["", "win", "loss"], key="jr_f_result",
                                  format_func=lambda k: {"": "Tous", "win": "Gagnants", "loss": "Perdants"}[k])
        with c:
            plan = st.selectbox("Plan", ["", "off", "on"], key="jr_f_plan",
                                format_func=lambda k: {"": "Tous", "off": "Avec un écart", "on": "Plan respecté"}[k])
    shown = sorted(book.closed, key=lambda t: t.closed_at, reverse=True)
    if symbol:
        shown = [t for t in shown if t.symbol == symbol]
    if result:
        shown = [t for t in shown if t.pnl is not None and ((t.pnl > 0) == (result == "win")) and t.pnl != 0]
    if plan:
        shown = [t for t in shown if (book.reviews.get(t.id) and book.reviews[t.id].followed is (plan == "on"))]
    html(f'<p class="sx-note">{len(shown)} trade{"s" if len(shown) > 1 else ""} sur {len(book.closed)}.</p>')
    page_no = int(st.session_state.get("jr_page", 1))
    pages = max(1, -(-len(shown) // PAGE_SIZE))
    page_no = min(page_no, pages)
    for t in shown[(page_no - 1) * PAGE_SIZE: page_no * PAGE_SIZE]:
        trade_row(t, book.reviews.get(t.id), key="list")
    if pages > 1:
        prev, mid, nxt = st.columns([1, 2, 1])
        with prev:
            if st.button("Plus récents", key="jr_prev", disabled=page_no <= 1):
                st.session_state["jr_page"] = page_no - 1
                st.rerun()
        with mid:
            html(f'<p class="sx-note" style="text-align:center">Page {page_no} sur {pages}</p>')
        with nxt:
            if st.button("Plus anciens", key="jr_next", disabled=page_no >= pages):
                st.session_state["jr_page"] = page_no + 1
                st.rerun()
    footer()


# =============================================================================
# ONE TRADE
# =============================================================================

def trade_page(catalog, email, route) -> None:
    book = _book(email)
    trade = book.trade(route.get("trade"))
    if trade is None or not trade.is_closed:
        _header("Trade", "Trade <em>introuvable</em>.", "Ce trade n'existe pas dans le journal affiché.")
        nav("journal_trade", email)
        rt.link("Retour aux trades", "journal_trades", key="trade_missing_back", kind="primary")
        footer()
        return
    review = book.reviews.get(trade.id)
    local = _paris(trade.opened_at)
    _header(trade.symbol, f"{esc(trade.symbol)} <em>{_side(trade).lower()}</em>",
            f"Ouvert le {date_fr(local, with_day=True)} à {local:%H:%M}, heure de Paris.")
    nav("journal_trade", email)
    _demo_banner(book, email, key="trade")

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        with st.container(key="panel_jr_ladder"):
            html(V.levels(trade.to_dict(), uid=f"lv{trade.id}"))
    with right:
        r = trade.r_multiple
        kept = f"{review.passed} règle{'s' if review.passed > 1 else ''} sur {len(review.evaluated)}" if review and review.evaluated else ""
        with st.container(key="navy_jr_result"):
            html(f'<div class="sx-c-verdict"><div class="k">Résultat</div><div class="r {V.tone(r)}">{esc(V.r_text(r))}</div>'
                 f'<p>{esc(_result_line(trade, review))}</p>'
                 + (f'<div class="pr">{V.rule_print(review.checks, big=True)}<span>{esc(kept)} tenues</span></div>' if kept else "")
                 + '</div>')
        html(_facts(trade))

    section(1, "La revue automatique", "Votre plan, règle par règle, appliqué à ce trade. Une règle non "
            "vérifiable n'est comptée ni pour ni contre.")
    if review:
        html(V.checks_list(review.checks))
        _lessons_for(review, key=f"trade_{trade.id}")
    if book.demo:
        note("Dans votre propre journal, vous pourriez annoter ce trade et demander sa revue à un coach.")
        _neighbours(book, trade)
        footer()
        return

    section(2, "Vos annotations", "Ce que vous avez noté sur ce trade. Les écarts que vous déclarez comptent "
            "dans la revue : c'est vous qui savez ce qui s'est passé.")
    _annotate(trade, email)

    section(3, "Demander la revue d'un coach", "Un coach Sensitor relit ce trade, sa revue automatique et "
            "votre question, puis vous répond dans l'onglet Revues.")
    from .trade_reviews import request_form
    request_form(trade, review, book.plan if book.plan_written else None, email)
    _neighbours(book, trade)
    footer()


def _result_line(trade: Trade, review: R.TradeReview | None) -> str:
    money = f"{V.signed(trade.pnl)} {_currency(trade.account_currency)}" if trade.pnl is not None else ""
    if review is None or review.followed is None:
        verdict = "aucune règle vérifiable"
    elif review.followed:
        verdict = "plan respecté"
    else:
        verdict = f"{len(review.failed)} écart{'s' if len(review.failed) > 1 else ''} au plan"
    return " · ".join(x for x in (money, verdict) if x)


def _facts(trade: Trade) -> str:
    cur = _currency(trade.account_currency)
    rr = trade.planned_rr
    rows = (
        ("Risque engagé", f"{V.fr(trade.risk_amount)} {cur}" if trade.risk_amount else "sans stop"),
        ("Rapport prévu", "n.d." if rr is None else V.fr(rr)),
        ("Séance", V.SESSION_SHORT.get(trade.session.value, "")),
        ("Durée", _duration(trade.duration_minutes)),
        ("Setup", _setups_text(trade)),
        ("État avant", EMOTIONS.get(trade.emotion_before or "", {}).get("fr", trade.emotion_before or "non noté")),
        ("Écarts notés", ", ".join(mistake_label(m, "fr").lower() for m in trade.mistakes) or "aucun"),
        ("Source", {"manual": "saisie", "mt5": "MetaTrader 5", "demo": "exemple"}.get(trade.source, trade.source)),
    )
    return '<dl class="sx-j-facts">' + "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in rows) + "</dl>"


def _duration(minutes: float | None) -> str:
    if minutes is None:
        return "n.d."
    minutes = int(round(minutes))
    if minutes < 60:
        return f"{minutes} min"
    hours, rest = divmod(minutes, 60)
    if hours >= 48:
        return f"{hours // 24} jours"
    return f"{hours} h {rest:02d}" if rest else f"{hours} h"


def lesson_ref(key: str, target: str, title: str, why: str) -> None:
    """A lesson to read, as a reference with the hook: the journal points to the Academy, it is not a chapter."""
    page, fields = spaces.parse_target(target)
    tap(key, f'<div class="sx-c-ref">{brand.hook_svg(15, color=V.K["note"])}<div><div class="t">{esc(title)}</div>'
             f'<div class="s">{esc(why)}</div></div><span class="go">{icon("arrow")}</span></div>',
        f"Leçon : {title}", page, **fields)


def _lessons_for(review: R.TradeReview, *, key: str) -> None:
    lessons = list(dict.fromkeys((c.lesson, c.lesson_title, c.label) for c in review.failed if c.lesson))
    if not lessons:
        return
    html('<div class="sx-kicker" style="margin-top:1.4rem">Pour progresser</div>')
    for i, (target, title, rule) in enumerate(lessons):
        lesson_ref(f"lesson_{key}_{i}", target, title, f"Academy · pour la règle « {rule.lower()} »")


def _neighbours(book: Book, trade: Trade) -> None:
    ordered = sorted(book.closed, key=lambda t: t.closed_at)
    i = next((k for k, t in enumerate(ordered) if t.id == trade.id), None)
    if i is None:
        return
    a, b = st.columns(2)
    with a:
        if i > 0:
            rt.link("Trade précédent", "journal_trade", key="trade_prev", trade=ordered[i - 1].id)
    with b:
        if i + 1 < len(ordered):
            rt.link("Trade suivant", "journal_trade", key="trade_next", trade=ordered[i + 1].id)


def _annotate(trade: Trade, email: str) -> None:
    store = rt.get_store()
    with st.container(key="panel_jr_annotate"):
        with st.form(f"jr_annotate_{trade.id}", border=False):
            a, b = st.columns(2)
            with a:
                setups = st.multiselect("Setup", SETUP_KEYS, default=[s for s in trade.setups if s in SETUPS],
                                        format_func=lambda k: setup_label(k, "fr"), key=f"jr_an_setups_{trade.id}", placeholder="Choisir")
            with b:
                mistakes = st.multiselect("Écarts à votre plan", MISTAKE_KEYS,
                                          default=[m for m in trade.mistakes if m in MISTAKES],
                                          format_func=lambda k: mistake_label(k, "fr"), key=f"jr_an_mistakes_{trade.id}", placeholder="Choisir")
            c, d = st.columns(2)
            with c:
                emotions = [""] + list(EMOTIONS)
                emotion = st.selectbox("État avant le trade", emotions,
                                       index=emotions.index(trade.emotion_before) if trade.emotion_before in EMOTIONS else 0,
                                       format_func=lambda k: EMOTIONS[k]["fr"] if k else "Non noté",
                                       key=f"jr_an_emotion_{trade.id}")
            with d:
                discipline = st.select_slider("Discipline ressentie", options=[0, 1, 2, 3, 4, 5],
                                              value=trade.discipline or 0,
                                              format_func=lambda v: "non noté" if not v else f"{v} sur 5",
                                              key=f"jr_an_disc_{trade.id}")
            notes = st.text_area("Notes", value=trade.notes or "", max_chars=2000, height=110,
                                 key=f"jr_an_notes_{trade.id}")
            if st.form_submit_button("Enregistrer les annotations", type="primary"):
                updated = trade.annotated(setups=list(setups), mistakes=list(mistakes), emotion_before=emotion or None,
                                          discipline=discipline or None, notes=notes.strip() or None)
                store.save_trade(email, updated)
                flash("Annotations enregistrées. La revue en tient compte.")
                st.rerun()
    if trade.source == "manual" or trade.id.startswith(("m-", "csv-")):
        if st.session_state.get("jr_delete") == trade.id:
            html('<p class="sx-note">Supprimer définitivement ce trade de votre journal ?</p>')
            yes, no, _ = st.columns([1, 1, 3])
            with yes:
                if st.button("Oui, supprimer", key="jr_del_yes", type="primary"):
                    store.delete_trade(email, trade.id)
                    st.session_state.pop("jr_delete", None)
                    rt.go("journal_trades")
                    st.rerun()
            with no:
                if st.button("Annuler", key="jr_del_no"):
                    st.session_state.pop("jr_delete", None)
                    st.rerun()
        elif st.button("Supprimer ce trade", key="jr_del", type="tertiary"):
            st.session_state["jr_delete"] = trade.id
            st.rerun()


# =============================================================================
# ENTER AND IMPORT
# =============================================================================

def add_page(catalog, email, route) -> None:
    _header("Saisir", "Ajouter des <em>trades</em>.", "Saisissez un trade avec ce que vous savez déjà : vos "
            "prix et le montant risqué. La taille de position et le résultat en R sont calculés pour vous.")
    nav("journal_add", email)
    if not email:
        _signin_prompt("add", "Connectez-vous pour saisir vos trades.")
        footer()
        return
    store = rt.get_store()
    section(1, "Saisir un trade", "Heures de Paris. Avec un stop, le risque en argent suffit : la taille "
            "est déduite de la distance au stop.")
    _entry_form(store, email)
    section(2, "Importer un fichier", "Un tableur au format du modèle : une ligne par trade. Séparateur "
            "« ; » ou « , », virgule décimale acceptée.")
    _import(store, email)
    section(3, "Synchroniser MetaTrader 5", "Votre historique lu directement dans le terminal : chaque trade "
            "arrive avec ses prix, son stop et son résultat, prêt pour la revue.")
    from . import journal_analysis
    journal_analysis.sync_section(store, email)
    footer()


def _entry_form(store, email: str) -> None:
    with st.container(key="panel_jr_entry"):
        with st.form("jr_entry", clear_on_submit=False, border=False):
            a, b, c = st.columns([1.2, 1, 1])
            with a:
                symbol = st.text_input("Actif", placeholder="EURUSD, XAUUSD, NAS100...", key="jr_e_symbol")
            with b:
                side = st.radio("Sens", ["long", "short"], format_func=lambda k: "Achat" if k == "long" else "Vente",
                                horizontal=True, key="jr_e_side")
            with c:
                day = st.date_input("Date", value=date.today(), format="DD/MM/YYYY", key="jr_e_day")
            d, e, f = st.columns(3)
            with d:
                opened = st.time_input("Heure d'ouverture", value=time(9, 30), key="jr_e_open")
            with e:
                closed = st.time_input("Heure de fermeture", value=time(10, 30), key="jr_e_close")
            with f:
                next_day = st.checkbox("Fermé un autre jour", key="jr_e_nextday")
                close_day = st.date_input("Date de fermeture", value=date.today(), format="DD/MM/YYYY",
                                          key="jr_e_closeday", label_visibility="collapsed") if next_day else None
            g, h, i, j = st.columns(4)
            with g:
                price_in = st.number_input("Entrée", min_value=0.0, value=None, format="%.5f", key="jr_e_entry")
            with h:
                stop = st.number_input("Stop", min_value=0.0, value=None, format="%.5f", key="jr_e_stop")
            with i:
                target = st.number_input("Objectif", min_value=0.0, value=None, format="%.5f", key="jr_e_target")
            with j:
                price_out = st.number_input("Sortie", min_value=0.0, value=None, format="%.5f", key="jr_e_exit")
            k, l, m = st.columns(3)
            with k:
                risk = st.number_input("Risque engagé (montant)", min_value=0.0, value=None, format="%.2f",
                                       key="jr_e_risk", help="Ce que vous perdiez au stop, en devise du compte.")
            with l:
                result = st.number_input("Résultat net réel (facultatif)", value=None, format="%.2f",
                                         key="jr_e_result", help="Celui de votre courtier, frais compris. "
                                         "Sinon il est calculé depuis les prix.")
            with m:
                currency = st.selectbox("Devise", ["EUR", "USD", "GBP", "CHF"], key="jr_e_currency")
            n, o, p = st.columns(3)
            with n:
                setups = st.multiselect("Setup", SETUP_KEYS, format_func=lambda k: setup_label(k, "fr"), key="jr_e_setups", placeholder="Choisir")
            with o:
                mistakes = st.multiselect("Écarts à votre plan", MISTAKE_KEYS,
                                          format_func=lambda k: mistake_label(k, "fr"), key="jr_e_mistakes", placeholder="Choisir")
            with p:
                emotions = [""] + list(EMOTIONS)
                emotion = st.selectbox("État avant le trade", emotions,
                                       format_func=lambda k: EMOTIONS[k]["fr"] if k else "Non noté", key="jr_e_emotion")
            notes = st.text_area("Notes", max_chars=2000, height=90, key="jr_e_notes",
                                 placeholder="Le contexte, la raison de l'entrée, ce que vous referiez autrement.")
            if st.form_submit_button("Enregistrer le trade", type="primary"):
                try:
                    end_day = close_day if next_day and close_day else day
                    trade = E.build_trade(
                        symbol=symbol, direction=side, opened_at=datetime.combine(day, opened),
                        closed_at=datetime.combine(end_day, closed), entry=price_in, exit=price_out,
                        stop=stop, target=target, risk=risk, result=result, setups=setups,
                        mistakes=mistakes, notes=notes, emotion=emotion or None, currency=currency)
                except ValueError as exc:
                    st.error(f"Ce trade n'a pas pu être enregistré : {exc}.")
                else:
                    store.save_trades(email, [trade])
                    st.session_state["jr_last_saved"] = trade.id
                    st.success(f"Trade enregistré : {trade.symbol}, {V.r_text(trade.r_multiple)}.")
    last = st.session_state.get("jr_last_saved")
    if last and store.get_trade(email, last):
        rt.link("Voir ce trade et sa revue", "journal_trade", key="jr_see_saved", kind="primary", trade=last)


def _import(store, email: str) -> None:
    with st.container(key="panel_jr_import"):
        st.download_button("Télécharger le modèle (CSV)", data=E.template_csv().encode("utf-8"),
                           file_name="sensitor-modele-trades.csv", mime="text/csv", key="jr_template")
        upload = st.file_uploader("Votre fichier", type=["csv", "txt"], key="jr_upload")
        currency = st.selectbox("Devise du compte", ["EUR", "USD", "GBP", "CHF"], key="jr_i_currency")
        if upload is None:
            return
        raw = upload.getvalue()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        trades, errors = E.parse_csv(text, currency=currency)
        html(f'<p class="sx-note"><b>{len(trades)}</b> trade{"s" if len(trades) > 1 else ""} lisible'
             f'{"s" if len(trades) > 1 else ""}, <b>{len(errors)}</b> ligne{"s" if len(errors) > 1 else ""} '
             f'à corriger.</p>')
        if errors:
            rows = "".join(f"<tr><td>{n}</td><td>{esc(msg)}</td></tr>" for n, msg in errors[:12])
            html(f'<table><thead><tr><th>Ligne</th><th>Problème</th></tr></thead><tbody>{rows}</tbody></table>')
            if len(errors) > 12:
                note(f"Et {len(errors) - 12} autres lignes.")
        if trades and st.button(f"Importer {len(trades)} trade{'s' if len(trades) > 1 else ''}",
                                key="jr_import_go", type="primary"):
            written = store.save_trades(email, trades)
            st.success(f"{written} trade{'s' if written > 1 else ''} importé{'s' if written > 1 else ''}. "
                       "Un fichier importé deux fois met à jour les mêmes trades, sans doublon.")


# =============================================================================
# THE PLAN
# =============================================================================

_PLAN_ERRORS = {
    "capital": "Le capital doit être un montant positif.",
    "risk_pct": "Le risque par trade doit être un pourcentage positif, au plus 100.",
    "min_rr": "Le rapport minimum doit être un nombre positif.",
    "max_trades_per_day": "Le nombre de trades par jour doit être un entier positif.",
    "daily_loss_r": "La limite de perte du jour doit être un nombre de R positif.",
    "pause_after_losses": "Le nombre de pertes avant la pause doit être un entier positif.",
}


def plan_page(catalog, email, route) -> None:
    _header("Mon plan", "Votre plan, <em>écrit</em>.", "Les règles que la revue automatique vérifie sur "
            "chaque trade. Laissez une règle vide pour qu'elle ne soit pas vérifiée.")
    nav("journal_plan", email)
    if not email:
        book = _book(None)
        _plan_card(book.plan, demo_plan=True)
        _signin_prompt("plan", "Connectez-vous pour écrire votre plan.")
        footer()
        return
    store = rt.get_store()
    saved = store.get_trading_plan(email)
    plan = R.TradingPlan.from_dict(saved) if saved else R.DEFAULT_PLAN
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        section(1, "Les règles", "Elles s'appliquent à tous vos trades, passés compris.", compact=True)
        _plan_form(store, email, plan)
    with right:
        section(2, "Votre plan, en clair", "Ce que la revue lira.", compact=True)
        _plan_card(plan, demo_plan=False, written=saved is not None)
        page, fields = spaces.parse_target("lesson:processus-de-trading/plan-de-trading")
        rt.link("Leçon : écrire son plan de trading", page, key="plan_lesson", width="stretch", **fields)
        rt.link("Le modèle de plan à remplir", "resource", key="plan_resource", width="stretch",
                resource="modele-plan-de-trading")
    footer()


def _plan_card(plan: R.TradingPlan, *, demo_plan: bool, written: bool = True) -> None:
    items = "".join(f"<li>{esc(s)}</li>" for s in R.plan_sentences(plan))
    kicker = "Exemple synthétique · le plan du trader fictif" if demo_plan else (
        "Votre plan" if written else "Plan de départ, pas encore enregistré")
    with st.container(key="navy_jr_plan"):
        html(f'<div class="sx-kicker on-navy">{esc(kicker)}</div><ol class="sx-j-plan">{items}</ol>')


def _plan_form(store, email: str, plan: R.TradingPlan) -> None:
    with st.container(key="panel_jr_plan"):
        with st.form("jr_plan", border=False):
            a, b, c = st.columns(3)
            with a:
                capital = st.number_input("Capital du compte", min_value=0.0, value=plan.capital, format="%.0f",
                                          key="jr_p_capital")
            with b:
                currency = st.selectbox("Devise", ["EUR", "USD", "GBP", "CHF"],
                                        index=["EUR", "USD", "GBP", "CHF"].index(plan.currency), key="jr_p_currency")
            with c:
                risk_pct = st.number_input("Risque maximum par trade (%)", min_value=0.0, max_value=100.0,
                                           value=plan.risk_pct, step=0.25, format="%.2f", key="jr_p_risk")
            d, e = st.columns(2)
            with d:
                min_rr = st.number_input("Rapport gain sur risque minimum", min_value=0.0, value=plan.min_rr,
                                         step=0.25, format="%.2f", key="jr_p_rr")
            with e:
                require_stop = st.checkbox("Un stop obligatoire sur chaque trade", value=plan.require_stop,
                                           key="jr_p_stop")
            sessions = st.multiselect("Séances autorisées (vide : toutes)", list(R.SESSION_CHOICES),
                                      default=list(plan.sessions), format_func=lambda s: R.SESSION_NAMES[s],
                                      key="jr_p_sessions", placeholder="Choisir")
            setups = st.multiselect("Setups du plan (vide : tout setup déclaré)", SETUP_KEYS,
                                    default=[s for s in plan.setups if s in SETUPS],
                                    format_func=lambda k: setup_label(k, "fr"), key="jr_p_setups", placeholder="Choisir")
            require_setup = st.checkbox("Chaque trade doit porter son setup", value=plan.require_setup,
                                        key="jr_p_reqsetup")
            f, g, h = st.columns(3)
            with f:
                per_day = st.number_input("Trades par jour, au plus", min_value=0, value=plan.max_trades_per_day,
                                          step=1, key="jr_p_perday")
            with g:
                daily = st.number_input("Arrêt après une perte du jour de (R)", min_value=0.0,
                                        value=plan.daily_loss_r, step=0.5, format="%.1f", key="jr_p_daily")
            with h:
                pause = st.number_input("Arrêt après N pertes d'affilée", min_value=0, value=plan.pause_after_losses,
                                        step=1, key="jr_p_pause")
            if st.form_submit_button("Enregistrer mon plan", type="primary"):
                try:
                    cleaned = R.clean_plan(dict(
                        capital=capital, currency=currency, risk_pct=risk_pct, require_stop=require_stop,
                        min_rr=min_rr, sessions=sessions, setups=setups, require_setup=require_setup,
                        max_trades_per_day=per_day, daily_loss_r=daily, pause_after_losses=pause))
                except ValueError as exc:
                    field_name = str(exc).split(" ")[0]
                    st.error(_PLAN_ERRORS.get(field_name, "Ce plan n'a pas pu être enregistré."))
                else:
                    store.save_trading_plan(email, cleaned.to_dict())
                    flash("Plan enregistré. Tous vos trades sont revus avec ces règles.")
                    st.rerun()
