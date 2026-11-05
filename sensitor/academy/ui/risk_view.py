"""
The risk calculator, used on the lab page and inside the risk lesson.

Every figure on screen comes from `academy.risk`. Position size is shown only
when a contract specification is given. Two presets, each on a dollar account
and each saying the convention it rests on: gold (XAUUSD, 1 lot = 100 ounces, so
a 1 $ move is worth 100 $ per lot), the lab's example, and EURUSD (standard lot
of 100 000 units, 1 pip = 0,0001 worth 10 $ per lot), the risk lesson's. The
custom mode asks for the broker's own figures. Nothing is assumed about indices
or shares.
"""

from __future__ import annotations

import streamlit as st

from .. import risk as R
from ...platform.ui.components import esc, html, money, number, percent

CURRENCIES = ("USD", "EUR", "GBP", "CHF")
SPEC_NONE = "Ne pas calculer la taille"
SPEC_GOLD = "Or (XAUUSD) sur un compte en USD (1 lot = 100 onces)"
SPEC_EURUSD = "EURUSD sur un compte en USD (lot standard)"
SPEC_CUSTOM = "Saisir la spécification de mon courtier"
MODES = (SPEC_NONE, SPEC_GOLD, SPEC_EURUSD, SPEC_CUSTOM)

# The example each preset opens with: constructed figures, not quotes. Gold: a
# 10 $ stop for a 1 % risk on 10 000 $, i.e. 0,10 lot; EURUSD: the risk
# lesson's 30-pip stop, i.e. 0,33 lot.
EXAMPLES = {
    "gold": {"entry": 2400.00, "stop": 2390.00, "target": 2420.00, "step": 0.01, "format": "%.2f", "decimals": 2, "unit": " $"},
    "eurusd": {"entry": 1.0850, "stop": 1.0820, "target": 1.0910, "step": 0.0001, "format": "%.5f", "decimals": 5, "unit": ""},
}
MODE_EXAMPLE = {SPEC_GOLD: "gold", SPEC_EURUSD: "eurusd"}
DEFAULT_MODE = {"gold": SPEC_GOLD, "eurusd": SPEC_EURUSD}


def render(*, scope: str, compact: bool = False, instrument: str = "eurusd") -> None:
    """`instrument`: the preset the calculator opens on, « gold » (the lab) or « eurusd » (the lesson)."""
    k = f"risk_{scope}"
    with st.container(key=f"panel_{k}"):
        html('<div class="sx-kicker">Calculateur pédagogique</div>'
             '<h2 class="sx-h3">Budget de risque et taille de position</h2>'
             '<p class="sx-body">Estimation éducative. Elle ne remplace pas le calcul de votre '
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

        mode = st.radio("Instrument et taille de position", MODES,
                        index=MODES.index(DEFAULT_MODE.get(instrument, SPEC_EURUSD)), key=f"{k}_mode")
        # Prices keep their own fields per instrument, so gold opens on gold prices
        # and EURUSD on EURUSD ones, each with its own number of decimals.
        family = MODE_EXAMPLE.get(mode, instrument if instrument in EXAMPLES else "eurusd")
        example = EXAMPLES[family]
        with st.container(key=f"inline_{k}_dir"):
            direction = st.radio("Sens", ["Achat", "Vente"], horizontal=True, key=f"{k}_dir")
        c1, c2, c3 = st.columns(3)
        with c1:
            entry = st.number_input("Prix d'entrée", min_value=0.0, value=example["entry"], step=example["step"],
                                    format=example["format"], key=f"{k}_entry_{family}")
        with c2:
            stop = st.number_input("Stop-loss", min_value=0.0, value=example["stop"], step=example["step"],
                                   format=example["format"], key=f"{k}_stop_{family}")
        with c3:
            target_raw = st.number_input("Objectif (facultatif, 0 = aucun)", min_value=0.0,
                                         value=example["target"], step=example["step"], format=example["format"],
                                         key=f"{k}_target_{family}")
        target = target_raw or None
        if mode in MODE_EXAMPLE:
            html('<p class="sx-note">Prix d\'exemple, construits pour le calcul : remplacez-les par ceux de '
                 'votre trade.</p>')
        spec = _spec(mode, k, currency)

        try:
            plan = R.plan(equity=equity, risk_pct=risk_pct, entry=entry, stop=stop,
                          direction=R.LONG if direction == "Achat" else R.SHORT,
                          target=target, spec=spec)
        except R.RiskInputError as exc:
            for message in exc.errors.values():
                st.error(message)
            return

        _figures(plan, currency, spec, decimals=example["decimals"],
                 unit=example["unit"] if mode in MODE_EXAMPLE else "")
        if not compact:
            _streaks(plan, currency, k)


def _spec(mode: str, k: str, currency: str) -> R.InstrumentSpec | None:
    if mode == SPEC_NONE:
        return None
    if mode == SPEC_GOLD:
        if currency != "USD":
            st.warning("Ce préréglage suppose un compte en dollars : l'or est coté en dollars, et un "
                       "mouvement de 1 $ ne vaut 100 $ par lot que sur un compte en USD. Choisissez « USD » "
                       "ou saisissez la spécification de votre courtier.")
            return None
        html('<p class="sx-note">Convention la plus courante pour l\'or (XAUUSD) : 1 lot = 100 onces, '
             'donc un mouvement de 1 $ du prix vaut 100 $ par lot (0,01 lot : 1 $). Pas de volume de '
             '0,01 lot. Certains courtiers ont un autre contrat (10 onces, 1 once) : vérifiez la « taille '
             'du contrat » dans la spécification de l\'instrument sur MetaTrader 5.</p>')
        return R.InstrumentSpec(contract_size=100, quote_to_account=1.0, lot_step=0.01,
                                min_lot=0.01, pip_size=None, label="XAUUSD · USD")
    if mode == SPEC_EURUSD:
        if currency != "USD":
            st.warning("Ce préréglage suppose un compte en dollars : la valeur d'un pip "
                       "d'EURUSD n'est de 10 $ par lot que dans ce cas. Choisissez « USD » "
                       "ou saisissez la spécification de votre courtier.")
            return None
        html('<p class="sx-note">Convention du marché des changes : 1 lot = 100 000 unités, '
             '1 pip = 0,0001, pas de volume de 0,01 lot. Vérifiez la spécification de votre '
             'courtier, qui peut différer.</p>')
        return R.InstrumentSpec(contract_size=100_000, quote_to_account=1.0, lot_step=0.01,
                                min_lot=0.01, pip_size=0.0001, label="EURUSD · USD")
    html('<p class="sx-note">Recopiez les valeurs de la fiche de l\'instrument chez votre '
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
        html('<p class="sx-note">Indiquez le nombre d\'unités par lot pour calculer la taille.</p>')
        return None
    return R.InstrumentSpec(contract_size=contract, quote_to_account=rate,
                            lot_step=step or None, min_lot=step or None, pip_size=pip or None)


def _cell(label: str, value: str, detail: str = "", emph: bool = False) -> str:
    detail_html = f'<div class="d">{detail}</div>' if detail else ""
    return (f'<div{" class=emph" if emph else ""}><div class="l">{esc(label)}'
            f'</div><div class="v">{value}</div>{detail_html}</div>')


def _figures(plan: R.RiskPlan, currency: str, spec: R.InstrumentSpec | None, *, decimals: int = 5,
             unit: str = "") -> None:
    cells = [_cell("Montant risqué", money(plan.risk_amount, currency),
                   f"{percent(plan.risk_pct, 2)} du capital", emph=True)]
    distance = number(plan.stop_distance, decimals) + unit
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
    html('<div class="sx-figures">' + "".join(cells) + "</div>")

    notes = list(plan.notes)
    if plan.position is None and spec is None:
        notes.insert(0, "Sans spécification d'instrument, la taille de position n'est pas "
                        "calculée : la valeur d'un mouvement de prix dépend du contrat.")
    html('<ul class="sx-body" style="margin:.8rem 0 0;padding-left:1.1rem;font-size:14px">'
         + "".join(f"<li>{esc(n)}</li>" for n in notes)
         + "<li>Un stop peut être exécuté au-delà de son niveau en cas de gap ou de marché rapide.</li>"
         "</ul>")


def _streaks(plan: R.RiskPlan, currency: str, k: str) -> None:
    html('<hr class="sx-hr"><div class="sx-kicker">Séries de pertes</div>'
         '<h2 class="sx-h3">Ce que coûterait une série de pertes</h2>'
         f'<p class="sx-body">Avec un risque de {percent(plan.risk_pct, 2)} du capital restant '
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
    html('<div class="sx-figures">' + "".join(cells) + "</div>")
    html('<p class="sx-note" style="margin-top:.7rem">Hypothèse : trades indépendants et taux '
         'de réussite constant. Dans la réalité, les pertes ont tendance à se regrouper, ce qui '
         'rend les longues séries plus probables encore.</p>')


def render_ruin(*, scope: str) -> None:
    """Expectancy, break-even, risk of ruin and final-equity range for given assumptions."""
    from .. import expectancy as E

    k = f"ruin_{scope}"
    with st.container(key=f"panel_{k}"):
        html('<div class="sx-kicker">Simulateur pédagogique</div>'
             '<h2 class="sx-h3">Espérance et risque de ruine</h2>'
             '<p class="sx-body">Calcul exact sous trois hypothèses : trades indépendants, taux de '
             'réussite et ratio constants, risque en pourcentage du capital restant. Ce ne sont pas '
             'des prévisions.</p>')
        c1, c2, c3 = st.columns(3)
        with c1:
            win = st.number_input("Taux de réussite (%)", min_value=1.0, max_value=99.0, value=45.0,
                                  step=1.0, format="%.0f", key=f"{k}_win")
        with c2:
            reward = st.number_input("Gain moyen (R)", min_value=0.1, max_value=10.0, value=1.5,
                                     step=0.1, format="%.1f", key=f"{k}_reward")
        with c3:
            risk_pct = st.number_input("Risque par trade (%)", min_value=0.1, max_value=20.0,
                                       value=1.0, step=0.25, format="%.2f", key=f"{k}_risk")
        c1, c2 = st.columns(2)
        with c1:
            trades = st.number_input("Nombre de trades", min_value=10, max_value=500, value=200,
                                     step=10, key=f"{k}_trades")
        with c2:
            threshold = st.number_input("Seuil de perte depuis le départ (%)", min_value=5.0,
                                        max_value=90.0, value=20.0, step=5.0, format="%.0f",
                                        key=f"{k}_threshold")

        p = win / 100
        exp = E.expectancy_r(p, reward)
        breakeven = E.breakeven_win_rate(reward)
        ruin = E.ruin_probability(p, reward, risk_pct, int(trades), threshold)
        q = E.final_equity_quantiles(p, reward, risk_pct, int(trades))
        sign = "+" if exp > 0 else ""
        cells = [
            _cell("Espérance par trade", f"{sign}{number(exp, 3)} R",
                  "positive" if exp > 0 else "nulle" if abs(exp) < 1e-9 else "négative", emph=True),
            _cell("Seuil de rentabilité", percent(breakeven * 100), f"pour des gains de {number(reward, 1)}R"),
            _cell("Profit factor", number(E.profit_factor(p, reward), 2), "gains ÷ pertes"),
            _cell(f"Perdre {number(threshold, 0)} % au moins une fois",
                  "< 0,1 %" if ruin < 0.001 else percent(ruin * 100), f"sur {int(trades)} trades"),
        ]
        html('<div class="sx-figures four">' + "".join(cells) + "</div>")
        html('<div class="sx-kicker muted" style="margin-top:1.2rem">Capital final, pour 100 au départ</div>')
        html('<div class="sx-figures three">'
             + _cell("Scénario défavorable (5 %)", number(q[0.05], 1), "5 % des cas finissent plus bas")
             + _cell("Médiane", number(q[0.5], 1), "la moitié des cas finit plus bas")
             + _cell("Scénario favorable (95 %)", number(q[0.95], 1), "5 % des cas finissent plus haut")
             + "</div>")
        html('<p class="sx-note" style="margin-top:.8rem">Le seuil se mesure depuis le capital de '
             'départ ; mesuré depuis un sommet, il serait atteint plus souvent. Les résultats réels se '
             'regroupent en séries, ce qui rend en général la réalité moins favorable que ces chiffres.</p>')
