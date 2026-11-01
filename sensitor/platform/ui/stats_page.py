"""
The administrator's statistics: the funnel from a visit to an accompanied
member, where accounts come from, and the audience, counted without cookies.

Counts only, read by `Store.admin_stats`, which checks the role; the rates are
`platform.stats`. No address is shown on this page.
"""

from __future__ import annotations

import datetime as _dt

import plotly.graph_objects as go
import streamlit as st

from .. import stats as S
from . import runtime as rt
from . import trade_visuals as V
from .components import crumbs, esc, footer, html, note, notice, page_header, section

WINDOWS = {7: "7 derniers jours", 30: "30 derniers jours", 90: "90 derniers jours", 365: "12 derniers mois"}
MONTHS = ("janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc.")


def _month_label(month: str) -> str:
    year, number = month.split("-")
    return f"{MONTHS[int(number) - 1]} {year}"


def _number(value: int) -> str:
    return f"{int(value):,}".replace(",", " ")


def render(catalog, email, route) -> None:
    crumbs("Sensitor", "Gestion", "Statistiques")
    page_header("Gestion · réservé aux administrateurs", "D'où viennent <em>les membres</em>.",
                "Des comptes, jamais des personnes : aucune adresse sur cette page, aucun cookie de mesure.")
    store = rt.get_store()
    if store is None or not rt.can(email, "admin.stats"):
        notice("Accès réservé", "Cette page est réservée aux administrateurs de Sensitor.", "lock")
        footer()
        return
    days = st.selectbox("Période", list(WINDOWS), index=1, format_func=WINDOWS.get, key="stats_window")
    since = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=days)).isoformat(timespec="seconds")
    data = store.admin_stats(email, since=since) or {}
    total = data.get("total", {})

    html('<dl class="sx-facts" style="max-width:720px;margin-top:1.2rem">'
         f'<div><dt>Membres</dt><dd>{_number(total.get("members", 0))}</dd></div>'
         f'<div><dt>Premium actifs</dt><dd>{_number(total.get("premium", 0))}</dd></div>'
         f'<div><dt>Accompagnés</dt><dd>{_number(total.get("accompanied", 0))}</dd></div>'
         f'<div><dt>Connectés sur la période</dt><dd>{_number(total.get("active_30", 0))}</dd></div>'
         f'<div><dt>Inscrits à la lettre</dt><dd>{_number(total.get("newsletter", 0))}</dd></div></dl>')

    section(1, "L'entonnoir", f"{WINDOWS[days]} : les visites, puis ce que sont devenus les comptes créés.")
    steps = S.funnel(data.get("visits", 0), data.get("signups", 0), data.get("verified", 0),
                     data.get("premium", 0), data.get("accompanied", 0))
    st.dataframe([{"Étape": s.label, "Nombre": s.count,
                   "Taux": "" if not s.base else f"{S.percent(s.rate)} {s.base}" if s.rate is not None else "n/a"}
                  for s in steps], hide_index=True, width="stretch", key="stats_funnel")
    note("Une visite est comptée une fois par session de navigation sur la plateforme. Le site public n'a pas de "
         "mesure : les comptes qu'il amène apparaissent sous la source « site ».")

    section(2, "Comptes créés par mois", "Les douze derniers mois où un compte a été créé.")
    months = list(reversed(data.get("by_month", [])))
    if months:
        K = V.K
        fig = go.Figure(go.Bar(x=[_month_label(m["month"]) for m in months], y=[m["n"] for m in months],
                               marker=dict(color=K.get("plan", "#1f4a72")),
                               hovertemplate="%{x} : %{y} compte(s)<extra></extra>"))
        fig.update_layout(height=260, margin=dict(l=44, r=16, t=18, b=10), paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", showlegend=False, bargap=0.35,
                          font=dict(family="Schibsted Grotesk, DM Sans, sans-serif", color=K.get("ink-2", "#18293a")))
        fig.update_yaxes(gridcolor=K.get("rule", "#ddd8cb"), rangemode="tozero", tickformat="d", automargin=True)
        fig.update_xaxes(showgrid=False, type="category", automargin=True)
        with st.container(key="chart_stats_months"):
            st.plotly_chart(fig, key="plot_stats_months", theme=None,
                            config={"displayModeBar": False, "responsive": True})
    else:
        note("Aucun compte pour l'instant.")

    section(3, "D'où viennent les comptes", f"{WINDOWS[days]}, par source de campagne (utm_source).")
    sources = data.get("by_source", [])
    if sources:
        st.dataframe([{"Source": s["source"], "Comptes": s["n"],
                       "Part": S.percent(S.rate(s["n"], data.get("signups", 0)))} for s in sources],
                     hide_index=True, width="stretch", key="stats_sources")
    else:
        note("Aucun compte créé sur la période.")
    html('<p class="sx-note">Pour suivre une campagne, ajoutez ses étiquettes au lien : '
         f'<code>{esc("?utm_source=instagram&utm_campaign=lancement")}</code>.</p>')

    section(4, "Les pages d'arrivée", f"{WINDOWS[days]}, les plus visitées.")
    landings = data.get("visits_by_landing", [])
    if landings:
        st.dataframe([{"Page": l["landing"], "Visites": l["n"]} for l in landings], hide_index=True,
                     width="stretch", key="stats_landings")
    else:
        note("Aucune visite comptée sur la période.")
    footer()
