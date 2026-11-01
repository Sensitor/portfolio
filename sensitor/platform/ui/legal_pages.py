"""
The three legal pages (`platform.legal`), linked from the footer of every page.
"""

from __future__ import annotations

import streamlit as st

from .. import legal
from .components import crumbs, esc, footer, notice, page_header


def _page(page: str):
    def renderer(catalog, email, route) -> None:
        doc = legal.document(page)
        crumbs("Sensitor", doc.title)
        page_header("Informations légales", esc(doc.title), esc(doc.summary))
        if doc.missing or not doc.reviewed:
            notice("Texte en cours de finalisation",
                   ("Certaines informations de l'éditeur restent à compléter. " if doc.missing else "")
                   + ("Ce texte n'a pas encore été relu par un juriste." if not doc.reviewed else ""), "info")
        with st.container(key=f"legal_{page}"):
            st.markdown(doc.body)
        footer()
    renderer.__name__ = f"render_{page}"
    return renderer


RENDERERS = {page: _page(page) for page in legal.PAGES}
