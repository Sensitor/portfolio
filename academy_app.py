"""
Sensitor Academy — the education app.

    streamlit run academy_app.py

A separate entry point from the portfolio app (`portfolio_optimizer_saas.py`),
sharing its accounts and database: the same `SENSITOR_DB_URL` and
`SENSITOR_AUTH` secrets configure both. See docs/ACADEMY.md.
"""

from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sensitor.academy.ui.brand import logo_svg  # noqa: E402

st.set_page_config(
    page_title="Sensitor Academy",
    page_icon=logo_svg(64, uid="favicon"),
    layout="wide",
    initial_sidebar_state="auto",
)

from sensitor.academy.ui import runtime  # noqa: E402

runtime.mirror_secrets()

from sensitor.academy.ui.app import main  # noqa: E402

main()
