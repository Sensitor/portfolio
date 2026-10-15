"""
The risk calculator, used on the lab page and inside the risk lesson.

Every figure on screen comes from `academy.risk`. Position size is shown only
when a contract specification is given; the one preset — EURUSD on a dollar
account — rests on the standard-lot convention and says so, and the custom mode
asks for the broker's own figures. Nothing is assumed about gold, indices or
shares.
"""

from __future__ import annotations

import streamlit as st

from .. import risk as R
from .components import esc, html, money, number, percent

CURRENCIES = ("USD", "EUR", "GBP", "CHF")
SPEC_NONE = "Ne pas calculer la taille"
SPEC_EURUSD = "EURUSD sur un compte en USD (lot standard)"
SPEC_CUSTOM = "Saisir la spécification de mon courtier"


def render(*, scope: str, compact: bool = False) -> None:
    k = f"risk_{scope}"
    with st.container(key=f"panel_{k}"):
        html('<div class="ac-eyebrow">Calculateur pédagogique</div>'
             '<h3 class="ac-h3" style="margin-top:.5rem">Budget de risque et taille de position</h3>'
             '<p class="ac-sub">Estimation éducative. Elle ne remplace pas le calcul de votre '
             'plateforme, qui seule connaît les conditions exactes de votre compte.</p>')

        c1, c2, c3 = st.columns(3)
        with c1:
            equity = st.number_input("Capital du compte", min_value=0.0, value=10_000.0,
                                     step=500.0, format="%.2f", key=f"{k}_equity")
        with c2:
            currency = st.selectbox("Devise du compte", CURRENCIES, key=f"{k}_ccy")
        with c3:
            risk_pct = st.number_input("Risque par position (%)", min_value=0.0, max_value=100.0,
                                       value=1.0, step=0.25, format="%.2f", key=f"{k}_pct")

        with st.container(key=f"inline_{k}_dir"):
            direction = st.radio("Sens", ["Achat", "Vente"], horizontal=True, key=f"{k}_dir")
        c1, c2, c3 = st.columns(3)
        with c1:
            entry = st.number_input("Prix d'entrée", min_value=0.0, value=1.0850, step=0.0001,
                                    format="%.5f", key=f"{k}_entry")
        with c2:
            stop = st.number_input("Stop-loss", min_value=0.0, value=1.0820, step=0.0001,
                                   format="%.5f", key=f"{k}_stop")
        with c3:
            target_raw = st.number_input("Objectif (facultatif, 0 = aucun)", min_value=0.0,
                                         value=1.0910, step=0.0001, format="%.5f",
                                         key=f"{k}_target")
        target = target_raw or None

        mode = st.radio("Taille de position", [SPEC_NONE, SPEC_EURUSD, SPEC_CUSTOM],
                        index=1, key=f"{k}_mode")
        spec = _spec(mode, k, currency)

        try:
            plan = R.plan(equity=equity, risk_pct=risk_pct, entry=entry, stop=stop,
                          direction=R.LONG if direction == "Achat" else R.SHORT,
                          target=target, spec=spec)
        except R.RiskInputError as exc:
            for message in exc.errors.values():
                st.error(message)
            return

        _figures(plan, currency, spec)
        if not compact:
            _streaks(plan, currency, k)


def _spec(mode: str, k: str, currency: str) -> R.InstrumentSpec | None:
    if mode == SPEC_NONE:
        return None
    if mode == SPEC_EURUSD:
        if currency != "USD":
            st.warning("Ce préréglage suppose un compte en dollars : la valeur d'un pip "
                       "d'EURUSD n'est de 10 $ par lot que dans ce cas. Choisissez « USD » "
                       "ou saisissez la spécification de votre courtier.")
            return None
        html('<p class="ac-note">Convention du marché des changes : 1 lot = 100 000 unités, '
             '1 pip = 0,0001, pas de volume de 0,01 lot. Vérifiez la spécification de votre '
             'courtier, qui peut différer.</p>')
        return R.InstrumentSpec(contract_size=100_000, quote_to_account=1.0, lot_step=0.01,
                                min_lot=0.01, pip_size=0.0001, label="EURUSD · USD")
    html('<p class="ac-note">Recopiez les valeurs de la fiche de l\'instrument chez votre '
         'courtier. Si l\'instrument est coté dans une autre devise que celle du compte, '
         'indiquez la valeur d\'une unité de cette devise dans la devise du compte.</p>')
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        contract = st.number_input("Unités par lot", min_value=0.0, value=0.0, step=1.0,
                                   format="%.4f", key=f"{k}_contract")
    with c2:
        rate = st.number_input(f"1 unité de cotation = … {currency}", min_value=0.0,
                               value=1.0, step=0.0001, format="%.5f", key=f"{k}_rate")
    with c3:
        step = st.number_input("Pas de volume (lot)", min_value=0.0, value=0.01, step=0.01,
                               format="%.4f", key=f"{k}_step")
    with c4:
        pip = st.number_input("Taille du pip (0 = aucun)", min_value=0.0, value=0.0,
                              step=0.0001, format="%.5f", key=f"{k}_pip")
    if contract <= 0:
        html('<p class="ac-note">Indiquez le nombre d\'unités par lot pour calculer la taille.</p>')
        return None
    return R.InstrumentSpec(contract_size=contract, quote_to_account=rate,
                            lot_step=step or None, min_lot=step or None, pip_size=pip or None)


def _cell(label: str, value: str, detail: str = "", emph: bool = False) -> str:
    detail_html = f'<div class="detail">{detail}</div>' if detail else ""
    return (f'<div class="ac-figure-cell{" emph" if emph else ""}"><div class="label">{esc(label)}'
            f'</div><div class="value">{value}</div>{detail_html}</div>')


def _figures(plan: R.RiskPlan, currency: str, spec: R.InstrumentSpec | None) -> None:
    cells = [_cell("Montant risqué", money(plan.risk_amount, currency),
                   f"{percent(plan.risk_pct, 2)} du capital", emph=True)]
    distance = number(plan.stop_distance, 5)
    detail = percent(plan.stop_distance_pct, 2) + " du prix d'entrée"
    if plan.stop_distance_pips is not None:
        detail = f"{number(plan.stop_distance_pips, 1)} pips · " + detail
    cells.append(_cell("Distance au stop", distance, detail))
    if plan.reward_to_risk is not None:
        cells.append(_cell("Ratio gain / risque", number(plan.reward_to_risk, 2),
                           f"gain prévu : {money(plan.planned_reward, currency)}"))
    if plan.position is not None:
        position = plan.position
        cells.append(_cell("Taille de position", f"{number(position.lots, 2)} lot",
                           f"calcul brut : {number(position.raw_lots, 4)} lot"))
        cells.append(_cell("Risque effectif", money(position.effective_risk, currency),
                           "après arrondi vers le bas"))
    html('<div class="ac-figures">' + "".join(cells) + "</div>")

    notes = list(plan.notes)
    if plan.position is None and spec is None:
        notes.insert(0, "Sans spécification d'instrument, la taille de position n'est pas "
                        "calculée : la valeur d'un mouvement de prix dépend du contrat.")
    html('<ul class="ac-sub" style="margin:.7rem 0 0;padding-left:1.1rem">'
         + "".join(f"<li>{esc(n)}</li>" for n in notes)
         + "<li>Un stop peut être exécuté au-delà de son niveau en cas de gap ou de marché rapide.</li>"
         "</ul>")


def _streaks(plan: R.RiskPlan, currency: str, k: str) -> None:
    html('<div class="ac-rule"></div><div class="ac-eyebrow">Séries de pertes</div>'
         '<h3 class="ac-h3" style="margin-top:.5rem">Ce que coûterait une série de pertes</h3>'
         f'<p class="ac-sub">Avec un risque de {percent(plan.risk_pct, 2)} du capital restant '
         'à chaque position, chaque perte touchant le stop.</p>')
    points = R.losing_streak(plan.equity, plan.risk_pct, 10)
    rows = "".join(
        f"<tr><td>{p.losses}</td><td>{money(p.equity, currency)}</td>"
        f"<td>−{percent(p.drawdown_pct)}</td><td>+{percent(p.recovery_pct)}</td></tr>"
        for p in points if p.losses in (1, 3, 5, 8, 10))
    html('<table><thead><tr><th>Pertes consécutives</th>'
         '<th>Capital restant</th><th>Baisse</th><th>Gain pour revenir</th></tr></thead>'
         f'<tbody>{rows}</tbody></table>')

    c1, c2 = st.columns(2)
    with c1:
        win = st.number_input("Taux de réussite supposé (%)", min_value=0.0, max_value=100.0,
                              value=50.0, step=5.0, format="%.0f", key=f"{k}_win")
    with c2:
        trades = st.number_input("Nombre de trades", min_value=1, max_value=2000, value=100,
                                 step=10, key=f"{k}_trades")
    cells = []
    for streak in (5, 8, 10):
        probability = R.streak_probability(int(trades), streak, win / 100)
        cells.append(_cell(f"Série de {streak} pertes ou plus", percent(probability * 100),
                           f"au moins une fois sur {int(trades)} trades"))
    html('<div class="ac-figures">' + "".join(cells) + "</div>")
    html('<p class="ac-note" style="margin-top:.7rem">Hypothèse : trades indépendants et taux '
         'de réussite constant. Dans la réalité, les pertes ont tendance à se regrouper, ce qui '
         'rend les longues séries plus probables encore.</p>')
