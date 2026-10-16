"""
Outgoing e-mail, for the two messages the platform sends: a password-reset link
and an address-verification link.

Plain SMTP, configured through the environment (or Streamlit secrets):

    SENSITOR_SMTP_HOST       smtp.example.com
    SENSITOR_SMTP_PORT       587 (STARTTLS) or 465 (TLS)
    SENSITOR_SMTP_USER       login
    SENSITOR_SMTP_PASSWORD   password or app token
    SENSITOR_MAIL_FROM       "Sensitor <no-reply@example.com>"
    SENSITOR_PUBLIC_URL      https://sensitor.streamlit.app  (base of the links)

Any transactional provider that offers SMTP works (Brevo, Postmark, Resend,
Mailgun, an OVH or Gmail mailbox). When the host is not set, `configured()` is
False and the UI says so instead of pretending a message was sent.

`transport` exists for the tests: they pass an object with `send(message)` and
no network is touched.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage

DEFAULT_URL = "http://localhost:8501"


@dataclass(frozen=True)
class MailConfig:
    host: str
    port: int
    user: str
    password: str
    sender: str


def config() -> MailConfig | None:
    host = os.getenv("SENSITOR_SMTP_HOST", "").strip()
    if not host:
        return None
    try:
        port = int(os.getenv("SENSITOR_SMTP_PORT", "587"))
    except ValueError:
        port = 587
    return MailConfig(host=host, port=port, user=os.getenv("SENSITOR_SMTP_USER", ""),
                      password=os.getenv("SENSITOR_SMTP_PASSWORD", ""),
                      sender=os.getenv("SENSITOR_MAIL_FROM", "") or os.getenv("SENSITOR_SMTP_USER", ""))


def configured() -> bool:
    return config() is not None


def public_url() -> str:
    return (os.getenv("SENSITOR_PUBLIC_URL", "").strip() or DEFAULT_URL).rstrip("/")


def link(page: str, token: str) -> str:
    return f"{public_url()}/?page={page}&token={token}"


class MailError(RuntimeError):
    """The message could not be handed to the SMTP server."""


class SMTPTransport:
    def __init__(self, cfg: MailConfig, timeout: float = 15.0):
        self.cfg = cfg
        self.timeout = timeout

    def send(self, message: EmailMessage) -> None:
        context = ssl.create_default_context()
        try:
            if self.cfg.port == 465:
                with smtplib.SMTP_SSL(self.cfg.host, self.cfg.port, context=context,
                                      timeout=self.timeout) as server:
                    self._deliver(server, message)
            else:
                with smtplib.SMTP(self.cfg.host, self.cfg.port, timeout=self.timeout) as server:
                    server.starttls(context=context)
                    self._deliver(server, message)
        except (smtplib.SMTPException, OSError) as exc:
            raise MailError(str(exc)) from exc

    def _deliver(self, server, message: EmailMessage) -> None:
        if self.cfg.user:
            server.login(self.cfg.user, self.cfg.password)
        server.send_message(message)


def _message(to: str, subject: str, body: str, sender: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    return message


def send(to: str, subject: str, body: str, *, transport=None) -> None:
    cfg = config()
    if transport is None:
        if cfg is None:
            raise MailError("SMTP is not configured")
        transport = SMTPTransport(cfg)
    sender = cfg.sender if cfg else "Sensitor <no-reply@localhost>"
    transport.send(_message(to, subject, body, sender))


def reset_body(url: str) -> str:
    return (
        "Bonjour,\n\n"
        "Une réinitialisation du mot de passe de votre compte Sensitor a été demandée.\n"
        "Pour choisir un nouveau mot de passe, ouvrez ce lien dans l'heure qui vient :\n\n"
        f"{url}\n\n"
        "Le lien ne fonctionne qu'une fois. Si vous n'êtes pas à l'origine de cette demande, "
        "ignorez ce message : votre mot de passe actuel reste valable.\n\n"
        "Sensitor\n")


def verify_body(url: str) -> str:
    return (
        "Bonjour,\n\n"
        "Pour confirmer que cette adresse est bien la vôtre, ouvrez ce lien dans les "
        "prochaines 48 heures :\n\n"
        f"{url}\n\n"
        "Si vous n'avez pas créé de compte Sensitor, ignorez ce message.\n\n"
        "Sensitor\n")
