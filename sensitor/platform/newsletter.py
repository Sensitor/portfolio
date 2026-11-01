"""
The newsletter: consent, double confirmation, one-click unsubscription.

A request records the exact wording the person accepted and when (the proof of
consent), and sends a confirmation link valid 48 hours; the subscription is
active only once that link is opened and its button pressed, so a mailbox
scanner that opens links does not subscribe anyone. Every message carries an
unsubscribe link that works in one click, for good. The provider (Brevo, see
`integrations.brevo`) is told on confirmation and on unsubscription when it is
configured; Sensitor's own record stays the reference for consent.

No Streamlit. Mail goes through `core.mailer`; tests pass a fake transport.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from ..core import mailer
from ..core.security import new_token, token_fingerprint
from ..integrations import brevo

CONSENT_TEXT = ("J'accepte de recevoir la lettre de Sensitor par e-mail : articles, analyses pédagogiques et "
                "nouveautés de la plateforme. Je peux me désinscrire à tout moment, en un clic depuis chaque "
                "message ou depuis mon compte.")
CONFIRM_HOURS = 48
RESEND_MINUTES = 10
SOURCES = ("account", "site")
log = logging.getLogger(__name__)


def _stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")


def confirm_body(confirm_url: str, stop_url: str) -> str:
    return (
        "Bonjour,\n\n"
        "Une inscription à la lettre de Sensitor a été demandée pour cette adresse.\n"
        f"Pour la confirmer, ouvrez ce lien dans les {CONFIRM_HOURS} heures, puis appuyez sur « Confirmer » :\n\n"
        f"{confirm_url}\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message : rien ne vous sera envoyé.\n\n"
        f"Pour ne plus jamais recevoir de message de la lettre : {stop_url}\n\n"
        "Sensitor\n"
    )


def request(store, email: str, *, source: str, consented: bool, transport=None) -> str:
    """
    Ask to subscribe. Returns one of:
    « sent » (a confirmation was e-mailed), « confirmed » (already subscribed),
    « throttled » (a link was sent minutes ago), « no_consent », « invalid_email »,
    « no_mail » (e-mail is not configured: nothing is recorded, since nothing could
    be confirmed). The page shows the same message for « sent » and « throttled ».
    """
    email = (email or "").strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1] or len(email) > 254:
        return "invalid_email"
    if not consented:
        return "no_consent"
    if source not in SOURCES:
        raise ValueError("unknown source")
    if transport is None and not mailer.configured():
        return "no_mail"
    now = datetime.now(timezone.utc)
    confirm, stop = new_token(), new_token()
    outcome = store.newsletter_request(
        email, consent_text=CONSENT_TEXT, source=source, confirm_fingerprint=token_fingerprint(confirm),
        unsubscribe_fingerprint=token_fingerprint(stop), expires_at=_stamp(now + timedelta(hours=CONFIRM_HOURS)),
        resend_after=_stamp(now - timedelta(minutes=RESEND_MINUTES)))
    if outcome != "pending":
        return outcome
    # A new request (after an unsubscription, or a link left to expire) gets a
    # new stop link; a confirmed subscription is never touched here.
    try:
        mailer.send(email, "Confirmez votre inscription à la lettre de Sensitor",
                    confirm_body(mailer.link("newsletter_confirm", confirm), mailer.link("newsletter_stop", stop)),
                    transport=transport)
    except mailer.MailError:
        log.warning("newsletter confirmation could not be sent")
        return "mail_failed"
    return "sent"


def confirm(store, token: str, *, opener=None) -> str | None:
    """Confirm with the e-mailed link. The address, or None. Tells the provider when configured."""
    email = store.newsletter_confirm(token_fingerprint(token or ""))
    if email and _sync(brevo.subscribe, email, opener):
        store.newsletter_synced(email)
    return email


def stop(store, token: str, *, opener=None) -> str | None:
    """Unsubscribe in one click with the link every message carries. The address, or None."""
    email = store.newsletter_stop(token_fingerprint(token or ""))
    if email and _sync(brevo.unsubscribe, email, opener):
        store.newsletter_synced(email)
    return email


def unsubscribe(store, email: str, *, opener=None) -> bool:
    """From the account page."""
    done = store.newsletter_unsubscribe(email)
    if done and _sync(brevo.unsubscribe, email, opener):
        store.newsletter_synced(email)
    return done


def _sync(call, email: str, opener) -> bool:
    return call(email, opener=opener) if opener is not None else call(email)
