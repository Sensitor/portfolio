"""
One account for every Sensitor space — sign in, sign up, sign out.

Uses the existing `Auth` service unchanged: the same credentials work in the
portfolio application. Error reasons are stable keys from `Auth`, translated
here.
"""

from __future__ import annotations

import streamlit as st

from ...core.security import MIN_PASSWORD_LENGTH
from . import runtime as rt
from .components import crumbs, esc, footer, html, note, page_header, section

REASONS = {
    "invalid_email": "Adresse e-mail invalide.",
    "invalid_credentials": "Adresse ou mot de passe incorrect.",
    "already_registered": "Un compte existe déjà avec cette adresse. Connectez-vous.",
    "weak_password": "Mot de passe trop faible.",
    "locked": "Trop de tentatives. Réessayez dans quelques minutes.",
}

BENEFITS = (
    ("Toutes les leçons publiées", "Les leçons réservées aux membres, au-delà des deux leçons en accès libre."),
    ("Une progression enregistrée", "Leçons terminées, quiz et erreurs à revoir, retrouvés à chaque visite."),
    ("Un compte pour tous les espaces", "Le même compte servira à chaque espace Sensitor à son ouverture."),
)


def render(catalog, email, route) -> None:
    crumbs("Sensitor", "Compte")
    if email:
        page_header("Compte · Membre", "Votre <em>compte</em>",
                    "Un seul compte pour tous les espaces Sensitor.")
        html(f'<div class="sx-facts" style="max-width:620px;margin-top:1.6rem">'
             f'<div><dt>Adresse</dt><dd>{esc(email)}</dd></div>'
             f'<div><dt>Accès</dt><dd>Toutes les leçons publiées</dd></div>'
             f'<div><dt>Abonnement</dt><dd>Aucun — accès membre gratuit</dd></div></div>')
        if not rt.multi_user():
            st.warning("Cette installation fonctionne en mode local (SENSITOR_AUTH n'est pas réglé "
                       "sur « multi ») : l'adresse sert d'identifiant sans mot de passe. Ce mode "
                       "convient à un usage personnel, pas à un site ouvert.")
        if st.button("Se déconnecter", key="sign_out"):
            rt.sign_out()
            rt.go("home")
            st.rerun()
        footer()
        return

    page_header("Compte", "Rejoindre <em>Sensitor</em>",
                "Un compte gratuit ouvre toutes les leçons publiées et enregistre votre "
                "progression. Aucun moyen de paiement n'est demandé.")
    if rt.get_store() is None:
        st.error("La base de données est indisponible : la connexion est impossible pour l'instant.")
        return
    multi = rt.multi_user()
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        tab_in, tab_up = st.tabs(["Se connecter", "Créer un compte"])
        with tab_in:
            with st.form("sign_in_form"):
                address = st.text_input("Adresse e-mail", key="si_email")
                password = (st.text_input("Mot de passe", type="password", key="si_pw")
                            if multi else None)
                if st.form_submit_button("Se connecter", type="primary"):
                    _finish(rt.sign_in(address, password))
        with tab_up:
            with st.form("sign_up_form"):
                address = st.text_input("Adresse e-mail", key="su_email")
                password = (st.text_input(f"Mot de passe ({MIN_PASSWORD_LENGTH} caractères minimum)",
                                          type="password", key="su_pw") if multi else None)
                if st.form_submit_button("Créer mon compte", type="primary"):
                    _finish(rt.sign_up(address, password))
        if not multi:
            note("Mode local : aucun mot de passe n'est demandé. Pour un site ouvert au public, "
                 "réglez SENSITOR_AUTH=multi.")
    with right:
        rows = "".join(f'<div><span class="n">{i:02d}</span><span class="x"><b>{esc(t)}</b><br>'
                       f'<span style="color:var(--muted);font-size:14px">{esc(x)}</span></span></div>'
                       for i, (t, x) in enumerate(BENEFITS, start=1))
        html(f'<div class="sx-kicker muted" style="margin-bottom:.4rem">Ce que donne un compte</div>'
             f'<div class="sx-objectives single">{rows}</div>')
    footer()


def _finish(result) -> None:
    if result:
        rt.go("home")
        st.rerun()
    reason = getattr(result, "reason", None)
    message = REASONS.get(reason, "La connexion a échoué.")
    if reason == "weak_password":
        detail = getattr(result, "detail", None) or ""
        message += (" Il ne doit pas commencer ni finir par une espace." if "space" in detail
                    else f" Il doit compter au moins {MIN_PASSWORD_LENGTH} caractères.")
    st.error(message)
