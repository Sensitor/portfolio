"""
Technical logs, without personal data.

One logger tree, `sensitor`, written to the standard error stream (Streamlit
Cloud, Render or a VPS keep it in their logs). Every line goes through `redact`
after formatting, traceback included: an e-mail address, a database URL, a
token, a password parameter or a bearer header never reaches the log, even when
an exception message carries one.

    SENSITOR_LOG_LEVEL   DEBUG, INFO (default), WARNING, ERROR

What is logged: a page that raised, the database that could not be opened or
lost its connection, an e-mail that could not be sent, a provider that refused a
call, an account locked after failed sign-ins (without its address). What is
not: who did what, any content, any figure of a member.

No Streamlit.
"""

from __future__ import annotations

import logging
import os
import re
import sys

ROOT = "sensitor"
FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

_PATTERNS = (
    (re.compile(r"postgres(?:ql)?://\S+", re.I), "[url de base]"),
    (re.compile(r"(?i)(password|passwd|pwd|secret|api[-_]?key|token)(\s*[=:]\s*)([^\s&,;'\"]+)"), r"\1\2[masqué]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [jeton]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[adresse]"),
    (re.compile(r"\b[A-Za-z0-9_-]{32,}\b"), "[jeton]"),
)


def redact(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))


def setup(stream=None) -> logging.Logger:
    """Configure the `sensitor` logger once per process (idempotent); returns it."""
    logger = logging.getLogger(ROOT)
    if not any(getattr(h, "_sensitor", False) for h in logger.handlers):
        handler = logging.StreamHandler(stream or sys.stderr)
        handler.setFormatter(RedactingFormatter(FORMAT))
        handler._sensitor = True                       # noqa: SLF001
        logger.addHandler(handler)
        logger.propagate = False
    level = os.getenv("SENSITOR_LOG_LEVEL", "INFO").strip().upper()
    logger.setLevel(getattr(logging, level, logging.INFO))
    return logger


def get(name: str) -> logging.Logger:
    """A logger under `sensitor` (pass `__name__`)."""
    setup()
    return logging.getLogger(name if name.startswith(ROOT) else f"{ROOT}.{name}")
