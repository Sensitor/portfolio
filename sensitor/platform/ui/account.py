"""
One account for every Sensitor space.

Sign in and sign up; password reset and address verification by e-mailed
single-use links; for a signed-in member: the access level, a display name, the
newsletter, password change, sign-out on every device, export of everything
stored, and deletion of the account, confirmed by the password.

Uses the existing `Auth` service: the same credentials work in the portfolio
application. Error reasons are stable keys from `Auth`, translated here.
Requests for a reset link never reveal whether an address has an account.
"""

from __future__ import annotations

import json

import streamlit as st

from ...core import mailer
from ...core import permissions as P
from ...core.security import MIN_PASSWORD_LENGTH
from ...database.connection import now as _now
from .. import newsletter as N
from . import newsletter_pages
from . import runtime as rt
from .components import crumbs, date_fr, esc, footer, html, note, notice, page_header, section

REASONS = {
    "invalid_email": "Adresse e-mail invalide.",
    "invalid_credentials": "Adresse ou mot de passe incorrect.",
    "already_registered": "Un compte existe déjà avec cette adresse. Connectez-vous, ou utilisez "
                          "« Mot de passe oublié » si vous n'avez pas encore de mot de passe.",
    "weak_password": "Mot de passe trop faible.",
    "locked": "Trop de tentatives. Réessayez dans quelques minutes.",
    "invalid_token": "Ce lien n'est plus valable : il a déjà servi ou il a expiré.",
    "not_multi_user": "Le changement de mot de passe n'existe qu'en mode multi-utilisateur.",
}

BENEFITS = (
    ("Toutes les leçons publiées", "Les leçons réservées aux membres, au-delà de celles en accès libre."),
    ("Une progression enregistrée", "Leçons terminées, quiz et erreurs à revoir, retrouvés à chaque visite."),
    ("Un compte pour tous les espaces", "Le même compte servira à chaque espace Sensitor à son ouverture."),
)


def _message(result) -> str:
    reason = getattr(result, "reason", None)
    message = REASONS.get(reason, "L'opération a échoué.")
    if reason == "weak_password":
        detail = getattr(result, "detail", None) or ""
        message += (" Il ne doit pas commencer ni finir par une espace." if "space" in detail
                    else f" Il doit compter au moins {MIN_PASSWORD_LENGTH} caractères.")
    return message


def _send_verification(email: str) -> bool:
    """Send a verification link if e-mail is configured. True when sent."""
    auth = rt.get_auth()
    if auth is None or not mailer.configured():
        return False
    token = auth.request_verification(email)
    if not token:
        return False
    try:
        mailer.send(email, "Confirmez votre adresse Sensitor",
                    mailer.verify_body(mailer.link("verify", token)))
    except mailer.MailError:
        return False
    return True


# =============================================================================
# Account page
# =============================================================================

def render(catalog, email, route) -> None:
    crumbs("Sensitor", "Compte")
    if email:
        _member(email)
    else:
        _visitor()
    footer()


def _visitor() -> None:
    page_header("Compte", "Rejoindre <em>Sensitor</em>",
                "Un compte gratuit ouvre toutes les leçons publiées et enregistre votre "
                "progression. Aucun moyen de paiement n'est demandé.")
    if rt.get_store() is None:
        st.error("La base de données est indisponible : la connexion est impossible pour l'instant.")
        reason = rt.store_error()
        if reason:
            with st.expander("Détail technique"):
                st.write(reason)
        return
    multi = rt.multi_user()
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        panes = st.tabs(["Se connecter", "Créer un compte"])
        with panes[0]:
            with st.form("sign_in_form"):
                address = st.text_input("Adresse e-mail", key="si_email")
                password = (st.text_input("Mot de passe", type="password", key="si_pw")
                            if multi else None)
                if st.form_submit_button("Se connecter", type="primary"):
                    result = rt.sign_in(address, password)
                    if result:
                        rt.go("home")
                        st.rerun()
                    st.error(_message(result))
        with panes[1]:
            with st.form("sign_up_form"):
                address = st.text_input("Adresse e-mail", key="su_email")
                password = (st.text_input(f"Mot de passe ({MIN_PASSWORD_LENGTH} caractères minimum)",
                                          type="password", key="su_pw") if multi else None)
                if st.form_submit_button("Créer mon compte", type="primary"):
                    result = rt.sign_up(address, password)
                    if result:
                        _send_verification(result.email)
                        rt.go("home")
                        st.rerun()
                    st.error(_message(result))
        if multi:
            with st.expander("Mot de passe oublié ?"):
                _forgot()
        else:
            note("Mode local : aucun mot de passe n'est demandé. Pour un site ouvert au public, "
                 "réglez SENSITOR_AUTH=multi.")
    with right:
        rows = "".join(f'<div><span class="n">{i:02d}</span><span class="x"><b>{esc(t)}</b><br>'
                       f'<span style="color:var(--muted);font-size:14px">{esc(x)}</span></span></div>'
                       for i, (t, x) in enumerate(BENEFITS, start=1))
        html(f'<div class="sx-kicker muted" style="margin-bottom:.4rem">Ce que donne un compte</div>'
             f'<div class="sx-objectives single">{rows}</div>'
             f'<p class="sx-note" style="margin-top:1.2rem">Vous restez connecté sur cet appareil '
             f'pendant 30 jours, ou jusqu\'à votre déconnexion.</p>')


def _forgot() -> None:
    if not mailer.configured():
        notice("Envoi d'e-mails non configuré",
               "Ce déploiement n'envoie pas encore d'e-mails. Écrivez au support Sensitor depuis "
               "l'adresse de votre compte : un lien de réinitialisation vous sera transmis.", "info")
        return
    with st.form("forgot_form"):
        address = st.text_input("Adresse e-mail du compte", key="fp_email")
        if st.form_submit_button("Recevoir un lien de réinitialisation", type="primary"):
            auth = rt.get_auth()
            token = auth.request_password_reset(address) if auth else None
            if token:
                try:
                    mailer.send(address.strip().lower(), "Réinitialiser votre mot de passe Sensitor",
                                mailer.reset_body(mailer.link("reset", token)))
                except mailer.MailError:
                    st.error("L'e-mail n'a pas pu être envoyé. Réessayez dans quelques minutes.")
                    return
            # Same answer whether or not the address has an account.
            st.success("Si un compte existe pour cette adresse, un e-mail vient d'être envoyé. "
                       "Le lien est valable une heure.")


def _access_text(store, email: str, who) -> str:
    """What the member's level opens, and until when, from their active entitlement."""
    if who.level != P.PREMIUM:
        return "Gratuit : toutes les leçons publiées hors Premium"
    now = _now()
    active = [e for e in store.entitlements(email) if not e["revoked_at"] and e["starts_at"] <= now
              and not (e["ends_at"] and e["ends_at"] <= now)]
    ends = [e["ends_at"] for e in active if e["ends_at"]]
    if len(ends) == len(active) and ends:
        return f"Premium, jusqu'au {date_fr(max(ends))}"
    return "Premium, sans date de fin"


def _member(email: str) -> None:
    store = rt.get_store()
    auth = rt.get_auth()
    user = store.get_user(email) if store else None
    who = rt.member(email)
    verified = (user or {}).get("email_verified_at")
    page_header("Compte · Membre", "Votre <em>compte</em>",
                "Un seul compte pour tous les espaces Sensitor.")
    roles = ", ".join(P.ROLE_LABELS[r] for r in sorted(who.roles))
    html('<dl class="sx-facts" style="max-width:640px;margin-top:1.6rem">'
         f'<div><dt>Adresse</dt><dd>{esc(email)}</dd></div>'
         f'<div><dt>Adresse vérifiée</dt><dd>{"Oui, le " + esc(date_fr(verified)) if verified else "Pas encore"}</dd></div>'
         f'<div><dt>Membre depuis</dt><dd>{esc(date_fr((user or {}).get("created_at", "")))}</dd></div>'
         f'<div><dt>Accès</dt><dd>{esc(_access_text(store, email, who))}</dd></div>'
         + (f'<div><dt>Rôles</dt><dd>{esc(roles)}</dd></div>' if roles else '')
         + '<div><dt>Abonnement</dt><dd>Aucun : il n\'existe pas d\'abonnement payant</dd></div></dl>')
    if not rt.multi_user():
        st.warning("Cette installation fonctionne en mode local (SENSITOR_AUTH n'est pas réglé sur "
                   "« multi ») : l'adresse sert d'identifiant sans mot de passe. Ce mode convient à "
                   "un usage personnel, pas à un site ouvert.")
    c1, c2, _ = st.columns([1, 1.4, 1.2])
    with c1:
        if st.button("Se déconnecter", key="sign_out"):
            rt.sign_out()
            rt.go("home")
            st.rerun()
    with c2:
        if st.button("Se déconnecter de tous les appareils", key="sign_out_all"):
            auth.sign_out_everywhere(email)
            rt.sign_out()
            rt.go("home")
            st.rerun()
    if not verified and mailer.configured():
        if st.button("Renvoyer l'e-mail de vérification", key="resend_verify", type="tertiary"):
            st.success("E-mail envoyé." if _send_verification(email)
                       else "L'e-mail n'a pas pu être envoyé. Réessayez plus tard.")

    section(1, "Profil", "Le nom affiché sur vos pages. Il n'est montré à aucun autre membre.")
    with st.form("profile_form"):
        name = st.text_input("Nom affiché", value=(user or {}).get("display_name") or "", max_chars=60,
                             key="pf_display_name")
        if st.form_submit_button("Enregistrer"):
            store.set_display_name(email, name)
            st.success("Profil enregistré.")

    section(2, "La lettre de Sensitor", "Articles, analyses pédagogiques et nouveautés, par e-mail, avec votre accord.")
    letter = store.newsletter(email)
    status = (letter or {}).get("status")
    if status == "confirmed":
        note(f"Inscrit depuis le {date_fr(letter['confirmed_at'])}.")
        if st.button("Me désinscrire de la lettre", key="newsletter_off"):
            N.unsubscribe(store, email)
            st.rerun()
    else:
        if status == "pending":
            note("Inscription en attente : ouvrez le lien de confirmation reçu par e-mail.")
        newsletter_pages.form("account_newsletter", email=email, source="account")

    if rt.multi_user():
        section(3, "Mot de passe", "Changer de mot de passe déconnecte tous vos autres appareils.")
        with st.form("change_password_form"):
            current = st.text_input("Mot de passe actuel", type="password", key="cp_current")
            new = st.text_input(f"Nouveau mot de passe ({MIN_PASSWORD_LENGTH} caractères minimum)",
                                type="password", key="cp_new")
            again = st.text_input("Confirmer le nouveau mot de passe", type="password", key="cp_again")
            if st.form_submit_button("Changer le mot de passe", type="primary"):
                if new != again:
                    st.error("Les deux nouveaux mots de passe ne correspondent pas.")
                else:
                    result = auth.change_password(email, current, new)
                    if result:
                        rt.remember(result.token)
                        st.success("Mot de passe changé. Vos autres appareils ont été déconnectés.")
                    else:
                        st.error(_message(result))

    section(4, "Vos données", "Tout ce que Sensitor conserve à votre nom, dans un seul fichier : compte, accès, "
            "sessions, progression, journaux, portefeuilles, lettre et, pour un coach, ce qu'il a rédigé.")
    export = json.dumps(store.export_user(email), ensure_ascii=False, indent=2, default=str)
    st.download_button("Exporter toutes mes données (JSON)", data=export.encode("utf-8"),
                       file_name="sensitor-mes-donnees.json", mime="application/json",
                       key="export_all")

    section(5, "Supprimer le compte",
            "La suppression efface définitivement le compte, la progression, les quiz, le journal "
            "de réflexion, l'inscription à la lettre et, le cas échéant, les portefeuilles et le journal de trading. "
            "Elle ne peut pas être annulée.")
    multi = rt.multi_user()
    with st.form("delete_account_form"):
        if multi:
            secret = st.text_input("Pour confirmer, saisissez votre mot de passe", type="password", key="del_pw")
        else:
            secret = st.text_input("Pour confirmer, saisissez votre adresse e-mail", key="del_email")
        if st.form_submit_button("Supprimer définitivement mon compte"):
            done = (auth.delete_account(email, secret) if multi
                    else auth.delete_account(email, typed=secret)) if auth else None
            if done is None:
                st.error("Le mot de passe est incorrect." if multi
                         else "L'adresse saisie ne correspond pas à celle du compte.")
            else:
                rt.sign_out()
                rt.go("home")
                st.rerun()


# =============================================================================
# Links received by e-mail
# =============================================================================

def reset_page(catalog, email, route) -> None:
    crumbs("Sensitor", "Compte", "Nouveau mot de passe")
    page_header("Compte", "Choisir un <em>nouveau</em> mot de passe",
                "Le lien reçu par e-mail ne fonctionne qu'une fois et pendant une heure.")
    token = route.get("token")
    if not token:
        notice("Lien incomplet", "Ouvrez le lien tel qu'il figure dans l'e-mail reçu.", "info")
        footer()
        return
    left, _ = st.columns([1.15, 1])
    with left:
        with st.form("reset_form"):
            new = st.text_input(f"Nouveau mot de passe ({MIN_PASSWORD_LENGTH} caractères minimum)",
                                type="password", key="rs_new")
            again = st.text_input("Confirmer le mot de passe", type="password", key="rs_again")
            if st.form_submit_button("Enregistrer et me connecter", type="primary"):
                if new != again:
                    st.error("Les deux mots de passe ne correspondent pas.")
                else:
                    auth = rt.get_auth()
                    result = auth.reset_password(token, new) if auth else None
                    if result:
                        rt.remember(result.token)
                        rt.go("home")
                        st.rerun()
                    st.error(_message(result))
    footer()


def verify_page(catalog, email, route) -> None:
    crumbs("Sensitor", "Compte", "Vérification de l'adresse")
    auth = rt.get_auth()
    done_key = f"ac_verified::{route.get('token')}"
    if done_key not in st.session_state:
        result = auth.verify_email(route.get("token") or "") if auth else None
        st.session_state[done_key] = bool(result)
    if st.session_state[done_key]:
        page_header("Compte", "Adresse <em>confirmée</em>",
                    "Merci : votre adresse e-mail est vérifiée.")
    else:
        page_header("Compte", "Lien <em>expiré</em>",
                    "Ce lien de vérification a déjà servi ou il a expiré. Vous pouvez en demander "
                    "un nouveau depuis la page de votre compte.")
    rt.link("Aller à mon espace", "home", key="verify_home", kind="primary")
    footer()
