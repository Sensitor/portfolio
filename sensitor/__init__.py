"""
Sensitor Portfolio Intelligence
===============================

Premium fintech analytics layer built on top of the existing Portfolio Health Pro
engine. Organised as:

    design.py      Design tokens, CSS theme, Plotly template, html() helper
    components.py  Visual components (metric cards, gauges, bars, alerts, tooltips)
    charts.py      Themed Plotly chart factories
    analytics.py   Pure computation (no Streamlit): performance, risk, benchmark
    xray.py        Look-through exposure reference data + computation
    pages/         Page renderers (overview, health, performance, risk, xray)

Nothing in `analytics.py` or `xray.py` imports Streamlit, so the maths is testable
in isolation and reusable outside the app (reports, API, batch jobs).
"""

__version__ = "5.0.0"
__product__ = "Sensitor Portfolio Intelligence"
