"""
The savings simulator: nominal and real value of a savings plan.

Every figure comes from `academy.savings`. The rates are held constant and the
panel says so: the simulator shows how compounding, fees, taxes and inflation
interact, not what a real account will hold.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from .. import savings as S
from ...platform.ui.components import html, money, percent
from ...platform.ui.theme import TOKENS
from .chart_view import FONT, style
from .risk_view import _cell


def figure(rows: list[S.Year]) -> go.Figure:
    years = [r.year for r in rows]
    fig = go.Figure()
    for label, values, color, dash in (
            ("Valeur affichée (nominale)", [r.nominal for r in rows], TOKENS["copper-2"], "solid"),
            ("Pouvoir d'achat (réel, en euros de départ)", [r.real for r in rows], TOKENS["blue"], "solid"),
            ("Sommes versées", [r.contributed for r in rows], TOKENS["muted"], "dot")):
        fig.add_trace(go.Scatter(x=years, y=values, name=label, mode="lines",
                                 line=dict(color=color, width=2.4 if dash == "solid" else 1.6, dash=dash),
                                 hovertemplate="%{y:,.0f} €<extra>" + label + "</extra>"))
    style(fig, x_label="Années", y_label="Euros", numeric_x=True, height=360)
    fig.update_layout(hoverlabel=dict(font=dict(family=FONT)))
    return fig


def render(*, scope: str) -> None:
    k = f"savings_{scope}"
    with st.container(key=f"panel_{k}"):
        html('<div class="sx-kicker">Simulateur pédagogique</div>'
             '<h2 class="sx-h3">Valeur nominale et valeur réelle d\'une épargne</h2>'
             '<p class="sx-body">Calcul mensuel, à taux constants : une hypothèse que la réalité ne '
             'respecte jamais. Il montre comment se combinent les intérêts composés, les frais, l\'impôt et '
             'l\'inflation ; il ne prévoit pas ce que contiendra un compte réel.</p>')
        c1, c2, c3 = st.columns(3)
        with c1:
            initial = st.number_input("Capital de départ (€)", min_value=0.0, max_value=10_000_000.0,
                                      value=10_000.0, step=1_000.0, format="%.0f", key=f"{k}_initial")
        with c2:
            monthly = st.number_input("Versement mensuel (€)", min_value=0.0, max_value=100_000.0,
                                      value=200.0, step=50.0, format="%.0f", key=f"{k}_monthly")
        with c3:
            years = st.number_input("Durée (années)", min_value=1, max_value=60, value=30, step=1,
                                    key=f"{k}_years")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            rate = st.number_input("Rendement nominal (% par an)", min_value=-50.0, max_value=50.0,
                                   value=5.0, step=0.5, format="%.1f", key=f"{k}_rate")
        with c2:
            infl = st.number_input("Inflation (% par an)", min_value=-10.0, max_value=50.0, value=2.0,
                                   step=0.5, format="%.1f", key=f"{k}_infl")
        with c3:
            fee = st.number_input("Frais (% par an)", min_value=0.0, max_value=10.0, value=0.0,
                                  step=0.25, format="%.2f", key=f"{k}_fee")
        with c4:
            tax = st.number_input("Impôt sur les gains (%)", min_value=0.0, max_value=90.0, value=0.0,
                                  step=5.0, format="%.0f", key=f"{k}_tax")

        rows = S.project(initial, int(years), rate / 100, infl / 100, monthly_contribution=monthly,
                         annual_fee=fee / 100, tax_on_gains=tax / 100)
        end = rows[-1]
        real = S.real_rate(rate / 100, infl / 100)
        html('<div class="sx-figures four">'
             + _cell("Valeur affichée", money(end.nominal, "EUR", 0), f"après {int(years)} ans", emph=True)
             + _cell("Pouvoir d'achat", money(end.real, "EUR", 0), "en euros d'aujourd'hui")
             + _cell("Sommes versées", money(end.contributed, "EUR", 0),
                     "gain réel : " + money(end.real - end.contributed, "EUR", 0))
             + _cell("Frais payés", money(end.fees, "EUR", 0),
                     f"rendement réel avant frais : {percent(real * 100, 2)}")
             + "</div>")
        st.plotly_chart(figure(rows), key=f"plot_{k}", theme=None,
                        config={"displayModeBar": False, "responsive": True})
        html('<p class="sx-note">Le pouvoir d\'achat divise la valeur affichée par la hausse des prix '
             'accumulée. Si la courbe dorée passe sous les sommes versées, l\'épargne a perdu en réel '
             'même si elle a gagné en euros. Ni les rendements ni l\'inflation ne sont constants en '
             'réalité ; aucun résultat de ce simulateur n\'est un conseil en investissement.</p>')
