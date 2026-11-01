"""
The newsletter's three pages: subscribe (for anyone, linked from the public
site), confirm (the e-mailed link, then a button), and stop (one click, from any
message). The logic is `platform.newsletter`.
"""

from __future__ import annotations

import streamlit as st

from .. import newsletter as N
from . import runtime as rt
from .components import crumbs, footer, note, notice, page_header

OUTCOMES = {
    "sent": ("success", "C'est presque fait : un e-mail de confirmation vient de partir. Ouvrez le lien qu'il "
                        f"contient dans les {N.CONFIRM_HOURS} heures pour activer l'inscription."),
    "throttled": ("success", "C'est presque fait : un e-mail de confirmation vient de partir. Ouvrez le lien qu'il "
                             f"contient dans les {N.CONFIRM_HOURS} heures pour activer l'inscription."),
    "confirmed": ("info", "Cette adresse est déjà inscrite à la lettre."),
    "no_consent": ("error", "Cochez la case de consentement pour vous inscrire."),
    "invalid_email": ("error", "Adresse e-mail invalide."),
    "no_mail": ("error", "L'inscription ouvrira dès que l'envoi d'e-mails sera configuré sur ce déploiement."),
    "mail_failed": ("error", "L'e-mail de confirmation n'a pas pu partir. Réessayez dans quelques minutes."),
}


def show(outcome: str) -> None:
    kind, text = OUTCOMES.get(outcome, ("error", "L'inscription a échoué."))
    getattr(st, kind)(text)


def form(key: str, *, email: str | None = None, source: str = "site") -> None:
    """The subscription form: an address (prefilled for a member) and the consent box."""
    store = rt.get_store()
    with st.form(key):
        address = email or st.text_input("Adresse e-mail", key=f"{key}_email")
        if email:
            note(f"Inscription pour {email}.")
        consented = st.checkbox(N.CONSENT_TEXT, key=f"{key}_consent")
        if st.form_submit_button("M'inscrire", type="primary"):
            if store is None:
                st.error("La base de données est indisponible pour l'instant.")
            else:
                show(N.request(store, address, source=source, consented=consented))


def subscribe_page(catalog, email, route) -> None:
    crumbs("Sensitor", "Lettre")
    page_header("La lettre de Sensitor", "Recevoir <em>la lettre</em>.",
                "Les nouveaux articles, les analyses pédagogiques et les nouveautés de la plateforme. "
                "Jamais de signal, jamais de recommandation d'achat ou de vente.")
    form("newsletter_form", email=email, source="account" if email else "site")
    note("Votre adresse sert uniquement à vous envoyer la lettre. Le détail est dans la politique de "
         "confidentialité, liée en bas de page.")
    footer()


def confirm_page(catalog, email, route) -> None:
    crumbs("Sensitor", "Lettre", "Confirmation")
    page_header("La lettre de Sensitor", "Confirmer <em>l'inscription</em>.", "")
    token = route.get("token", "")
    store = rt.get_store()
    if not token or store is None:
        notice("Lien incomplet", "Ce lien de confirmation est incomplet.", "info")
    elif st.button("Confirmer mon inscription", type="primary", key="newsletter_confirm_button"):
        if N.confirm(store, token):
            st.success("Inscription confirmée. Chaque lettre contiendra un lien pour vous désinscrire en un clic.")
        else:
            st.error("Ce lien n'est plus valable : il a déjà servi ou il a expiré. Vous pouvez vous inscrire à nouveau.")
    footer()


def stop_page(catalog, email, route) -> None:
    crumbs("Sensitor", "Lettre", "Désinscription")
    page_header("La lettre de Sensitor", "Désinscription.", "")
    token = route.get("token", "")
    store = rt.get_store()
    done = bool(token and store is not None and N.stop(store, token))
    if done:
        st.success("Vous êtes désinscrit : vous ne recevrez plus la lettre.")
    else:
        notice("Lien non reconnu", "Ce lien de désinscription n'est pas reconnu. Depuis votre compte, la page "
               "« Compte » permet aussi de vous désinscrire.", "info")
    footer()


RENDERERS = {"newsletter": subscribe_page, "newsletter_confirm": confirm_page, "newsletter_stop": stop_page}
