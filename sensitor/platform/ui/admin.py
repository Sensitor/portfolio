"""
Internal management: the members and their access, for administrators.

One page, `?page=admin`. Every read and write goes through a `Store` method
that checks the administrator role in its own SQL statement; the page's own
check only decides what to draw. The selected member is held in session, never
in the address bar, so an address does not end up in a browser history or a
server log.

Premium is granted by hand with a reason and an optional end date; each grant
and each revocation stays in the `entitlements` table, which is the trace.
Nothing here is billing.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from ...core import permissions as P
from ...database.connection import now as _now
from . import runtime as rt
from .components import crumbs, date_fr, esc, footer, html, note, notice, page_header, section

SELECTED = "admin_selected"
SOURCES = {"manual": "Attribution manuelle", "payment": "Paiement", "migration": "Niveau antérieur",
           "config": "Liste PRO_EMAILS"}


def _status(item: dict, now: str) -> str:
    if item.get("revoked_at"):
        return f"Retiré le {date_fr(item['revoked_at'])}"
    if item.get("ends_at") and item["ends_at"] <= now:
        return f"Terminé le {date_fr(item['ends_at'])}"
    if item.get("ends_at"):
        return f"Actif jusqu'au {date_fr(item['ends_at'])}"
    return "Actif, sans date de fin"


def render(catalog, email, route) -> None:
    crumbs("Sensitor", "Gestion", "Membres")
    page_header("Gestion · réservé aux administrateurs", "Les membres et <em>leurs accès</em>.",
                "Rechercher un membre, lui attribuer ou lui retirer l'accès Premium avec un motif, "
                "nommer un coach ou un administrateur. Chaque attribution reste tracée.")
    store = rt.get_store()
    if store is None or not rt.can(email, "admin.members"):
        notice("Accès réservé", "Cette page est réservée aux administrateurs de Sensitor.", "lock")
        footer()
        return

    counts = store.admin_count(email) or {}
    html('<dl class="sx-facts" style="max-width:640px;margin-top:1.2rem">'
         f'<div><dt>Membres</dt><dd>{counts.get("members", 0)}</dd></div>'
         f'<div><dt>Accès Premium actifs</dt><dd>{counts.get("premium", 0)}</dd></div>'
         f'<div><dt>Adresses vérifiées</dt><dd>{counts.get("verified", 0)}</dd></div></dl>')

    section(1, "Rechercher", "Par adresse ou par nom affiché.")
    query = st.text_input("Adresse ou nom", key="admin_query", placeholder="nom@exemple.fr")
    members = store.admin_members(email, query=query) or []
    if not members:
        note("Aucun membre ne correspond à cette recherche.")
        footer()
        return
    rows = [{"Adresse": m["email"], "Nom": m.get("display_name") or "",
             "Niveau": P.LEVEL_LABELS.get(m["level"], m["level"]),
             "Rôles": ", ".join(P.ROLE_LABELS[r] for r in m["roles"]),
             "Inscrit le": date_fr(m.get("created_at") or ""),
             "Dernière connexion": date_fr(m["last_login_at"]) if m.get("last_login_at") else ""}
            for m in members]
    st.dataframe(rows, hide_index=True, width="stretch", key="admin_table")
    addresses = [m["email"] for m in members]
    current = st.session_state.get(SELECTED)
    chosen = st.selectbox("Ouvrir la fiche de", addresses,
                          index=addresses.index(current) if current in addresses else 0, key="admin_pick")
    st.session_state[SELECTED] = chosen
    _member(store, email, chosen)
    footer()


def _member(store, admin: str, member: str) -> None:
    item = store.admin_member(admin, member)
    if item is None:
        note("Ce membre n'existe plus.")
        return
    now = _now()
    section(2, member, "Niveau, rôles et historique des accès.")
    html('<dl class="sx-facts" style="max-width:640px">'
         f'<div><dt>Niveau</dt><dd>{esc(P.LEVEL_LABELS.get(item["level"], item["level"]))}</dd></div>'
         f'<div><dt>Rôles</dt><dd>{esc(", ".join(P.ROLE_LABELS[r] for r in item["roles"]) or "Aucun")}</dd></div>'
         f'<div><dt>Adresse vérifiée</dt><dd>{"Oui" if item.get("email_verified_at") else "Pas encore"}</dd></div>'
         '</dl>')

    left, right = st.columns(2, gap="large")
    with left:
        html('<div class="sx-kicker muted">Attribuer l\'accès Premium</div>')
        with st.form(f"grant_{member}"):
            reason = st.text_input("Motif (obligatoire)", key="grant_reason",
                                   placeholder="Bêta-testeur, partenariat, geste commercial…")
            dated = st.checkbox("Avec une date de fin", key="grant_dated")
            end = st.date_input("Date de fin", value=date.today() + timedelta(days=30),
                                min_value=date.today() + timedelta(days=1), key="grant_end", format="DD/MM/YYYY")
            if st.form_submit_button("Attribuer", type="primary"):
                ends_at = f"{end.isoformat()}T23:59:59+00:00" if dated else None
                if not reason.strip():
                    st.error("Indiquez un motif : il reste dans l'historique.")
                elif store.grant_access(admin, member, reason=reason, ends_at=ends_at) is None:
                    st.error("L'attribution a été refusée.")
                else:
                    st.success("Accès Premium attribué.")
                    st.rerun()
    with right:
        html('<div class="sx-kicker muted">Rôles</div>')
        for role in P.ROLES:
            has = role in item["roles"]
            own_admin = role == P.ADMIN and member == admin
            name = P.ROLE_LABELS[role].lower()
            label = f"Retirer le rôle {name}" if has else f"Nommer {name}"
            if st.button(label, key=f"role_{role}_{member}", disabled=own_admin and has,
                         help="Vous ne pouvez pas retirer votre propre rôle d'administrateur." if own_admin and has
                         else None):
                if store.admin_set_role(admin, member, role, not has):
                    st.rerun()
                st.error("Le changement de rôle a été refusé.")

    html('<div class="sx-kicker muted" style="margin-top:1.4rem">Historique des accès</div>')
    if not item["entitlements"]:
        note("Aucun accès Premium n'a jamais été attribué à ce membre.")
        return
    for grant in item["entitlements"]:
        active = not grant.get("revoked_at") and not (grant.get("ends_at") and grant["ends_at"] <= now)
        cols = st.columns([3, 1])
        with cols[0]:
            html(f'<div class="sx-c-row" style="grid-template-columns:1fr"><div>'
                 f'<div class="sym">{esc(_status(grant, now))}</div>'
                 f'<div class="when">{esc(SOURCES.get(grant["source"], grant["source"]))} · le '
                 f'{esc(date_fr(grant["created_at"]))}'
                 f'{" · par " + esc(grant["reference"]) if grant.get("reference") else ""}</div>'
                 f'<div class="q">{esc(grant.get("reason") or "")}</div></div></div>')
        with cols[1]:
            if active and st.button("Retirer", key=f"revoke_{grant['id']}"):
                if store.revoke_access(admin, grant["id"]):
                    st.rerun()
                st.error("Le retrait a été refusé.")
