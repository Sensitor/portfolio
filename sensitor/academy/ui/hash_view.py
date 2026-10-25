"""
The hash demonstration: what SHA-256 does to a text, and a toy proof of work.

Every figure comes from `academy.hashing`, computed in the reader's session on
what they type. Nothing is sent anywhere, and no key, address or seed phrase is
ever asked for: the demonstration works on plain sentences.
"""

from __future__ import annotations

import streamlit as st

from .. import hashing as H
from ...platform.ui.components import esc, html
from .risk_view import _cell


def _hex(value: str, zeros: int = 0) -> str:
    head, tail = value[:zeros], value[zeros:]
    return (f'<code class="sx-hash">{f"<b>{head}</b>" if head else ""}{esc(tail)}</code>')


def render(*, scope: str) -> None:
    k = f"hash_{scope}"
    with st.container(key=f"panel_{k}"):
        html('<div class="sx-kicker">Démonstration</div>'
             '<h2 class="sx-h3">Une empreinte, puis une preuve de travail</h2>'
             '<p class="sx-body">Tapez une phrase : son empreinte SHA-256 s\'affiche. Changez une seule '
             'lettre, l\'empreinte change entièrement. Le calcul se fait sur cette page, sur le texte que '
             'vous tapez ; aucune clé ni phrase de récupération n\'est jamais demandée.</p>')
        text = st.text_input("Texte", value="Alice paie 1 BTC à Bob", max_chars=200, key=f"{k}_text")
        html(f'<div class="sx-kicker muted" style="margin:.4rem 0 .3rem">Empreinte SHA-256</div>{_hex(H.digest(text))}')

        html('<div class="sx-kicker muted" style="margin:1.4rem 0 .3rem">Preuve de travail, version jouet</div>'
             '<p class="sx-body">Trouver un nombre, le nonce, qui ajouté au texte donne une empreinte '
             'commençant par un nombre de zéros donné. Chaque zéro de plus multiplie le travail moyen par 16.</p>')
        with st.container(key=f"inline_{k}"):
            zeros = st.radio("Zéros exigés en tête de l'empreinte", options=list(range(1, H.MAX_ZEROS + 1)),
                             index=2, horizontal=True, key=f"{k}_zeros")
        if st.button("Chercher le nonce", key=f"{k}_mine", type="primary"):
            st.session_state[f"{k}_result"] = (text, zeros, H.mine(text, zeros))
        result = st.session_state.get(f"{k}_result")
        if result and result[0] == text and result[1] == zeros and result[2]:
            mined = result[2]
            html('<div class="sx-figures three">'
                 + _cell("Nonce trouvé", f"{mined.nonce:,}".replace(",", " "), "ajouté à la fin du texte", emph=True)
                 + _cell("Essais", f"{mined.tries:,}".replace(",", " "),
                         f"en moyenne : {H.expected_tries(zeros):,}".replace(",", " "))
                 + _cell("Vérification", "1 calcul", "pour quiconque veut contrôler")
                 + '</div>')
            html(f'<div style="margin-top:.6rem">{_hex(mined.digest, zeros)}</div>')
        elif result:
            html('<p class="sx-note">Le texte ou la difficulté ont changé : relancez la recherche.</p>')
        html('<p class="sx-note">Trouver le nonce demande des milliers d\'essais ; vérifier qu\'il convient '
             'n\'en demande qu\'un. C\'est l\'asymétrie qui fait la preuve de travail. Le réseau Bitcoin '
             'demandait en octobre 2026 environ 6 × 10<sup>23</sup> essais en moyenne par bloc.</p>')
