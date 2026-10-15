"""
Sensitor — the platform: Academy, Library, Trading Lab, Progression, and the
spaces in preparation, under one navigation and one account.

    streamlit run sensitor_app.py

Shares its accounts and database with the portfolio app
(`portfolio_optimizer_saas.py`): the same `SENSITOR_DB_URL` and `SENSITOR_AUTH`
secrets configure both. See docs/PLATFORM.md.
"""

from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sensitor.platform.brand import mark_svg  # noqa: E402

st.set_page_config(
    page_title="Sensitor",
    page_icon=mark_svg(64, uid="favicon"),
    layout="wide",
    initial_sidebar_state="auto",
)

from sensitor.platform.ui import runtime  # noqa: E402

runtime.mirror_secrets()

from sensitor.platform.ui.shell import main  # noqa: E402

main()
