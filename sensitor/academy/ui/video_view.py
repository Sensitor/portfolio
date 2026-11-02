"""
A video in a lesson (or a session's replay): a card first, the player only
when the reader asks for it.

Until the button is pressed, the page sends nothing to YouTube or Vimeo: no
request, no cookie from them. The transcript is always shown, below.
"""

from __future__ import annotations

import streamlit as st

from ...platform.ui.components import esc, html, md


def player(url: str, host: str, *, key: str, title: str = "", minutes: int | None = None) -> None:
    """The click-to-load player: a card, a button naming the host, then `st.video` once asked."""
    shown = f"video_on_{key}"
    length = f" · {minutes} min" if minutes else ""
    html(f'<div class="sx-c-blank"><div class="rub">Vidéo{length} · hébergée par {esc(host or "un service tiers")}'
         f'</div>' + (f"<h3>{esc(title)}</h3>" if title else "")
         + "<p>La vidéo se charge à votre demande : avant, aucune information n'est envoyée à "
         f"{esc(host or 'ce service')}.</p></div>")
    if st.session_state.get(shown):
        st.video(url)
    elif st.button(f"Lire la vidéo sur {host or 'le service tiers'}", key=f"video_btn_{key}"):
        st.session_state[shown] = True
        st.rerun()


def render(video, caption: str, *, key: str) -> None:
    player(video.url, video.host, key=key, title=video.title, minutes=video.duration_minutes)
    if caption:
        md(caption)
    with st.expander("Transcription"):
        md(video.transcript)
