"""
The challenge simulator: the odds of passing a prop firm challenge, for given
statistics or for the member's own journal.

Presentation only: every figure comes from `sensitor.academy.propfirm`. The
member's trades are read for the verified email of this session and never
cached; the odds themselves depend on numbers alone.
"""

from __future__ import annotations

import streamlit as st

from .. import expectancy as E
from .. import propfirm as P
from ...platform.ui import runtime as rt
from ...platform.ui.components import date_fr, esc, html, number, percent

MIN_TRADES = 20      # below this, the journal's figures are not offered


def _cell(label: str, value: str, detail: str = "", emph: bool = False) -> str:
    detail_html = f'<div class="d">{detail}</div>' if detail else ""
    return (f'<div{" class=emph" if emph else ""}><div class="l">{esc(label)}'
            f'</div><div class="v">{value}</div>{detail_html}</div>')


def _share(x: float) -> str:
    return "< 0,1 %" if 0 < x < 0.001 else percent(x * 100)


def journal_profile(email: str | None) -> P.Profile | None:
    """Win rate and average R of the member's closed trades with a stop, or None."""
    store = rt.get_store()
    if not email or store is None:
        return None
    try:
        trades = store.list_trades(email)
    except Exception:                                    # noqa: BLE001
        return None
    results = [t.r_multiple for t in trades if t.is_closed and t.r_multiple is not None]
    profile = P.profile_from_r(results)
    return profile if profile and profile.trades >= MIN_TRADES else None


def render(*, scope: str) -> None:
    k = f"prop_{scope}"
    email = rt.current_user()
    mine = journal_profile(email)
    with st.container(key=f"panel_{k}"):
        html('<div class="sx-kicker">Simulateur pédagogique</div>'
             '<h2 class="sx-h3">Ses chances de réussir un challenge</h2>'
             '<p class="sx-body">Probabilité exacte d\'atteindre l\'objectif avant les limites de perte, '
             'pour les règles publiées par la société et les statistiques indiquées. Ce n\'est pas une '
             'prévision : les hypothèses sont écrites sous les résultats.</p>')
        names = {rid: f"{r.firm} · {r.product}" for rid, r in P.RULESETS.items()}
        rid = st.selectbox("Challenge", list(names), format_func=names.get, key=f"{k}_rules")
        rules = P.ruleset(rid)

        use_mine = False
        if mine:
            use_mine = st.toggle(f"Utiliser les chiffres de mon journal ({mine.trades} trades fermés)",
                                 key=f"{k}_mine")
        elif email:
            html(f'<p class="sx-note">Avec au moins {MIN_TRADES} trades fermés et leur stop dans votre '
                 'journal de trading, le simulateur peut reprendre vos propres chiffres.</p>')

        if use_mine:
            win, reward, loss = mine.win_rate * 100, mine.reward_r, mine.loss_r
            html('<div class="sx-figures three">'
                 + _cell("Taux de réussite", percent(win), f"sur {mine.trades} trades fermés")
                 + _cell("Gain moyen", f"{number(reward, 2)} R")
                 + _cell("Perte moyenne", f"{number(loss, 2)} R") + "</div>")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                win = st.number_input("Taux de réussite (%)", min_value=1.0, max_value=99.0, value=45.0,
                                      step=1.0, format="%.0f", key=f"{k}_win")
            with c2:
                reward = st.number_input("Gain moyen (R)", min_value=0.1, max_value=10.0, value=1.5,
                                         step=0.1, format="%.1f", key=f"{k}_reward")
            with c3:
                loss = st.number_input("Perte moyenne (R)", min_value=0.5, max_value=3.0, value=1.0,
                                       step=0.1, format="%.1f", key=f"{k}_loss")
        c1, c2, c3 = st.columns(3)
        with c1:
            risk_pct = st.number_input("Risque par trade (% du solde initial)", min_value=0.1,
                                       max_value=5.0, value=1.0, step=0.25, format="%.2f",
                                       key=f"{k}_risk")
        with c2:
            per_day = st.number_input("Trades par jour", min_value=1, max_value=6, value=2, step=1,
                                      key=f"{k}_perday")
        with c3:
            fee = st.number_input("Frais d'une tentative ($, facultatif)", min_value=0.0,
                                  max_value=5000.0, value=0.0, step=50.0, format="%.0f", key=f"{k}_fee")

        p = win / 100
        odds = P.pass_odds(rules, win_rate=p, reward_r=reward, risk_pct=risk_pct,
                           trades_per_day=int(per_day), loss_r=loss)
        edge = E.expectancy_r(p, reward, loss)
        risk_dollars = rules.account * risk_pct / 100
        cells = [
            _cell("Réussir", _share(odds.passed), f"en {number(odds.mean_trades_to_pass, 0)} trades en "
                  "moyenne" if odds.passed > 0 else "aucun chemin ne réussit", emph=True),
            _cell("Éliminé par la perte maximale", _share(odds.failed_max),
                  f"{P.losses_to(rules.max_loss, risk_dollars)} pertes de {number(risk_dollars, 0)} $ au départ"),
            _cell("Éliminé par la perte journalière", _share(odds.failed_daily),
                  "la limite arrête seulement la séance" if not rules.daily_loss_fails else
                  (f"{P.losses_to(rules.daily_loss, risk_dollars)} pertes le même jour"
                   if rules.daily_loss else "aucune limite journalière")),
            _cell("Ni l'un ni l'autre après 400 trades", _share(odds.running), "la course continue"),
        ]
        html('<div class="sx-figures four">' + "".join(cells) + "</div>")

        facts = [f"Espérance : {'+' if edge > 0 else ''}{number(edge, 3)} R par trade."]
        if fee > 0:
            cost = P.cost_per_pass(fee, odds.passed)
            facts.append("Coût moyen d'une réussite : "
                         + ("aucune réussite possible." if cost == float("inf") else f"{number(cost, 0)} $."))
        if use_mine:
            wins = round(mine.win_rate * mine.trades)
            interval = E.win_rate_interval(wins, mine.trades)
            low = P.pass_odds(rules, win_rate=interval.low, reward_r=reward, risk_pct=risk_pct,
                              trades_per_day=int(per_day), loss_r=loss).passed
            high = P.pass_odds(rules, win_rate=interval.high, reward_r=reward, risk_pct=risk_pct,
                               trades_per_day=int(per_day), loss_r=loss).passed
            facts.append(f"Sur {mine.trades} trades, votre taux de réussite se situe, avec 95 % de "
                         f"confiance, entre {percent(interval.low * 100)} et {percent(interval.high * 100)} : "
                         f"vos chances, entre {_share(low)} et {_share(high)}.")
        html('<ul class="sx-c-facts">' + "".join(f"<li>{esc(f)}</li>" for f in facts) + "</ul>")

        sources = " ; ".join(f"{label}, mis à jour le {date_fr(updated)}" for label, _url, updated in rules.sources)
        html('<p class="sx-note" style="margin-top:.8rem">Hypothèses : risque constant en part du solde '
             'initial, trades indépendants à taux de réussite constant, jugés sur les positions fermées ; '
             'le trader s\'arrête pour la journée quand l\'objectif est atteint ; la règle de régularité '
             f'n\'est pas comptée. Règles : {esc(sources)}, consultées le 25 octobre 2026.</p>')
