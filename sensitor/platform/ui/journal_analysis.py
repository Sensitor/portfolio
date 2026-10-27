"""
The trading analytics inside the « Journal de trading » space, and the
MetaTrader 5 synchronisation.

Nothing of the analysis is rewritten. The four pages are the separate app's
trading renderers (`sensitor.pages.trading_*`), in French and styled by the
analyzer's component stylesheet (`ui.themes.inject_components`), as the
« Portefeuille et risque » space does for the portfolio pages. They read the
same trades table as the journal, through the same verified email: the
renderers resolve the member from the session token, read the book per run and
cache nothing across users (`pages._trading_shared.trading_context`).

What this module adds is the platform side: the space's navigation, a sign-in
prompt for a visitor, the journal's own empty state, and a word when the
dashboard is showing the demonstration journal, which these pages never read.

The synchronisation form calls the connector (`integrations.mt5`) and the merge
rule that keeps what the member wrote (`integrations.sync`); it knows nothing of
MT5 itself. It asks for the investor password, which only reads, and never keeps
it: the form clears on submit, and only the account number, server, offset and
window are remembered for the next sync.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone

import streamlit as st

from ...pages import (render_trading_analytics, render_trading_overview, render_trading_psychology,
                      render_trading_risk)
from ...ui import themes as analysis_theme
from . import runtime as rt
from . import trading_journal as J
from .. import spaces
from .components import crumbs, esc, footer, html, notice

PAGES = (
    ("journal_performance", "Performance", render_trading_overview),
    ("journal_analysis", "Analyse", render_trading_analytics),
    ("journal_risk", "Risque", render_trading_risk),
    ("journal_behaviour", "Comportement", render_trading_psychology),
)
SYNC_DEFAULTS = "jr_mt5_last"            # account number, server, offset, window; never the password


def _page(page: str, label: str, render):
    def renderer(catalog, email, route) -> None:
        crumbs("Sensitor", spaces.space("journal").label, label)
        J.nav(page, email)
        if not email:
            J._signin_prompt(page, "Connectez-vous pour analyser vos trades.")
            footer()
            return
        if st.session_state.get(J.DEMO_KEY):
            notice("Vos trades, pas l'exemple", "Le tableau de bord montre le journal d'exemple ; les analyses "
                   "lisent toujours votre propre journal.", "info")
            if st.button("Revenir à mon journal", key=f"demo_off_{page}"):
                st.session_state[J.DEMO_KEY] = False
                st.rerun()
        store = rt.get_store()
        if store is None or not store.count_trades(email):
            J._empty_state(email)
            footer()
            return
        st.session_state["language"] = "fr"
        analysis_theme.inject_components()
        render()
        footer()
    renderer.__name__ = f"render_{page}"
    return renderer


RENDERERS = {page: _page(page, label, render) for page, label, render in PAGES}


# =============================================================================
# METATRADER 5
# =============================================================================

CLOCKS = {"ny+7": "UTC+2 l'hiver, UTC+3 l'été (la plupart des courtiers forex)",
          "2": "UTC+2 toute l'année", "3": "UTC+3 toute l'année", "0": "UTC", "1": "UTC+1 (heure de Paris en hiver)"}
CLOCK_KEY = "jr_report_clock"
STEPS = (
    ("Ouvrez l'historique", "Dans MetaTrader 5 sur ordinateur, ouvrez la <b>Boîte à outils</b> (Ctrl+T, ou Cmd+T "
     "sur Mac) et cliquez sur l'onglet <b>Historique</b> (<i>History</i>) en bas de la fenêtre."),
    ("Choisissez la période", "Clic droit dans la liste (sur Mac : clic à deux doigts), puis la période : "
     "<b>Tout l'historique</b> (<i>All History</i>), ou les derniers mois."),
    ("Exportez le rapport", "Clic droit encore, <b>Rapport</b> (<i>Report</i>), puis <b>HTML</b> ou <b>Open XML</b> "
     "(Excel). Enregistrez le fichier."),
    ("Déposez-le ici", "Vos positions clôturées sont lues avec leurs prix, leur stop et leur résultat. Les positions "
     "encore ouvertes viendront au prochain rapport, une fois fermées."),
)


def report_section(store, email: str) -> None:
    """Section « Importer depuis MetaTrader 5 » of the entry page: the history report, without a terminal."""
    from ...integrations import mt5_report as MR
    from ...integrations import sync as broker_sync

    html('<ol class="sx-j-steps">' + "".join(f"<li><b>{esc(t)}</b><span>{body}</span></li>" for t, body in STEPS)
         + "</ol>")
    with st.container(key="panel_jr_report"):
        upload = st.file_uploader("Le rapport MetaTrader 5", type=["html", "htm", "xlsx"], key="jr_report")
        clock = st.selectbox("Heure du serveur de votre courtier", list(CLOCKS), format_func=CLOCKS.get,
                             key=CLOCK_KEY, help="Les heures du rapport sont celles du serveur, affichée en haut de la "
                             "fenêtre Market Watch du terminal (« Market Watch: 19:35 »). Comparez-la à l'heure "
                             "UTC, qui a une heure de retard sur Paris en hiver et deux en été. La plupart des "
                             "courtiers forex affichent l'heure de New York plus sept heures, soit UTC+2 l'hiver et "
                             "UTC+3 l'été : c'est le choix proposé.")
        if upload is None:
            return
        try:
            report = MR.read(upload.getvalue(), upload.name, clock=clock if clock == MR.NY_PLUS_7 else float(clock))
        except MR.ReportError as exc:
            st.error(f"Ce fichier n'a pas pu être lu : {exc}.")
            return
        n = len(report.trades)
        account = f"compte {report.account_login}, " if report.account_login else ""
        html(f'<p class="sx-note"><b>{n}</b> position{"s" if n > 1 else ""} clôturée{"s" if n > 1 else ""} '
             f'trouvée{"s" if n > 1 else ""} ({esc(account)}{esc(report.currency or "")})'
             + (f", {len(report.skipped)} ligne{'s' if len(report.skipped) > 1 else ''} écartée"
                f"{'s' if len(report.skipped) > 1 else ''}" if report.skipped else "") + ".</p>")
        k = report.protective_stops
        if k:
            notice("Stops au point d'entrée ou en profit", f"{k} position{'s ont' if k > 1 else ' a'} un dernier stop "
                   "au point d'entrée ou en profit. Le rapport ne donne que le dernier stop, pas celui de "
                   "départ : pour ne pas inventer un R, il n'est pas calculé pour ces trades. Saisissez le stop de "
                   "départ sur la fiche d'un trade pour obtenir son R.", "info")
        if report.skipped:
            rows = "".join(f"<tr><td>{line}</td><td>{esc(why)}</td></tr>" for line, why in report.skipped[:8])
            html(f'<table><thead><tr><th>Ligne</th><th>Raison</th></tr></thead><tbody>{rows}</tbody></table>')
        if not n:
            return
        if st.button(f"Importer {n} trade{'s' if n > 1 else ''}", key="jr_report_go", type="primary"):
            result = broker_sync.sync_trades(MR.ReportSource(report), store, email,
                                             since=min(t.opened_at for t in report.trades))
            message = (f"Import terminé : {result.added} ajouté{'s' if result.added > 1 else ''}, "
                       f"{result.updated} mis à jour, {result.unchanged} déjà à jour.")
            if result.annotations_kept:
                message += " Vos annotations sont conservées."
            J.flash(message + " Réimporter le même rapport, ou un plus récent, ne crée aucun doublon.")
            st.session_state.pop("jr_report", None)
            st.rerun()


def terminal_available() -> bool:
    """Whether this server can reach a terminal at all: the package ships for Windows only."""
    return importlib.util.find_spec("MetaTrader5") is not None


def connector(config):
    """The connector to a terminal on this machine. A seam, so the tests can give it a fake terminal."""
    from ...integrations.mt5 import MT5Connector
    return MT5Connector(config)


def sync_section(store, email: str) -> None:
    """Section « Synchroniser MetaTrader 5 » of the entry page."""
    accounts = [a for a in store.list_accounts(email) if a.last_synced_at]
    if accounts:
        rows = "".join(f"<li><b>{esc(a.name or a.id)}</b> · {esc(a.currency or '')} · dernière synchronisation "
                       f"le {esc(_stamp(a.last_synced_at))}</li>" for a in accounts)
        html(f'<ul class="sx-c-facts">{rows}</ul>')
    html('<p class="sx-note">La synchronisation lit l\'historique d\'un terminal MetaTrader 5 ouvert sur la même '
         'machine que Sensitor, avec le paquet Python MetaTrader5, publié pour Windows seulement. Les trades sont '
         'appariés sur le numéro de position du courtier : resynchroniser ne crée aucun doublon, et vos setups, '
         'notes, émotions et évaluations sont conservés.</p>')
    if not terminal_available():
        notice("Pas de terminal sur ce serveur", "Ce déploiement ne tourne pas sous Windows avec MetaTrader 5 : la "
               "synchronisation directe n'y est pas possible. Importez plutôt le rapport d'historique, en haut de "
               "cette page : le résultat est le même.", "info")
        return
    last = st.session_state.get(SYNC_DEFAULTS) or {}
    with st.container(key="panel_jr_mt5"):
        with st.form("jr_mt5", clear_on_submit=True, border=False):
            a, b, c = st.columns(3)
            with a:
                login = st.text_input("Numéro de compte", value=last.get("login", ""), key="jr_mt5_login")
            with b:
                password = st.text_input("Mot de passe investisseur (lecture seule)", type="password",
                                         key="jr_mt5_password",
                                         help="Le mot de passe en lecture seule de votre compte, pas celui qui "
                                              "permet de passer des ordres. Il n'est pas conservé.")
            with c:
                server = st.text_input("Serveur", value=last.get("server", ""), key="jr_mt5_server",
                                       placeholder="Broker-Live")
            d, e, f = st.columns(3)
            with d:
                offset = st.number_input("Décalage UTC du serveur (heures)", min_value=-12.0, max_value=14.0,
                                         value=float(last.get("offset", 0.0)), step=1.0, key="jr_mt5_offset")
            with e:
                days = st.number_input("Historique à lire (jours)", min_value=1, max_value=3650,
                                       value=int(last.get("days", 365)), step=30, key="jr_mt5_days")
            with f:
                path = st.text_input("Chemin du terminal (facultatif)", value=last.get("path", ""),
                                     key="jr_mt5_path", placeholder="terminal64.exe")
            html('<p class="sx-note">Les heures MetaTrader sont celles du serveur du courtier, souvent UTC+2 ou '
                 'UTC+3. Saisissez le décalage que montre l\'horloge du terminal : sans lui, les trades tombent '
                 'dans la mauvaise séance. Laissez le compte vide pour lire celui qui est déjà connecté au '
                 'terminal.</p>')
            go = st.form_submit_button("Synchroniser", type="primary")
    if go:
        st.session_state.pop("jr_mt5_password", None)     # gone from the session before the terminal is even called
        st.session_state[SYNC_DEFAULTS] = {"login": login.strip(), "server": server.strip(), "offset": offset,
                                           "days": int(days), "path": path.strip()}
        run_sync(store, email, login=login, password=password, server=server, path=path, offset=offset,
                 days=int(days))


def run_sync(store, email: str, *, login, password, server, path, offset, days) -> None:
    from ...core.exceptions import IntegrationError
    from ...integrations import sync as broker_sync
    from ...integrations.mt5 import MT5Config

    config = MT5Config(
        login=int(login) if str(login).strip().isdigit() else None,
        password=password or None,
        server=str(server).strip() or None,
        path=str(path).strip() or None,
        server_utc_offset_hours=float(offset),
    )
    # The connector and the stored MT5 trades are on naive UTC.
    since = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0) - timedelta(days=days)
    try:
        with st.spinner("Lecture du terminal..."):
            with connector(config) as broker:
                result = broker_sync.sync_trades(broker, store, email, since=since)
    except IntegrationError as exc:
        # The connector's message says what to do, and never contains the password.
        st.error(f"MetaTrader 5 n'a pas pu être lu. Message du terminal : {exc}")
        return
    except Exception as exc:                                      # noqa: BLE001
        st.error(f"La synchronisation a échoué : {exc}")
        return
    message = f"Synchronisation terminée : {result.summary('fr')}."
    if result.annotations_kept:
        kept = result.annotations_kept
        message += f" {kept} trade{'s ont' if kept > 1 else ' a'} gardé vos annotations."
    J.flash(message)
    st.rerun()


def _stamp(value: str) -> str:
    try:
        moment = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return str(value)
    return J._when(moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc))
