"""
Repositories — the query layer the application talks to.

`Store` is the only database surface the pages and the future API use. It owns a
connection from `connection.connect()` and serialises access behind a lock,
because Streamlit serves reruns from a thread pool and SQLite connections are
not safe to share across threads without one.

Privacy
-------
Rows carry an email address and the holdings behind it. That is personal
financial data: it stays on whatever machine runs the app, it is never sent
anywhere by this module, and a deployment that shares a database between people
needs authentication in front of it — the email field here identifies a row, it
does not authenticate anyone.

No Streamlit import: this module is testable and reusable on its own.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import asdict

from ..core import permissions as P
from .connection import connect, describe, now as _now, target
from .models import (
    SCHEMA_VERSION, TRADE_COLUMNS, Portfolio, Snapshot, TradingAccount, Workspace,
    _jsonable, _to_account, _to_portfolio, _to_snapshot, _to_workspace,
    row_to_trade, trade_to_row,
)


def _email(value: str) -> str:
    """
    Normalise an address into the form every row is keyed by.

    One function rather than `.strip().lower()` at each call site: a single
    method that forgot the `.lower()` would file a person's trades under a second
    identity and show them an empty journal, which reads as data loss.
    """
    return (value or "").strip().lower()


class Store:
    """
    Repository over SQLite.

    One connection, guarded by a lock: Streamlit serves reruns from a thread pool,
    and SQLite connections are not safe to share across threads without it.
    """

    def __init__(self, path: str | None = None):
        # Resolved here, not at import: see `connection.target`.
        self.path = path or target()
        self._lock = threading.Lock()
        self._conn = connect(path)

    # ── Plumbing ─────────────────────────────────────────────────────────────

    @contextmanager
    def _write(self):
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def _read(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            fast = getattr(self._conn, "read", None)       # Postgres: one round trip
            if fast is not None:
                return fast(sql, params)
            try:
                rows = self._conn.execute(sql, params).fetchall()
            except Exception:
                # A failed read must not leave the shared connection in an aborted transaction.
                self._conn.rollback()
                raise
            end = getattr(self._conn, "end_read", None)    # Postgres: close the read's transaction
            if end is not None:
                end()
            return rows

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ── Users ────────────────────────────────────────────────────────────────

    def upsert_user(self, email: str, tier: str = "free",
                    display_name: str | None = None) -> None:
        """
        Record or refresh a user.

        `tier` is ignored and kept for earlier callers: a new row is free, and a
        level comes from entitlements only (`set_tier`, `grant_access`), so a
        page that refreshes the row with the level it happens to hold in session
        can neither raise nor undo one.
        """
        email = _email(email)
        if not email:
            return
        now = _now()
        with self._write() as conn:
            conn.execute(
                """INSERT INTO users (email, tier, display_name, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(email) DO UPDATE SET
                     display_name = COALESCE(excluded.display_name, users.display_name),
                     updated_at = excluded.updated_at""",
                (email, P.FREE, display_name, now, now),
            )

    def set_tier(self, email: str, tier: str, *, source: str = "manual", reference: str = "cli",
                 reason: str = "") -> None:
        """
        The system's way to set a member's level, for trusted callers only: the
        operator's command line, `PRO_EMAILS` at sign-in, later a verified
        payment. Premium records an entitlement (unless one is already active);
        free revokes every active one. An administrator in the platform goes
        through `grant_access` and `revoke_access`, which check the role.
        """
        email = _email(email)
        if not email:
            return
        level = P.level_of(tier)
        with self._write() as conn:
            self._ensure_user(conn, email)
            stamp = _now()
            if level == P.PREMIUM:
                if self._active_entitlements(conn, email, stamp):
                    return
                conn.execute(
                    "INSERT INTO entitlements (user_email, level, source, reference, reason, starts_at, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)", (email, P.PREMIUM, source, reference, reason, stamp, stamp))
            else:
                conn.execute("UPDATE entitlements SET revoked_at = ?, revoked_by = ? "
                             "WHERE user_email = ? AND revoked_at IS NULL", (stamp, reference, email))
            self._cache_tier(conn, email, stamp)

    # ── Access: entitlements and roles ───────────────────────────────────────
    #
    # The level is computed from the active entitlements by
    # `core.permissions.level_from`; `users.tier` is a cache of it for the API
    # and the mobile app. Every administrator write checks the caller's role in
    # its own SQL statement, like the coach's writes.

    _ADMIN = "EXISTS (SELECT 1 FROM user_roles a WHERE a.user_email = ? AND a.role = 'admin')"

    @staticmethod
    def _active_entitlements(conn, email: str, stamp: str) -> list:
        return conn.execute(
            "SELECT id FROM entitlements WHERE user_email = ? AND revoked_at IS NULL AND starts_at <= ? "
            "AND (ends_at IS NULL OR ends_at > ?)", (email, stamp, stamp)).fetchall()

    def _cache_tier(self, conn, email: str, stamp: str) -> None:
        rows = conn.execute("SELECT level, starts_at, ends_at, revoked_at FROM entitlements WHERE user_email = ?",
                            (email,)).fetchall()
        level = P.level_from([dict(r) for r in rows], stamp)
        conn.execute("UPDATE users SET tier = ?, updated_at = ? WHERE email = ?", (level, stamp, email))

    def entitlements(self, email: str) -> list[dict]:
        """Every grant recorded for one member, the latest first, revoked and expired ones included."""
        return [dict(r) for r in self._read(
            "SELECT id, level, source, reference, reason, starts_at, ends_at, revoked_at, revoked_by, created_at "
            "FROM entitlements WHERE user_email = ? ORDER BY created_at DESC, id DESC", (_email(email),))]

    def roles(self, email: str) -> frozenset:
        return frozenset(r["role"] for r in self._read(
            "SELECT role FROM user_roles WHERE user_email = ?", (_email(email),)))

    def access(self, email: str) -> P.Member:
        """
        The member as the permissions module sees them: level from active
        entitlements, and roles. One query: it runs on every page.
        """
        email = _email(email)
        if not email:
            return P.VISITOR_MEMBER
        rows = self._read(
            "SELECT level, starts_at, ends_at, revoked_at, NULL AS role FROM entitlements WHERE user_email = ? "
            "UNION ALL SELECT NULL, NULL, NULL, NULL, role FROM user_roles WHERE user_email = ? "
            "UNION ALL SELECT NULL, NULL, NULL, NULL, 'cohort:' || m.cohort_id FROM cohort_members m "
            "JOIN cohorts c ON c.id = m.cohort_id WHERE m.user_email = ? AND c.status = 'open'",
            (email, email, email))
        grants = [dict(r) for r in rows if r["role"] is None]
        tags = [r["role"] for r in rows if r["role"] is not None]
        roles = frozenset(t for t in tags if not t.startswith("cohort:"))
        cohorts = frozenset(int(t.split(":", 1)[1]) for t in tags if t.startswith("cohort:"))
        return P.Member(email, P.level_from(grants, _now()), roles, cohorts)

    def has_admin(self) -> bool:
        """Whether anyone holds the administrator role (the pre-launch check asks)."""
        return bool(self._count("SELECT COUNT(*) AS n FROM user_roles WHERE role = 'admin'"))

    def is_admin(self, email: str) -> bool:
        return P.ADMIN in self.roles(email)

    def grant_role(self, email: str, role: str, *, granted_by: str = "cli") -> bool:
        """System path (command line). False for an unknown address."""
        if role not in P.ROLES:
            raise ValueError("unknown role")
        email = _email(email)
        with self._write() as conn:
            if not conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchall():
                return False
            conn.execute("INSERT INTO user_roles (user_email, role, granted_by, created_at) VALUES (?, ?, ?, ?) "
                         "ON CONFLICT (user_email, role) DO NOTHING", (email, role, granted_by, _now()))
            if role == P.COACH:
                conn.execute("UPDATE users SET role = 'coach', updated_at = ? WHERE email = ?", (_now(), email))
            return True

    def revoke_role(self, email: str, role: str) -> bool:
        if role not in P.ROLES:
            raise ValueError("unknown role")
        email = _email(email)
        with self._write() as conn:
            cursor = conn.execute("DELETE FROM user_roles WHERE user_email = ? AND role = ?", (email, role))
            if role == P.COACH:
                conn.execute("UPDATE users SET role = '', updated_at = ? WHERE email = ?", (_now(), email))
            return cursor.rowcount > 0

    def _member_row(self, row: dict, stamp: str) -> dict:
        email = row["email"]
        return {
            "email": email, "display_name": row.get("display_name"),
            "level": P.level_from(self.entitlements(email), stamp),
            "roles": sorted(self.roles(email)),
            "email_verified_at": row.get("email_verified_at"), "last_login_at": row.get("last_login_at"),
            "created_at": row.get("created_at"),
        }

    def admin_members(self, email: str, *, query: str = "", limit: int = 200) -> list[dict] | None:
        """
        The members, for an administrator: address, name, level, roles, dates.
        None for anyone else. Never the password hash or the throttling state.
        """
        if not self.is_admin(email):
            return None
        pattern = f"%{(query or '').strip().lower()}%"
        rows = self._read(
            "SELECT email, display_name, email_verified_at, last_login_at, created_at FROM users "
            "WHERE LOWER(email) LIKE ? OR LOWER(COALESCE(display_name, '')) LIKE ? "
            "ORDER BY created_at DESC, email LIMIT ?", (pattern, pattern, int(limit)))
        stamp = _now()
        return [self._member_row(dict(r), stamp) for r in rows]

    def admin_member(self, email: str, member: str) -> dict | None:
        """One member and their whole access history, for an administrator; None otherwise."""
        if not self.is_admin(email):
            return None
        rows = self._read("SELECT email, display_name, email_verified_at, last_login_at, created_at "
                          "FROM users WHERE email = ?", (_email(member),))
        if not rows:
            return None
        item = self._member_row(dict(rows[0]), _now())
        item["entitlements"] = self.entitlements(member)
        return item

    def admin_count(self, email: str) -> dict | None:
        """Head counts for the administrator's page."""
        if not self.is_admin(email):
            return None
        stamp = _now()
        return {
            "members": self._count("SELECT COUNT(*) AS n FROM users"),
            "premium": self._count(
                "SELECT COUNT(DISTINCT user_email) AS n FROM entitlements WHERE revoked_at IS NULL "
                "AND starts_at <= ? AND (ends_at IS NULL OR ends_at > ?)", stamp, stamp),
            "verified": self._count("SELECT COUNT(*) AS n FROM users WHERE email_verified_at IS NOT NULL"),
        }

    def grant_access(self, email: str, member: str, *, reason: str, ends_at: str | None = None) -> int | None:
        """
        An administrator gives `member` the premium level, with a reason and an
        optional end. Returns the entitlement's id; None when `email` is not an
        administrator, the member does not exist, or the reason is empty.
        """
        admin, member = _email(email), _email(member)
        reason = (reason or "").strip()[:300]
        if not reason or not member:
            return None
        stamp = _now()
        if ends_at is not None and ends_at <= stamp:
            raise ValueError("the end date is in the past")
        with self._write() as conn:
            cursor = conn.execute(
                "INSERT INTO entitlements (user_email, level, source, reference, reason, starts_at, ends_at, "
                "created_at) SELECT ?, 'premium', 'manual', ?, ?, ?, ?, ? "
                f"WHERE {self._ADMIN} AND EXISTS (SELECT 1 FROM users u WHERE u.email = ?) RETURNING id",
                (member, admin, reason, stamp, ends_at, stamp, admin, member))
            row = cursor.fetchone()
            if row is None:
                return None
            self._cache_tier(conn, member, stamp)
            return int(row[0])

    def revoke_access(self, email: str, entitlement_id: int) -> bool:
        """An administrator ends an active entitlement now. False otherwise."""
        admin = _email(email)
        stamp = _now()
        with self._write() as conn:
            owner = conn.execute("SELECT user_email FROM entitlements WHERE id = ? AND revoked_at IS NULL",
                                 (int(entitlement_id),)).fetchall()
            if not owner:
                return False
            cursor = conn.execute(
                "UPDATE entitlements SET revoked_at = ?, revoked_by = ? "
                f"WHERE id = ? AND revoked_at IS NULL AND {self._ADMIN}",
                (stamp, admin, int(entitlement_id), admin))
            if cursor.rowcount == 0:
                return False
            self._cache_tier(conn, owner[0][0], stamp)
            return True

    def admin_set_role(self, email: str, member: str, role: str, on: bool) -> bool:
        """
        An administrator names or removes a coach or an administrator. An
        administrator cannot remove their own role, so the platform always keeps one.
        """
        if role not in P.ROLES:
            raise ValueError("unknown role")
        admin, member = _email(email), _email(member)
        if not on and role == P.ADMIN and admin == member:
            return False
        stamp = _now()
        with self._write() as conn:
            if not conn.execute(f"SELECT 1 WHERE {self._ADMIN}", (admin,)).fetchall():
                return False
            if not conn.execute("SELECT 1 FROM users WHERE email = ?", (member,)).fetchall():
                return False
            if on:
                conn.execute("INSERT INTO user_roles (user_email, role, granted_by, created_at) VALUES (?, ?, ?, ?) "
                             "ON CONFLICT (user_email, role) DO NOTHING", (member, role, admin, stamp))
            else:
                conn.execute("DELETE FROM user_roles WHERE user_email = ? AND role = ?", (member, role))
            if role == P.COACH:
                conn.execute("UPDATE users SET role = ?, updated_at = ? WHERE email = ?",
                             ("coach" if on else "", stamp, member))
            return True

    def set_display_name(self, email: str, name: str | None) -> None:
        """The name shown on the member's pages; empty clears it. Trimmed to 60 characters."""
        name = " ".join((name or "").split())[:60] or None
        with self._write() as conn:
            conn.execute("UPDATE users SET display_name = ?, updated_at = ? WHERE email = ?",
                         (name, _now(), _email(email)))

    def get_user(self, email: str) -> dict | None:
        rows = self._read("SELECT * FROM users WHERE email = ?", (_email(email),))
        return dict(rows[0]) if rows else None

    def list_users(self) -> list[dict]:
        """Everyone with a row. The deployment decides who may ask."""
        return [dict(r) for r in
                self._read("SELECT * FROM users ORDER BY email")]

    def _ensure_user(self, conn, email: str) -> None:
        """
        Create the user row a write is about to reference.

        Every user-owned table has a foreign key to `users`, so a portfolio or a
        trade written for someone with no row would be rejected. Calling this on
        the write paths means a caller never has to remember to register a user
        first — and it is what makes the cascade in `delete_user` complete,
        because a row that was never registered could not be cascaded from.
        """
        stamp = _now()
        conn.execute(
            """INSERT INTO users (email, tier, created_at, updated_at)
               VALUES (?, 'free', ?, ?) ON CONFLICT(email) DO NOTHING""",
            (email, stamp, stamp),
        )

    def delete_user(self, email: str) -> dict:
        """
        Remove a person and everything filed under them.

        Counted before deleting and reported back, because "your data has been
        deleted" is a claim that should be able to say how much. The children go
        through the foreign keys' cascade; they are also deleted explicitly, so
        the guarantee does not depend on a pragma being set on this connection.
        """
        email = _email(email)
        if not email:
            return {"portfolios": 0, "snapshots": 0, "accounts": 0, "trades": 0,
                    "workspace": 0}

        counts = {
            "portfolios": self._count(
                "SELECT COUNT(*) AS n FROM portfolios WHERE user_email = ?", email),
            "snapshots": self._count(
                "SELECT COUNT(*) AS n FROM snapshots WHERE portfolio_id IN "
                "(SELECT id FROM portfolios WHERE user_email = ?)", email),
            "accounts": self._count(
                "SELECT COUNT(*) AS n FROM trading_accounts WHERE user_email = ?", email),
            "trades": self._count(
                "SELECT COUNT(*) AS n FROM trades WHERE user_email = ?", email),
            "sessions": self._count(
                "SELECT COUNT(*) AS n FROM sessions WHERE user_email = ?", email),
            "workspace": self._count(
                "SELECT COUNT(*) AS n FROM workspace WHERE user_email = ?", email),
            "lesson_progress": self._count(
                "SELECT COUNT(*) AS n FROM lesson_progress WHERE user_email = ?", email),
            "quiz_attempts": self._count(
                "SELECT COUNT(*) AS n FROM quiz_attempts WHERE user_email = ?", email),
            "journal_entries": self._count(
                "SELECT COUNT(*) AS n FROM journal_entries WHERE user_email = ?", email),
            "trading_plans": self._count(
                "SELECT COUNT(*) AS n FROM trading_plans WHERE user_email = ?", email),
            "trade_reviews": self._count(
                "SELECT COUNT(*) AS n FROM trade_reviews WHERE user_email = ?", email),
            "entitlements": self._count(
                "SELECT COUNT(*) AS n FROM entitlements WHERE user_email = ?", email),
            "user_roles": self._count(
                "SELECT COUNT(*) AS n FROM user_roles WHERE user_email = ?", email),
            "newsletter": self._count(
                "SELECT COUNT(*) AS n FROM newsletter WHERE email = ?", email),
            "cohort_members": self._count(
                "SELECT COUNT(*) AS n FROM cohort_members WHERE user_email = ?", email),
            "support_requests": self._count(
                "SELECT COUNT(*) AS n FROM support_requests WHERE user_email = ?", email),
            "signup_sources": self._count(
                "SELECT COUNT(*) AS n FROM signup_sources WHERE user_email = ?", email),
        }

        with self._write() as conn:
            conn.execute(
                "DELETE FROM snapshots WHERE portfolio_id IN "
                "(SELECT id FROM portfolios WHERE user_email = ?)", (email,))
            conn.execute("DELETE FROM sessions WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM trades WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM trading_accounts WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM portfolios WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM workspace WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM lesson_progress WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM quiz_attempts WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM journal_entries WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM trading_plans WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM trade_reviews WHERE user_email = ?", (email,))
            # A departing coach's address leaves the answers they gave, which stay with
            # the members who received them.
            conn.execute("UPDATE trade_reviews SET coach_email = NULL WHERE coach_email = ?", (email,))
            # The same for the sessions a departing coach wrote: they stay with the room.
            conn.execute("UPDATE market_sessions SET author_email = NULL WHERE author_email = ?", (email,))
            conn.execute("DELETE FROM entitlements WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM user_roles WHERE user_email = ?", (email,))
            # A departing administrator's address leaves the grants they made: the
            # trace keeps what was done and when, no longer by whom.
            conn.execute("UPDATE entitlements SET reference = 'compte supprimé' WHERE reference = ?", (email,))
            conn.execute("UPDATE entitlements SET revoked_by = 'compte supprimé' WHERE revoked_by = ?", (email,))
            conn.execute("UPDATE user_roles SET granted_by = 'compte supprimé' WHERE granted_by = ?", (email,))
            conn.execute("DELETE FROM account_tokens WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM newsletter WHERE email = ?", (email,))
            conn.execute("DELETE FROM cohort_members WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM support_requests WHERE user_email = ?", (email,))
            conn.execute("DELETE FROM signup_sources WHERE user_email = ?", (email,))
            # What a departing coach or administrator wrote or set up stays, without their address.
            conn.execute("UPDATE support_requests SET answered_by = NULL WHERE answered_by = ?", (email,))
            conn.execute("UPDATE cohorts SET created_by = NULL WHERE created_by = ?", (email,))
            conn.execute("UPDATE cohort_members SET added_by = NULL WHERE added_by = ?", (email,))
            conn.execute("DELETE FROM users WHERE email = ?", (email,))
        return counts

    def export_user(self, email: str) -> dict:
        """
        Everything stored for one person, as plain JSON-able data.

        Portability, and the shape the API will serve. Reads through the same
        user-scoped methods as everything else, so an export cannot reach
        further than the app can.
        """
        email = _email(email)
        return {
            # The credential is not personal data the person needs back, and an
            # export is a file that gets e-mailed and left in download folders.
            "user": {k: v for k, v in (self.get_user(email) or {}).items()
                     if k not in ("password_hash", "failed_logins", "locked_until")} or None,
            "portfolios": [
                {
                    "portfolio": asdict(portfolio),
                    "snapshots": [asdict(s) for s in self.list_snapshots(
                        email, portfolio.id, limit=10_000)],
                }
                for portfolio in self.list_portfolios(email)
            ],
            "workspace": (lambda w: asdict(w) if w else None)(
                self.load_workspace(email)),
            "accounts": [asdict(a) for a in self.list_accounts(email)],
            "trades": [t.to_dict() for t in self.list_trades(email)],
            "lesson_progress": self.completed_lessons(email),
            "quiz_attempts": self.quiz_attempts(email, limit=100_000),
            "journal_entries": self.journal_entries(email, limit=100_000),
            "trading_plan": self.get_trading_plan(email),
            "trade_reviews": self.review_requests(email),
            "entitlements": self.entitlements(email),
            "roles": sorted(self.roles(email)),
            "newsletter": self.newsletter(email),
            "cohorts": self.my_cohorts(email),
            "support_requests": self.support_requests(email),
            "signup_source": self.signup_source(email),
            # Where and when the account is signed in; never the token or its fingerprint.
            "sessions": [{k: row.get(k) for k in ("created_at", "last_seen_at", "expires_at", "label")}
                         for row in self.list_sessions(email)],
            # What the person wrote as a coach: sessions of the trading room and answers to reviews.
            "authored": self.authored_by(email),
            "schema_version": SCHEMA_VERSION,
        }

    def authored_by(self, email: str) -> dict:
        """
        Content written by this person as a coach: the trading room's sessions
        and the answers given to review requests (the answer only, not the
        member's trade). Part of the export; on deletion it stays, without the
        author's address (`delete_user`).
        """
        email = _email(email)
        sessions = [self._market_row(r) for r in self._read(
            "SELECT id, session_date, title, access, status, content, review, published_at, updated_at "
            "FROM market_sessions WHERE author_email = ? ORDER BY session_date", (email,))]
        answers = [{"id": r["id"], "answered_at": r["answered_at"],
                    "feedback": None if r["feedback"] is None else json.loads(r["feedback"])}
                   for r in self._read("SELECT id, answered_at, feedback FROM trade_reviews WHERE coach_email = ? "
                                       "ORDER BY answered_at", (email,))]
        support = [{"id": r["id"], "answered_at": r["answered_at"], "answer": r["answer"]}
                   for r in self._read("SELECT id, answered_at, answer FROM support_requests WHERE answered_by = ? "
                                       "ORDER BY answered_at", (email,))]
        return {"market_sessions": sessions, "review_answers": answers, "support_answers": support}

    # ── Academy ──────────────────────────────────────────────────────────────
    #
    # Every query below is scoped by `user_email`, like the rest of the store.
    # There is no method that reads progress or attempts across users.

    def mark_lesson_complete(self, user_email: str, course_id: str, lesson_id: str,
                             *, version: int = 1) -> None:
        user_email = _email(user_email)
        if not user_email or not course_id or not lesson_id:
            raise ValueError("user_email, course_id and lesson_id are all required")
        stamp = _now()
        with self._write() as conn:
            self._ensure_user(conn, user_email)
            conn.execute(
                """INSERT INTO lesson_progress
                     (user_email, course_id, lesson_id, lesson_version, completed_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(user_email, course_id, lesson_id) DO UPDATE SET
                     lesson_version = excluded.lesson_version,
                     completed_at = excluded.completed_at""",
                (user_email, course_id, lesson_id, int(version), stamp),
            )

    def unmark_lesson(self, user_email: str, course_id: str, lesson_id: str) -> None:
        with self._write() as conn:
            conn.execute(
                "DELETE FROM lesson_progress WHERE user_email = ? AND course_id = ? "
                "AND lesson_id = ?", (_email(user_email), course_id, lesson_id))

    def completed_lessons(self, user_email: str,
                          course_id: str | None = None) -> list[dict]:
        sql = ("SELECT course_id, lesson_id, lesson_version, completed_at "
               "FROM lesson_progress WHERE user_email = ?")
        params: tuple = (_email(user_email),)
        if course_id:
            sql += " AND course_id = ?"
            params += (course_id,)
        sql += " ORDER BY completed_at, lesson_id"
        return [dict(r) for r in self._read(sql, params)]

    def record_quiz_attempt(self, user_email: str, quiz_id: str, *, version: int,
                            correct: int, total: int, passed: bool,
                            responses: dict) -> int:
        user_email = _email(user_email)
        if not user_email or not quiz_id:
            raise ValueError("user_email and quiz_id are required")
        stamp = _now()
        with self._write() as conn:
            self._ensure_user(conn, user_email)
            cursor = conn.execute(
                """INSERT INTO quiz_attempts
                     (user_email, quiz_id, quiz_version, correct, total, passed,
                      responses, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   RETURNING id""",
                (user_email, quiz_id, int(version), int(correct), int(total),
                 1 if passed else 0, json.dumps(responses, sort_keys=True), stamp),
            )
            return int(cursor.fetchone()[0])

    def quiz_attempts(self, user_email: str, quiz_id: str | None = None, *,
                      limit: int = 50) -> list[dict]:
        """Newest first. `responses` is decoded; `passed` is a bool."""
        sql = "SELECT * FROM quiz_attempts WHERE user_email = ?"
        params: tuple = (_email(user_email),)
        if quiz_id:
            sql += " AND quiz_id = ?"
            params += (quiz_id,)
        sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params += (int(limit),)
        rows = []
        for row in self._read(sql, params):
            item = dict(row)
            item["responses"] = json.loads(item["responses"] or "{}")
            item["passed"] = bool(item["passed"])
            rows.append(item)
        return rows

    # ── Reflection journal ───────────────────────────────────────────────────
    #
    # Private notes. Every read and every delete carries the owner's address in
    # its WHERE clause: an entry id on its own never reaches a row, so a guessed
    # or replayed id from another member matches nothing.

    def add_journal_entry(self, user_email: str, *, kind: str, body: str,
                          mood: int | None = None, prompt: str = "",
                          checks: list[str] | None = None) -> int:
        user_email = _email(user_email)
        if not user_email:
            raise ValueError("user_email is required")
        with self._write() as conn:
            self._ensure_user(conn, user_email)
            cursor = conn.execute(
                """INSERT INTO journal_entries
                     (user_email, kind, mood, prompt, body, checks, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   RETURNING id""",
                (user_email, kind, mood, prompt or "", body,
                 None if checks is None else json.dumps(list(checks)), _now()),
            )
            return int(cursor.fetchone()[0])

    def journal_entries(self, user_email: str, kind: str | None = None, *,
                        limit: int = 200) -> list[dict]:
        """Newest first. `checks` is decoded: a list, or None when no routine was offered."""
        sql = ("SELECT id, kind, mood, prompt, body, checks, created_at FROM journal_entries "
               "WHERE user_email = ?")
        params: tuple = (_email(user_email),)
        if kind:
            sql += " AND kind = ?"
            params += (kind,)
        sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params += (int(limit),)
        rows = []
        for row in self._read(sql, params):
            item = dict(row)
            item["checks"] = None if item["checks"] is None else json.loads(item["checks"])
            rows.append(item)
        return rows

    def delete_journal_entry(self, user_email: str, entry_id: int) -> bool:
        with self._write() as conn:
            cursor = conn.execute(
                "DELETE FROM journal_entries WHERE user_email = ? AND id = ?",
                (_email(user_email), int(entry_id)))
            return cursor.rowcount > 0

    # ── Trading plan and review requests ─────────────────────────────────────
    #
    # The plan and the requests are a member's own, read through methods scoped
    # by their address like everything else. The one exception is deliberate and
    # narrow: a coach reads the requests members chose to send, and nothing
    # else. Those methods check the role inside the same query, so a caller that
    # forgot to check it still gets nothing.

    def get_trading_plan(self, user_email: str) -> dict | None:
        rows = self._read("SELECT plan FROM trading_plans WHERE user_email = ?",
                          (_email(user_email),))
        return json.loads(rows[0]["plan"]) if rows else None

    def save_trading_plan(self, user_email: str, plan: dict) -> None:
        user_email = _email(user_email)
        if not user_email:
            raise ValueError("user_email is required")
        with self._write() as conn:
            self._ensure_user(conn, user_email)
            conn.execute(
                """INSERT INTO trading_plans (user_email, plan, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(user_email) DO UPDATE SET plan = excluded.plan,
                     updated_at = excluded.updated_at""",
                (user_email, json.dumps(plan, ensure_ascii=False), _now()))

    def create_review_request(self, user_email: str, *, trade_id: str, trade: dict,
                              auto_review: dict, plan: dict | None, question: str) -> int:
        user_email = _email(user_email)
        if not user_email:
            raise ValueError("user_email is required")
        with self._write() as conn:
            self._ensure_user(conn, user_email)
            cursor = conn.execute(
                """INSERT INTO trade_reviews
                     (user_email, trade_id, trade, auto_review, plan, question, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                   RETURNING id""",
                (user_email, str(trade_id), json.dumps(trade, ensure_ascii=False, default=str),
                 json.dumps(auto_review, ensure_ascii=False),
                 None if plan is None else json.dumps(plan, ensure_ascii=False), question, _now()))
            return int(cursor.fetchone()[0])

    @staticmethod
    def _review_row(row) -> dict:
        item = dict(row)
        for key in ("trade", "auto_review", "plan", "feedback"):
            if key in item:
                item[key] = None if item[key] is None else json.loads(item[key])
        return item

    def review_requests(self, user_email: str) -> list[dict]:
        """A member's own requests, newest first. The coach's address is not returned."""
        rows = self._read(
            "SELECT id, trade_id, trade, auto_review, plan, question, status, feedback, "
            "created_at, answered_at, seen_at FROM trade_reviews WHERE user_email = ? "
            "ORDER BY created_at DESC, id DESC", (_email(user_email),))
        return [self._review_row(r) for r in rows]

    def count_review_requests(self, user_email: str, since: str) -> int:
        return self._count("SELECT COUNT(*) AS n FROM trade_reviews WHERE user_email = ? "
                           "AND created_at >= ?", _email(user_email), since)

    def open_review_for_trade(self, user_email: str, trade_id: str) -> int | None:
        rows = self._read("SELECT id FROM trade_reviews WHERE user_email = ? AND trade_id = ? "
                          "AND status = 'pending'", (_email(user_email), str(trade_id)))
        return int(rows[0]["id"]) if rows else None

    def withdraw_review_request(self, user_email: str, review_id: int) -> bool:
        """A member may withdraw a request the coach has not answered yet."""
        with self._write() as conn:
            cursor = conn.execute(
                "DELETE FROM trade_reviews WHERE user_email = ? AND id = ? AND status = 'pending'",
                (_email(user_email), int(review_id)))
            return cursor.rowcount > 0

    def mark_review_seen(self, user_email: str, review_id: int) -> None:
        with self._write() as conn:
            conn.execute("UPDATE trade_reviews SET seen_at = ? WHERE user_email = ? AND id = ? "
                         "AND status = 'answered' AND seen_at IS NULL",
                         (_now(), _email(user_email), int(review_id)))

    def unseen_reviews(self, user_email: str) -> int:
        return self._count("SELECT COUNT(*) AS n FROM trade_reviews WHERE user_email = ? "
                           "AND status = 'answered' AND seen_at IS NULL", _email(user_email))

    # Coaches.

    def set_role(self, email: str, role: str) -> bool:
        """The coach role on or off (`''`), kept for the earlier callers; `grant_role` is the general form."""
        if role not in ("", "coach"):
            raise ValueError("role must be '' or 'coach'")
        if role:
            return self.grant_role(email, P.COACH)
        if not self.get_user(email):
            return False
        self.revoke_role(email, P.COACH)
        return True

    def is_coach(self, email: str) -> bool:
        return P.COACH in self.roles(email)

    def pending_reviews(self, email: str) -> int:
        """How many requests wait for an answer, for a coach (the sidebar's count); 0 for anyone else."""
        return self._count("SELECT COUNT(*) AS n FROM trade_reviews WHERE status = 'pending' AND EXISTS "
                           "(SELECT 1 FROM user_roles c WHERE c.user_email = ? AND c.role = 'coach')", _email(email))

    def coach_queue(self, email: str, status: str = "pending", *, limit: int = 200) -> list[dict]:
        """
        The requests members sent, for the coach `email`: oldest pending first, or the latest
        answered. Empty for anyone who is not a coach. The member is returned as an address only so the
        page can derive a pseudonym; the page never shows it.
        """
        if status not in ("pending", "answered"):
            raise ValueError("unknown status")
        order = "r.created_at ASC, r.id ASC" if status == "pending" else "r.answered_at DESC, r.id DESC"
        rows = self._read(
            "SELECT r.id, r.user_email, r.trade_id, r.trade, r.auto_review, r.plan, r.question, "
            "r.status, r.feedback, r.created_at, r.answered_at FROM trade_reviews r "
            "WHERE r.status = ? AND EXISTS (SELECT 1 FROM user_roles c WHERE c.user_email = ? AND c.role = 'coach') "
            f"ORDER BY {order} LIMIT ?", (status, _email(email), int(limit)))
        return [self._review_row(r) for r in rows]

    def answer_review(self, email: str, review_id: int, feedback: dict) -> bool:
        """Record a coach's answer once. False when not a coach, or already answered."""
        coach_email = _email(email)
        with self._write() as conn:
            cursor = conn.execute(
                "UPDATE trade_reviews SET status = 'answered', coach_email = ?, feedback = ?, "
                "answered_at = ? WHERE id = ? AND status = 'pending' "
                "AND EXISTS (SELECT 1 FROM user_roles c WHERE c.user_email = ? AND c.role = 'coach')",
                (coach_email, json.dumps(feedback, ensure_ascii=False), _now(), int(review_id),
                 coach_email))
            return cursor.rowcount > 0

    # ── Trading room ─────────────────────────────────────────────────────────
    #
    # Sessions are written by coaches and read by everyone at the access level of
    # each session; the access check itself is the page's (academy.access). Every
    # write is gated on the coach role in SQL, like the review queue.

    _COACH = "EXISTS (SELECT 1 FROM user_roles c WHERE c.user_email = ? AND c.role = 'coach')"

    @staticmethod
    def _market_row(row) -> dict:
        item = dict(row)
        for key in ("content", "review"):
            if key in item:
                item[key] = None if item[key] is None else json.loads(item[key])
        return item

    def save_market_session(self, email: str, session: dict, session_id: int | None = None) -> int | None:
        """
        Create a draft, or update a session, from `platform.market.clean_session()`.
        None when `email` is not a coach or the session does not exist. Editing a
        published session keeps it published.
        """
        coach = _email(email)
        stamp = _now()
        content = json.dumps(session["content"], ensure_ascii=False)
        with self._write() as conn:
            if session_id is None:
                cursor = conn.execute(
                    "INSERT INTO market_sessions (author_email, session_date, title, access, status, content, "
                    f"created_at, updated_at) SELECT ?, ?, ?, ?, 'draft', ?, ?, ? WHERE {self._COACH} RETURNING id",
                    (coach, session["session_date"], session["title"], session["access"], content, stamp, stamp, coach))
                row = cursor.fetchone()
                return int(row[0]) if row else None
            cursor = conn.execute(
                "UPDATE market_sessions SET session_date = ?, title = ?, access = ?, content = ?, updated_at = ? "
                f"WHERE id = ? AND {self._COACH}",
                (session["session_date"], session["title"], session["access"], content, stamp, int(session_id), coach))
            return int(session_id) if cursor.rowcount else None

    def publish_market_session(self, email: str, session_id: int) -> list[str] | None:
        """
        Publish a draft. Returns the reasons it cannot be published (empty on
        success), or None when `email` is not a coach or there is no such draft.
        The check is `platform.market.publishable`, applied to what is stored.
        """
        from ..platform import market as M

        row = self.market_session(int(session_id), coach=email)
        if row is None or row["status"] != "draft":
            return None
        problems = M.publishable({"title": row["title"], "content": row["content"]})
        if problems:
            return problems
        with self._write() as conn:
            cursor = conn.execute(
                "UPDATE market_sessions SET status = 'published', published_at = ?, updated_at = ? "
                f"WHERE id = ? AND status = 'draft' AND {self._COACH}",
                (_now(), _now(), int(session_id), _email(email)))
            return [] if cursor.rowcount else None

    def unpublish_market_session(self, email: str, session_id: int) -> bool:
        with self._write() as conn:
            cursor = conn.execute(
                "UPDATE market_sessions SET status = 'draft', updated_at = ? "
                f"WHERE id = ? AND status = 'published' AND {self._COACH}",
                (_now(), int(session_id), _email(email)))
            return cursor.rowcount > 0

    def review_market_session(self, email: str, session_id: int, review: dict) -> bool:
        """Record or replace the review of a published session, from `platform.market.clean_review()`."""
        with self._write() as conn:
            cursor = conn.execute(
                "UPDATE market_sessions SET review = ?, reviewed_at = ?, updated_at = ? "
                f"WHERE id = ? AND status = 'published' AND {self._COACH}",
                (json.dumps(review, ensure_ascii=False), _now(), _now(), int(session_id), _email(email)))
            return cursor.rowcount > 0

    def delete_market_session(self, email: str, session_id: int) -> bool:
        """A draft can be deleted; a published session is unpublished first."""
        with self._write() as conn:
            cursor = conn.execute(
                f"DELETE FROM market_sessions WHERE id = ? AND status = 'draft' AND {self._COACH}",
                (int(session_id), _email(email)))
            return cursor.rowcount > 0

    def market_sessions(self, *, limit: int = 60) -> list[dict]:
        """Published sessions, the most recent date first. Drafts never appear here."""
        rows = self._read(
            "SELECT id, session_date, title, access, status, content, review, published_at, reviewed_at "
            "FROM market_sessions WHERE status = 'published' ORDER BY session_date DESC, id DESC LIMIT ?",
            (int(limit),))
        return [self._market_row(r) for r in rows]

    def market_drafts(self, email: str) -> list[dict]:
        """Drafts, for a coach; empty for anyone else."""
        rows = self._read(
            "SELECT id, session_date, title, access, status, content, review, updated_at FROM market_sessions "
            f"WHERE status = 'draft' AND {self._COACH} ORDER BY session_date DESC, id DESC", (_email(email),))
        return [self._market_row(r) for r in rows]

    def market_session(self, session_id: int, *, coach: str | None = None) -> dict | None:
        """
        One session. A draft is returned only to a coach; the author's address is
        returned to a coach only.
        """
        is_coach = bool(coach) and self.is_coach(coach)
        columns = ("id, session_date, title, access, status, content, review, published_at, reviewed_at, "
                   "updated_at" + (", author_email" if is_coach else ""))
        status = "" if is_coach else " AND status = 'published'"
        rows = self._read(f"SELECT {columns} FROM market_sessions WHERE id = ?{status}", (int(session_id),))
        return self._market_row(rows[0]) if rows else None

    # ── Accompaniment: cohorts, workshops, requests ──────────────────────────
    #
    # Administrators manage cohorts and workshops, coaches answer requests;
    # each write checks the role in its own SQL. A member reads the workshops
    # of the open cohorts they belong to only while their premium level is
    # active, checked in the same query.

    def _premium_sql(self, column: str) -> str:
        return (f"EXISTS (SELECT 1 FROM entitlements e WHERE e.user_email = {column} AND e.revoked_at IS NULL "
                "AND e.starts_at <= ? AND (e.ends_at IS NULL OR e.ends_at > ?))")

    def admin_cohorts(self, email: str) -> list[dict] | None:
        if not self.is_admin(email):
            return None
        return [dict(r) for r in self._read(
            "SELECT c.id, c.title, c.summary, c.starts_on, c.ends_on, c.status, "
            "(SELECT COUNT(*) FROM cohort_members m WHERE m.cohort_id = c.id) AS members, "
            "(SELECT COUNT(*) FROM workshops w WHERE w.cohort_id = c.id AND w.status = 'scheduled') AS workshops "
            "FROM cohorts c ORDER BY c.status, c.starts_on DESC, c.id DESC")]

    def create_cohort(self, email: str, cohort: dict) -> int | None:
        """From `platform.cohorts.clean_cohort`. None when `email` is not an administrator."""
        admin, stamp = _email(email), _now()
        with self._write() as conn:
            row = conn.execute(
                "INSERT INTO cohorts (title, summary, starts_on, ends_on, status, created_by, created_at, updated_at) "
                f"SELECT ?, ?, ?, ?, 'open', ?, ?, ? WHERE {self._ADMIN} RETURNING id",
                (cohort["title"], cohort["summary"], cohort["starts_on"], cohort["ends_on"], admin, stamp, stamp,
                 admin)).fetchone()
            return int(row[0]) if row else None

    def update_cohort(self, email: str, cohort_id: int, cohort: dict, *, status: str = "open") -> bool:
        if status not in ("open", "closed"):
            raise ValueError("unknown status")
        with self._write() as conn:
            cursor = conn.execute(
                "UPDATE cohorts SET title = ?, summary = ?, starts_on = ?, ends_on = ?, status = ?, updated_at = ? "
                f"WHERE id = ? AND {self._ADMIN}",
                (cohort["title"], cohort["summary"], cohort["starts_on"], cohort["ends_on"], status, _now(),
                 int(cohort_id), _email(email)))
            return cursor.rowcount > 0

    def cohort_roster(self, email: str, cohort_id: int) -> list[dict] | None:
        """The members of a cohort with their level, for an administrator."""
        if not self.is_admin(email):
            return None
        stamp = _now()
        return [dict(r) for r in self._read(
            "SELECT m.user_email AS email, u.display_name, m.created_at, "
            f"CASE WHEN {self._premium_sql('m.user_email')} THEN 1 ELSE 0 END AS premium "
            "FROM cohort_members m JOIN users u ON u.email = m.user_email WHERE m.cohort_id = ? "
            "ORDER BY m.created_at", (stamp, stamp, int(cohort_id)))]

    def add_to_cohort(self, email: str, cohort_id: int, member: str) -> bool:
        admin = _email(email)
        with self._write() as conn:
            cursor = conn.execute(
                "INSERT INTO cohort_members (cohort_id, user_email, added_by, created_at) "
                f"SELECT ?, ?, ?, ? WHERE {self._ADMIN} AND EXISTS (SELECT 1 FROM users u WHERE u.email = ?) "
                "AND EXISTS (SELECT 1 FROM cohorts c WHERE c.id = ?) ON CONFLICT (cohort_id, user_email) DO NOTHING",
                (int(cohort_id), _email(member), admin, _now(), admin, _email(member), int(cohort_id)))
            return cursor.rowcount > 0

    def remove_from_cohort(self, email: str, cohort_id: int, member: str) -> bool:
        with self._write() as conn:
            cursor = conn.execute(f"DELETE FROM cohort_members WHERE cohort_id = ? AND user_email = ? AND {self._ADMIN}",
                                  (int(cohort_id), _email(member), _email(email)))
            return cursor.rowcount > 0

    def save_workshop(self, email: str, cohort_id: int, workshop: dict, workshop_id: int | None = None) -> int | None:
        """From `platform.cohorts.clean_workshop`; creates or updates. None when not an administrator."""
        admin, stamp = _email(email), _now()
        values = (workshop["title"], workshop["summary"], workshop["starts_at"], workshop["duration_minutes"],
                  workshop["place"])
        with self._write() as conn:
            if workshop_id is None:
                row = conn.execute(
                    "INSERT INTO workshops (cohort_id, title, summary, starts_at, duration_minutes, place, status, "
                    f"created_at, updated_at) SELECT ?, ?, ?, ?, ?, ?, 'scheduled', ?, ? WHERE {self._ADMIN} "
                    "AND EXISTS (SELECT 1 FROM cohorts c WHERE c.id = ?) RETURNING id",
                    (int(cohort_id), *values, stamp, stamp, admin, int(cohort_id))).fetchone()
                return int(row[0]) if row else None
            cursor = conn.execute(
                "UPDATE workshops SET title = ?, summary = ?, starts_at = ?, duration_minutes = ?, place = ?, "
                f"updated_at = ? WHERE id = ? AND cohort_id = ? AND {self._ADMIN}",
                (*values, stamp, int(workshop_id), int(cohort_id), admin))
            return int(workshop_id) if cursor.rowcount else None

    def set_workshop_status(self, email: str, workshop_id: int, status: str) -> bool:
        if status not in ("scheduled", "cancelled"):
            raise ValueError("unknown status")
        with self._write() as conn:
            cursor = conn.execute(f"UPDATE workshops SET status = ?, updated_at = ? WHERE id = ? AND {self._ADMIN}",
                                  (status, _now(), int(workshop_id), _email(email)))
            return cursor.rowcount > 0

    def admin_workshops(self, email: str, cohort_id: int) -> list[dict] | None:
        if not self.is_admin(email):
            return None
        return [dict(r) for r in self._read(
            "SELECT * FROM workshops WHERE cohort_id = ? ORDER BY starts_at", (int(cohort_id),))]

    def my_cohorts(self, email: str) -> list[dict]:
        """The open cohorts this member belongs to (title, dates), whatever their level."""
        return [dict(r) for r in self._read(
            "SELECT c.id, c.title, c.summary, c.starts_on, c.ends_on FROM cohorts c JOIN cohort_members m "
            "ON m.cohort_id = c.id WHERE m.user_email = ? AND c.status = 'open' ORDER BY c.starts_on",
            (_email(email),))]

    def my_workshops(self, email: str) -> list[dict]:
        """
        The workshops of the member's open cohorts, place included; empty unless
        the member belongs to the cohort and their premium level is active.
        """
        email, stamp = _email(email), _now()
        return [dict(r) for r in self._read(
            "SELECT w.id, w.cohort_id, c.title AS cohort, w.title, w.summary, w.starts_at, w.duration_minutes, "
            "w.place, w.status FROM workshops w JOIN cohorts c ON c.id = w.cohort_id "
            "JOIN cohort_members m ON m.cohort_id = w.cohort_id AND m.user_email = ? "
            f"WHERE c.status = 'open' AND {self._premium_sql('m.user_email')} ORDER BY w.starts_at",
            (email, stamp, stamp))]

    def create_support_request(self, email: str, request: dict) -> int | None:
        """
        From `platform.support.clean_request`. None unless the member is
        accompanied (premium active, in an open cohort), checked in SQL.
        """
        email, stamp = _email(email), _now()
        with self._write() as conn:
            row = conn.execute(
                "INSERT INTO support_requests (user_email, topic, question, status, created_at) "
                "SELECT ?, ?, ?, 'pending', ? WHERE EXISTS (SELECT 1 FROM cohort_members m JOIN cohorts c "
                f"ON c.id = m.cohort_id WHERE m.user_email = ? AND c.status = 'open') AND {self._premium_sql('?')} "
                "RETURNING id",
                (email, request["topic"], request["question"], stamp, email, email, stamp, stamp)).fetchone()
            return int(row[0]) if row else None

    def support_requests(self, email: str) -> list[dict]:
        """The member's own requests, the latest first; never who answered."""
        return [dict(r) for r in self._read(
            "SELECT id, topic, question, status, answer, created_at, answered_at, seen_at FROM support_requests "
            "WHERE user_email = ? ORDER BY created_at DESC, id DESC", (_email(email),))]

    def count_support_requests(self, email: str, since: str) -> int:
        return self._count("SELECT COUNT(*) AS n FROM support_requests WHERE user_email = ? AND created_at >= ?",
                           _email(email), since)

    def mark_support_seen(self, email: str, request_id: int) -> None:
        with self._write() as conn:
            conn.execute("UPDATE support_requests SET seen_at = ? WHERE id = ? AND user_email = ? "
                         "AND status = 'answered' AND seen_at IS NULL", (_now(), int(request_id), _email(email)))

    def unseen_support(self, email: str) -> int:
        return self._count("SELECT COUNT(*) AS n FROM support_requests WHERE user_email = ? "
                           "AND status = 'answered' AND seen_at IS NULL", _email(email))

    def support_queue(self, email: str, status: str = "pending", *, limit: int = 200) -> list[dict]:
        """Requests for a coach, oldest pending first; the address only to derive a pseudonym. Empty otherwise."""
        if status not in ("pending", "answered"):
            raise ValueError("unknown status")
        order = "r.created_at ASC, r.id ASC" if status == "pending" else "r.answered_at DESC, r.id DESC"
        return [dict(r) for r in self._read(
            "SELECT r.id, r.user_email, r.topic, r.question, r.status, r.answer, r.created_at, r.answered_at "
            "FROM support_requests r WHERE r.status = ? AND EXISTS (SELECT 1 FROM user_roles c "
            f"WHERE c.user_email = ? AND c.role = 'coach') ORDER BY {order} LIMIT ?",
            (status, _email(email), int(limit)))]

    def coach_counts(self, email: str) -> tuple[int, int]:
        """(pending trade reviews, pending accompaniment requests) for a coach, in one query; (0, 0) otherwise."""
        rows = self._read(
            "SELECT (SELECT COUNT(*) FROM trade_reviews WHERE status = 'pending') AS reviews, "
            "(SELECT COUNT(*) FROM support_requests WHERE status = 'pending') AS support "
            "WHERE EXISTS (SELECT 1 FROM user_roles c WHERE c.user_email = ? AND c.role = 'coach')", (_email(email),))
        return (int(rows[0][0]), int(rows[0][1])) if rows else (0, 0)

    def pending_support(self, email: str) -> int:
        return self._count("SELECT COUNT(*) AS n FROM support_requests WHERE status = 'pending' AND EXISTS "
                           "(SELECT 1 FROM user_roles c WHERE c.user_email = ? AND c.role = 'coach')", _email(email))

    def answer_support(self, email: str, request_id: int, answer: str) -> bool:
        """A coach answers once. False when not a coach, or already answered."""
        coach = _email(email)
        with self._write() as conn:
            cursor = conn.execute(
                "UPDATE support_requests SET status = 'answered', answer = ?, answered_by = ?, answered_at = ? "
                "WHERE id = ? AND status = 'pending' AND EXISTS (SELECT 1 FROM user_roles c "
                "WHERE c.user_email = ? AND c.role = 'coach')", (answer, coach, _now(), int(request_id), coach))
            return cursor.rowcount > 0

    # ── Statistics ───────────────────────────────────────────────────────────

    def record_visit(self, day: str, landing: str, source: str = "") -> None:
        """One more visit for this day, landing page and source. No member data."""
        with self._write() as conn:
            conn.execute("INSERT INTO visits (day, landing, source, n) VALUES (?, ?, ?, 1) "
                         "ON CONFLICT (day, landing, source) DO UPDATE SET n = visits.n + 1",
                         (day, landing[:60], source[:40]))

    def set_signup_source(self, email: str, *, source: str, medium: str, campaign: str, landing: str) -> None:
        """Where the account came from, recorded once at sign-up; a later call changes nothing."""
        with self._write() as conn:
            self._ensure_user(conn, _email(email))
            conn.execute("INSERT INTO signup_sources (user_email, source, medium, campaign, landing, created_at) "
                         "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (user_email) DO NOTHING",
                         (_email(email), source, medium, campaign, landing[:60], _now()))

    def signup_source(self, email: str) -> dict | None:
        rows = self._read("SELECT source, medium, campaign, landing, created_at FROM signup_sources "
                          "WHERE user_email = ?", (_email(email),))
        return dict(rows[0]) if rows else None

    def admin_stats(self, email: str, *, since: str) -> dict | None:
        """
        Counts for the administrator's statistics page, over the window from
        `since` (an ISO date), and in total. Counts only: no address leaves here.
        """
        if not self.is_admin(email):
            return None
        stamp = _now()
        premium = self._premium_sql("u.email")
        accompanied = ("EXISTS (SELECT 1 FROM cohort_members m JOIN cohorts c ON c.id = m.cohort_id "
                       "WHERE m.user_email = u.email AND c.status = 'open')")
        window = "u.created_at >= ?"

        def count(where: str, *params) -> int:
            return self._count(f"SELECT COUNT(*) AS n FROM users u WHERE {where}", *params)

        def grouped(sql: str, *params) -> list[dict]:
            return [dict(r) for r in self._read(sql, params)]

        return {
            "visits": self._count("SELECT COALESCE(SUM(n), 0) AS n FROM visits WHERE day >= ?", since[:10]),
            "signups": count(window, since),
            "verified": count(f"{window} AND u.email_verified_at IS NOT NULL", since),
            "premium": count(f"{window} AND {premium}", since, stamp, stamp),
            "accompanied": count(f"{window} AND {premium} AND {accompanied}", since, stamp, stamp),
            "total": {
                "members": count("1 = 1"),
                "premium": count(premium, stamp, stamp),
                "accompanied": count(f"{premium} AND {accompanied}", stamp, stamp),
                "active_30": count("u.last_login_at >= ?", since),
                "newsletter": self._count("SELECT COUNT(*) AS n FROM newsletter WHERE status = 'confirmed'"),
            },
            "by_month": grouped("SELECT SUBSTR(created_at, 1, 7) AS month, COUNT(*) AS n FROM users "
                                "GROUP BY SUBSTR(created_at, 1, 7) ORDER BY month DESC LIMIT 12"),
            "by_source": grouped("SELECT COALESCE(NULLIF(s.source, ''), 'direct') AS source, COUNT(*) AS n "
                                 "FROM users u LEFT JOIN signup_sources s ON s.user_email = u.email "
                                 "WHERE u.created_at >= ? GROUP BY COALESCE(NULLIF(s.source, ''), 'direct') "
                                 "ORDER BY n DESC", since),
            "visits_by_day": grouped("SELECT day, SUM(n) AS n FROM visits WHERE day >= ? GROUP BY day ORDER BY day",
                                     since[:10]),
            "visits_by_landing": grouped("SELECT landing, SUM(n) AS n FROM visits WHERE day >= ? GROUP BY landing "
                                         "ORDER BY n DESC LIMIT 10", since[:10]),
        }

    # ── Newsletter ───────────────────────────────────────────────────────────
    #
    # Keyed by address (a visitor can subscribe). Active once confirmed by the
    # e-mailed link; the wording accepted and its date are the proof of consent.
    # The service around these methods is `platform.newsletter`.

    _NEWSLETTER_PUBLIC = ("email, status, source, consent_text, consent_at, confirmed_at, unsubscribed_at, "
                          "provider_synced_at, created_at")

    def newsletter(self, email: str) -> dict | None:
        """One address's subscription, without its token fingerprints."""
        rows = self._read(f"SELECT {self._NEWSLETTER_PUBLIC} FROM newsletter WHERE email = ?", (_email(email),))
        return dict(rows[0]) if rows else None

    def newsletter_request(self, email: str, *, consent_text: str, source: str, confirm_fingerprint: str,
                           unsubscribe_fingerprint: str, expires_at: str, resend_after: str) -> str:
        """
        Record a request to subscribe, awaiting confirmation. Returns « pending »
        when a confirmation should be sent, « confirmed » when the address
        already is (nothing to send), « throttled » when a link was sent after
        `resend_after` (nothing sent, so the form cannot flood a mailbox).
        """
        email = _email(email)
        stamp = _now()
        with self._write() as conn:
            rows = conn.execute("SELECT status, confirm_sent_at FROM newsletter WHERE email = ?", (email,)).fetchall()
            if rows and rows[0][0] == "confirmed":
                return "confirmed"
            if rows and rows[0][0] == "pending" and (rows[0][1] or "") > resend_after:
                return "throttled"
            if rows:
                conn.execute(
                    "UPDATE newsletter SET status = 'pending', source = ?, consent_text = ?, consent_at = ?, "
                    "confirm_fingerprint = ?, confirm_expires_at = ?, confirm_sent_at = ?, confirmed_at = NULL, "
                    "unsubscribe_fingerprint = ?, unsubscribed_at = NULL, updated_at = ? WHERE email = ?",
                    (source, consent_text, stamp, confirm_fingerprint, expires_at, stamp, unsubscribe_fingerprint,
                     stamp, email))
            else:
                conn.execute(
                    "INSERT INTO newsletter (email, status, source, consent_text, consent_at, confirm_fingerprint, "
                    "confirm_expires_at, confirm_sent_at, unsubscribe_fingerprint, created_at, updated_at) "
                    "VALUES (?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (email, source, consent_text, stamp, confirm_fingerprint, expires_at, stamp,
                     unsubscribe_fingerprint, stamp, stamp))
            return "pending"

    def newsletter_confirm(self, fingerprint: str) -> str | None:
        """
        Confirm by the e-mailed link's fingerprint: the address, or None for an
        unknown, used or expired link. The link works once.
        """
        stamp = _now()
        with self._write() as conn:
            rows = conn.execute("SELECT email FROM newsletter WHERE confirm_fingerprint = ? AND status = 'pending' "
                                "AND confirm_expires_at > ?", (fingerprint, stamp)).fetchall()
            if not rows:
                return None
            conn.execute("UPDATE newsletter SET status = 'confirmed', confirmed_at = ?, confirm_fingerprint = NULL, "
                         "updated_at = ? WHERE email = ?", (stamp, stamp, rows[0][0]))
            return rows[0][0]

    def newsletter_stop(self, fingerprint: str) -> str | None:
        """One-click unsubscribe by the link every message carries: the address, or None."""
        stamp = _now()
        with self._write() as conn:
            rows = conn.execute("SELECT email FROM newsletter WHERE unsubscribe_fingerprint = ?",
                                (fingerprint,)).fetchall()
            if not rows:
                return None
            conn.execute("UPDATE newsletter SET status = 'unsubscribed', unsubscribed_at = COALESCE("
                         "CASE WHEN status = 'unsubscribed' THEN unsubscribed_at END, ?), confirm_fingerprint = NULL, "
                         "updated_at = ? WHERE email = ?", (stamp, stamp, rows[0][0]))
            return rows[0][0]

    def newsletter_unsubscribe(self, email: str) -> bool:
        """From the member's account page."""
        stamp = _now()
        with self._write() as conn:
            cursor = conn.execute("UPDATE newsletter SET status = 'unsubscribed', unsubscribed_at = ?, "
                                  "confirm_fingerprint = NULL, updated_at = ? WHERE email = ? "
                                  "AND status != 'unsubscribed'", (stamp, stamp, _email(email)))
            return cursor.rowcount > 0

    def newsletter_synced(self, email: str) -> None:
        with self._write() as conn:
            conn.execute("UPDATE newsletter SET provider_synced_at = ? WHERE email = ?", (_now(), _email(email)))

    def newsletter_subscribers(self, email: str) -> list[dict] | None:
        """The confirmed addresses with their proof of consent, for an administrator; None otherwise."""
        if not self.is_admin(email):
            return None
        return [dict(r) for r in self._read(
            "SELECT email, source, consent_at, confirmed_at FROM newsletter WHERE status = 'confirmed' "
            "ORDER BY confirmed_at")]

    # ── Single-use account tokens ────────────────────────────────────────────

    def create_account_token(self, email: str, fingerprint: str, *, purpose: str,
                             expires_at: str) -> None:
        """
        Record a new token and retire every unused one of the same purpose.

        Only the latest link sent works: asking twice for a reset must not leave
        two live links in someone's mailbox.
        """
        email = _email(email)
        stamp = _now()
        with self._write() as conn:
            self._ensure_user(conn, email)
            conn.execute(
                "UPDATE account_tokens SET used_at = ? WHERE user_email = ? "
                "AND purpose = ? AND used_at IS NULL", (stamp, email, purpose))
            conn.execute(
                "INSERT INTO account_tokens (fingerprint, user_email, purpose, "
                "created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                (fingerprint, email, purpose, stamp, expires_at))

    def account_token(self, fingerprint: str, purpose: str) -> dict | None:
        """The token row if it exists for this purpose. Expiry is the caller's call."""
        rows = self._read(
            "SELECT * FROM account_tokens WHERE fingerprint = ? AND purpose = ?",
            (fingerprint, purpose))
        return dict(rows[0]) if rows else None

    def use_account_token(self, fingerprint: str) -> bool:
        """Mark a token used. False if it was already used: a link works once."""
        with self._write() as conn:
            cursor = conn.execute(
                "UPDATE account_tokens SET used_at = ? WHERE fingerprint = ? "
                "AND used_at IS NULL", (_now(), fingerprint))
            return cursor.rowcount == 1

    def set_email_verified(self, email: str) -> None:
        with self._write() as conn:
            conn.execute("UPDATE users SET email_verified_at = ?, updated_at = ? "
                         "WHERE email = ?", (_now(), _now(), _email(email)))

    # ── Credentials ──────────────────────────────────────────────────────────

    def set_password_hash(self, email: str, password_hash: str | None) -> None:
        """
        Store a credential. `None` removes it, leaving an account with no
        password — which is a real state, not a missing one.
        """
        email = _email(email)
        stamp = _now()
        with self._write() as conn:
            self._ensure_user(conn, email)
            conn.execute(
                "UPDATE users SET password_hash = ?, updated_at = ?, "
                "failed_logins = 0, locked_until = NULL WHERE email = ?",
                (password_hash, stamp, email),
            )

    def credential(self, email: str) -> dict | None:
        """
        What sign-in needs, and nothing else.

        A narrow read rather than `get_user`: the password hash should travel to
        as few places as possible, and a method that returns it should be
        obvious at the call site.
        """
        rows = self._read(
            "SELECT email, password_hash, failed_logins, locked_until "
            "FROM users WHERE email = ?", (_email(email),))
        return dict(rows[0]) if rows else None

    def record_login_success(self, email: str) -> None:
        with self._write() as conn:
            conn.execute(
                "UPDATE users SET last_login_at = ?, failed_logins = 0, "
                "locked_until = NULL, updated_at = ? WHERE email = ?",
                (_now(), _now(), _email(email)),
            )

    def reset_login_failures(self, email: str) -> None:
        with self._write() as conn:
            conn.execute("UPDATE users SET failed_logins = 0, locked_until = NULL, updated_at = ? WHERE email = ?",
                         (_now(), _email(email)))

    def count_account_tokens(self, email: str, purpose: str, *, since: str) -> int:
        """Tokens of this purpose created for an address since a moment: how many e-mails were asked for."""
        return self._count("SELECT COUNT(*) AS n FROM account_tokens WHERE user_email = ? AND purpose = ? "
                           "AND created_at >= ?", _email(email), purpose, since)

    def record_login_failure(self, email: str, *,
                             locked_until: str | None = None) -> int:
        """Count a failed attempt and return the new total."""
        email = _email(email)
        with self._write() as conn:
            conn.execute(
                "UPDATE users SET failed_logins = failed_logins + 1, "
                "locked_until = COALESCE(?, locked_until), updated_at = ? "
                "WHERE email = ?",
                (locked_until, _now(), email),
            )
        return self._count(
            "SELECT failed_logins AS n FROM users WHERE email = ?", email)

    # ── Sessions ─────────────────────────────────────────────────────────────

    def create_session(self, email: str, fingerprint: str, *,
                       expires_at: str, label: str | None = None, login: bool = False) -> None:
        """
        Record a new session. `login` also records a successful sign-in (last
        login, failed attempts reset) in the same transaction: one commit
        instead of two on the way in.
        """
        email = _email(email)
        stamp = _now()
        with self._write() as conn:
            self._ensure_user(conn, email)
            if login:
                conn.execute("UPDATE users SET last_login_at = ?, failed_logins = 0, locked_until = NULL, "
                             "updated_at = ? WHERE email = ?", (stamp, stamp, email))
            conn.execute(
                """INSERT INTO sessions
                     (fingerprint, user_email, created_at, expires_at,
                      last_seen_at, label)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(fingerprint) DO UPDATE SET
                     expires_at = excluded.expires_at,
                     last_seen_at = excluded.last_seen_at""",
                (fingerprint, email, stamp, expires_at, stamp, label),
            )

    def session(self, fingerprint: str) -> dict | None:
        """
        A session row, or None when it does not exist or has expired.

        Expiry is applied in the query. A caller that fetched the row and
        checked the date itself would be one forgotten comparison away from
        honouring a session forever, and the comparison would have to be
        repeated at every call site.
        """
        rows = self._read(
            "SELECT s.*, CASE WHEN u.password_hash IS NULL THEN 0 ELSE 1 END AS has_password "
            "FROM sessions s JOIN users u ON u.email = s.user_email "
            "WHERE s.fingerprint = ? AND s.expires_at > ?",
            (fingerprint or "", _now()),
        )
        return dict(rows[0]) if rows else None

    def touch_session(self, fingerprint: str, *, expires_at: str | None = None) -> None:
        """Mark a session as seen, and optionally slide its expiry forward."""
        with self._write() as conn:
            if expires_at:
                conn.execute(
                    "UPDATE sessions SET last_seen_at = ?, expires_at = ? "
                    "WHERE fingerprint = ?", (_now(), expires_at, fingerprint))
            else:
                conn.execute(
                    "UPDATE sessions SET last_seen_at = ? WHERE fingerprint = ?",
                    (_now(), fingerprint))

    def revoke_session(self, fingerprint: str) -> None:
        with self._write() as conn:
            conn.execute("DELETE FROM sessions WHERE fingerprint = ?", (fingerprint,))

    def revoke_sessions(self, user_email: str) -> int:
        """Sign a user out everywhere. What a password change must do."""
        with self._write() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE user_email = ?",
                                  (_email(user_email),))
            return cursor.rowcount

    def list_sessions(self, user_email: str) -> list[dict]:
        return [dict(r) for r in self._read(
            "SELECT * FROM sessions WHERE user_email = ? AND expires_at > ? "
            "ORDER BY created_at DESC",
            (_email(user_email), _now()))]

    def purge_expired_sessions(self) -> int:
        with self._write() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE expires_at <= ?",
                                  (_now(),))
            return cursor.rowcount

    def _count(self, sql: str, *params) -> int:
        rows = self._read(sql, tuple(params))
        return int(rows[0]["n"]) if rows else 0

    # ── The working portfolio ────────────────────────────────────────────────

    def save_workspace(self, user_email: str, holdings: dict, *,
                       mode: str = "simulation", base_currency: str = "USD",
                       profile: str = "balanced", period: str | None = None,
                       quantities: dict | None = None,
                       total_value: float | None = None,
                       manual_prices: dict | None = None,
                       portfolio_id: int | None = None,
                       portfolio_name: str | None = None) -> None:
        """
        Write down what someone is working on, so a restart does not lose it.

        One row per person, replaced in place. Called on every real change to the
        allocation rather than behind a button: the whole point is that there is
        nothing to remember to press. Empty holdings are stored as an empty
        workspace rather than rejected — clearing the portfolio is a change worth
        persisting too, and the alternative is that emptying it silently restores
        the old one on the next visit.
        """
        user_email = _email(user_email)
        if not user_email:
            return

        with self._write() as conn:
            self._ensure_user(conn, user_email)
            conn.execute(
                """INSERT INTO workspace
                     (user_email, holdings, mode, base_currency, profile, period,
                      quantities, total_value, manual_prices,
                      portfolio_id, portfolio_name, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(user_email) DO UPDATE SET
                     holdings = excluded.holdings,
                     mode = excluded.mode,
                     base_currency = excluded.base_currency,
                     profile = excluded.profile,
                     period = excluded.period,
                     quantities = excluded.quantities,
                     total_value = excluded.total_value,
                     manual_prices = excluded.manual_prices,
                     portfolio_id = excluded.portfolio_id,
                     portfolio_name = excluded.portfolio_name,
                     updated_at = excluded.updated_at""",
                (user_email, json.dumps(_jsonable(holdings or {})), mode,
                 (base_currency or "USD").upper(), profile, period,
                 json.dumps(_jsonable(quantities or {})),
                 float(total_value) if total_value is not None else None,
                 json.dumps(_jsonable(manual_prices or {})),
                 int(portfolio_id) if portfolio_id is not None else None,
                 portfolio_name, _now()),
            )

    def load_workspace(self, user_email: str) -> Workspace | None:
        """What this person was last working on, or None if they never have."""
        user_email = _email(user_email)
        if not user_email:
            return None
        rows = self._read("SELECT * FROM workspace WHERE user_email = ?", (user_email,))
        return _to_workspace(rows[0]) if rows else None

    def clear_workspace(self, user_email: str) -> None:
        user_email = _email(user_email)
        if not user_email:
            return
        with self._write() as conn:
            conn.execute("DELETE FROM workspace WHERE user_email = ?", (user_email,))

    # ── Portfolios ───────────────────────────────────────────────────────────

    def save_portfolio(self, user_email: str, name: str, holdings: dict, *,
                       mode: str = "simulation", currency: str = "$",
                       notes: str | None = None,
                       client_name: str | None = None) -> int:
        """
        Create or overwrite a portfolio by (user, name).

        Overwriting rather than erroring on a duplicate name is deliberate: the
        save button is how people iterate, and a name is how they mean to identify
        one book across those iterations.
        """
        user_email = _email(user_email)
        name = name.strip()
        if not user_email or not name or not holdings:
            raise ValueError("user_email, name and holdings are all required")

        now = _now()
        payload = json.dumps(holdings)
        with self._write() as conn:
            self._ensure_user(conn, user_email)
            cursor = conn.execute(
                """INSERT INTO portfolios
                     (user_email, name, holdings, mode, currency, notes, client_name,
                      created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(user_email, name) DO UPDATE SET
                     holdings = excluded.holdings,
                     mode = excluded.mode,
                     currency = excluded.currency,
                     notes = excluded.notes,
                     client_name = excluded.client_name,
                     updated_at = excluded.updated_at
                   RETURNING id""",
                (user_email, name, payload, mode, currency, notes, client_name, now, now),
            )
            # `RETURNING id` rather than `lastrowid`: Postgres has no such
            # attribute, and SQLite has supported RETURNING since 3.35 — so one
            # statement now works on both instead of the call site branching on
            # which database it is talking to.
            returned = cursor.fetchone()
            if returned is not None:
                return int(returned[0])
        row = self._read(
            "SELECT id FROM portfolios WHERE user_email = ? AND name = ?",
            (user_email, name),
        )
        return int(row[0]["id"]) if row else -1

    def list_portfolios(self, user_email: str, *,
                        clients_only: bool = False) -> list[Portfolio]:
        sql = "SELECT * FROM portfolios WHERE user_email = ?"
        if clients_only:
            sql += " AND client_name IS NOT NULL AND client_name != ''"
        sql += " ORDER BY updated_at DESC"
        return [_to_portfolio(r) for r in self._read(sql, (_email(user_email),))]

    def get_portfolio(self, user_email: str, portfolio_id: int) -> Portfolio | None:
        """
        One portfolio, and only if it belongs to this user.

        Every method from here down takes the owner. An integer primary key is
        guessable, so a lookup by id alone returns whatever row holds that id —
        which on a shared database means one person's holdings answering another
        person's request. The user is not an optional extra argument for that
        reason: a parameter with a default is exactly how this comes back.
        """
        rows = self._read(
            "SELECT * FROM portfolios WHERE id = ? AND user_email = ?",
            (int(portfolio_id), _email(user_email)),
        )
        return _to_portfolio(rows[0]) if rows else None

    def rename_portfolio(self, user_email: str, portfolio_id: int,
                         new_name: str) -> bool:
        """True when a row was renamed — False when it was not this user's."""
        with self._write() as conn:
            cursor = conn.execute(
                "UPDATE portfolios SET name = ?, updated_at = ? "
                "WHERE id = ? AND user_email = ?",
                (new_name.strip(), _now(), int(portfolio_id), _email(user_email)),
            )
            return cursor.rowcount > 0

    def delete_portfolio(self, user_email: str, portfolio_id: int) -> bool:
        """
        Delete a portfolio and its snapshots. False when it was not this user's.

        The snapshots go through the foreign key's cascade on a version 2
        database. The explicit delete stays for one written down reason: a
        connection that lost `PRAGMA foreign_keys = ON` would otherwise leave
        orphaned snapshots behind, and an orphan carrying holdings is the kind
        of residue a deletion is supposed to remove.
        """
        email = _email(user_email)
        with self._write() as conn:
            conn.execute(
                "DELETE FROM snapshots WHERE portfolio_id IN "
                "(SELECT id FROM portfolios WHERE id = ? AND user_email = ?)",
                (int(portfolio_id), email),
            )
            cursor = conn.execute(
                "DELETE FROM portfolios WHERE id = ? AND user_email = ?",
                (int(portfolio_id), email),
            )
            return cursor.rowcount > 0

    # ── Snapshots ────────────────────────────────────────────────────────────
    #
    # Snapshots carry no user column; they reach their owner through the
    # portfolio. Every query below joins through it rather than trusting the
    # caller's id, so a snapshot cannot be read, written or deleted across the
    # boundary even when its own id is known.

    def add_snapshot(self, user_email: str, portfolio_id: int, *,
                     total_value: float | None, weights: dict,
                     metrics: dict) -> int:
        """
        Record the portfolio's state at a point in time.

        Snapshots are what make the history view possible: the app can recompute
        metrics from prices at any time, but it cannot recover what the allocation
        *was* last month unless that was written down.

        Returns -1 when the portfolio is not this user's, rather than writing a
        snapshot onto someone else's history.
        """
        if self.get_portfolio(user_email, portfolio_id) is None:
            return -1
        with self._write() as conn:
            cursor = conn.execute(
                """INSERT INTO snapshots (portfolio_id, taken_at, total_value, weights, metrics)
                   VALUES (?, ?, ?, ?, ?)
                   RETURNING id""",
                (int(portfolio_id), _now(),
                 float(total_value) if total_value is not None else None,
                 json.dumps(weights), json.dumps(_jsonable(metrics))),
            )
            returned = cursor.fetchone()
            return int(returned[0]) if returned is not None else -1

    def list_snapshots(self, user_email: str, portfolio_id: int,
                       limit: int = 100) -> list[Snapshot]:
        rows = self._read(
            """SELECT s.* FROM snapshots s
               JOIN portfolios p ON p.id = s.portfolio_id
               WHERE s.portfolio_id = ? AND p.user_email = ?
               ORDER BY s.taken_at DESC LIMIT ?""",
            (int(portfolio_id), _email(user_email), int(limit)),
        )
        return [_to_snapshot(r) for r in rows]

    def latest_snapshot(self, user_email: str, portfolio_id: int) -> Snapshot | None:
        snapshots = self.list_snapshots(user_email, portfolio_id, limit=1)
        return snapshots[0] if snapshots else None

    def delete_snapshot(self, user_email: str, snapshot_id: int) -> bool:
        with self._write() as conn:
            cursor = conn.execute(
                """DELETE FROM snapshots WHERE id = ? AND portfolio_id IN
                   (SELECT id FROM portfolios WHERE user_email = ?)""",
                (int(snapshot_id), _email(user_email)),
            )
            return cursor.rowcount > 0

    # ── Aggregates ───────────────────────────────────────────────────────────

    def portfolio_summaries(self, user_email: str, *,
                            clients_only: bool = False) -> list[dict]:
        """
        Every portfolio with its most recent snapshot attached.

        This is what the advisor view renders from, so it is one query plus one
        lookup per portfolio rather than a join — the row counts here are small,
        and keeping it simple keeps it portable to another database.
        """
        out = []
        for portfolio in self.list_portfolios(user_email, clients_only=clients_only):
            snapshot = self.latest_snapshot(user_email, portfolio.id)
            out.append({
                "portfolio": portfolio,
                "snapshot": snapshot,
                "metrics": snapshot.metrics if snapshot else {},
                "total_value": snapshot.total_value if snapshot else None,
                "n_snapshots": len(
                    self.list_snapshots(user_email, portfolio.id, limit=500)),
            })
        return out

    # ── Trading accounts ─────────────────────────────────────────────────────

    def upsert_account(self, user_email: str, account_id: str, name: str, *,
                       broker: str | None = None, currency: str = "USD") -> None:
        user_email = _email(user_email)
        now = _now()
        with self._write() as conn:
            self._ensure_user(conn, user_email)
            conn.execute(
                """INSERT INTO trading_accounts
                     (id, user_email, name, broker, currency, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(user_email, id) DO UPDATE SET
                     name = excluded.name,
                     broker = excluded.broker,
                     currency = excluded.currency,
                     updated_at = excluded.updated_at""",
                (str(account_id), user_email, name, broker, currency, now, now),
            )

    def list_accounts(self, user_email: str) -> list[TradingAccount]:
        rows = self._read(
            "SELECT * FROM trading_accounts WHERE user_email = ? ORDER BY name",
            (_email(user_email),),
        )
        return [_to_account(r) for r in rows]

    def delete_account(self, user_email: str, account_id: str) -> None:
        """Removes the account and every trade filed under it."""
        user_email = _email(user_email)
        with self._write() as conn:
            conn.execute("DELETE FROM trades WHERE user_email = ? AND account_id = ?",
                         (user_email, str(account_id)))
            conn.execute("DELETE FROM trading_accounts WHERE user_email = ? AND id = ?",
                         (user_email, str(account_id)))

    def record_sync(self, user_email: str, account_id: str, *,
                    trades: int = 0, at: str | None = None) -> None:
        """
        Mark when an account was last pulled from, and how much came back.

        Stored rather than inferred. The obvious proxy — the newest close in the
        journal — is wrong in the one case that matters: a sync that found
        nothing leaves it unchanged, so the next window reaches further back
        every time nothing happens, and a quiet fortnight turns every sync into
        a full re-download.
        """
        with self._write() as conn:
            conn.execute(
                """UPDATE trading_accounts
                   SET last_synced_at = ?, last_sync_trades = ?, updated_at = ?
                   WHERE user_email = ? AND id = ?""",
                (at or _now(), int(trades), _now(),
                 _email(user_email), str(account_id)),
            )

    def last_synced_at(self, user_email: str, account_id: str) -> str | None:
        rows = self._read(
            "SELECT last_synced_at FROM trading_accounts "
            "WHERE user_email = ? AND id = ?",
            (_email(user_email), str(account_id)),
        )
        return rows[0]["last_synced_at"] if rows else None

    # ── Trades ───────────────────────────────────────────────────────────────

    def save_trade(self, user_email: str, trade) -> None:
        self.save_trades(user_email, [trade])

    def save_trades(self, user_email: str, trades) -> int:
        """
        Upsert a batch of trades, returning how many were written.

        One statement per batch rather than per trade: a broker sync arrives with
        thousands at once, and a commit per row turns a two-second import into a
        two-minute one.

        `created_at` is preserved on conflict so a re-sync does not rewrite when a
        trade was first seen — that timestamp is the only record of it.
        """
        user_email = _email(user_email)
        if not user_email:
            raise ValueError("user_email is required")

        now = _now()
        rows = [trade_to_row(t, user_email, now) for t in trades]
        if not rows:
            return 0

        columns = ", ".join(TRADE_COLUMNS)
        placeholders = ", ".join("?" for _ in TRADE_COLUMNS)
        updates = ", ".join(
            f"{c} = excluded.{c}" for c in TRADE_COLUMNS
            if c not in ("id", "user_email", "created_at")
        )
        sql = (f"INSERT INTO trades ({columns}) VALUES ({placeholders}) "
               f"ON CONFLICT(user_email, id) DO UPDATE SET {updates}")

        with self._write() as conn:
            self._ensure_user(conn, user_email)
            conn.executemany(sql, [[row[c] for c in TRADE_COLUMNS] for row in rows])
        return len(rows)

    def list_trades(self, user_email: str, *, account_id: str | None = None,
                    symbol: str | None = None, limit: int | None = None,
                    updated_since: str | None = None) -> list:
        """
        Trades for a user, newest close first.

        Open trades have a null `closed_at` and sort last under `DESC`; that is
        deliberate — a list of results should lead with results.

        `updated_since` is what makes an incremental sync possible: a client
        that already holds the journal asks only for what has changed since it
        last looked. It filters on `updated_at`, not `closed_at`, because a
        trade annotated today is a change the client needs even though it closed
        in March.
        """
        sql = "SELECT * FROM trades WHERE user_email = ?"
        params: list = [_email(user_email)]
        if account_id:
            sql += " AND account_id = ?"
            params.append(str(account_id))
        if symbol:
            sql += " AND symbol = ?"
            params.append(symbol)
        if updated_since:
            sql += " AND updated_at > ?"
            params.append(str(updated_since))
        sql += " ORDER BY closed_at DESC, opened_at DESC"
        if limit:
            sql += " LIMIT ?"
            params.append(int(limit))
        return [row_to_trade(r) for r in self._read(sql, tuple(params))]

    def get_trade(self, user_email: str, trade_id: str):
        rows = self._read(
            "SELECT * FROM trades WHERE user_email = ? AND id = ?",
            (_email(user_email), str(trade_id)),
        )
        return row_to_trade(rows[0]) if rows else None

    def delete_trade(self, user_email: str, trade_id: str) -> None:
        with self._write() as conn:
            conn.execute("DELETE FROM trades WHERE user_email = ? AND id = ?",
                         (_email(user_email), str(trade_id)))

    def delete_all_trades(self, user_email: str, account_id: str | None = None) -> int:
        user_email = _email(user_email)
        with self._write() as conn:
            if account_id:
                cursor = conn.execute(
                    "DELETE FROM trades WHERE user_email = ? AND account_id = ?",
                    (user_email, str(account_id)))
            else:
                cursor = conn.execute("DELETE FROM trades WHERE user_email = ?",
                                      (user_email,))
            return cursor.rowcount

    def count_trades(self, user_email: str, account_id: str | None = None) -> int:
        sql = "SELECT COUNT(*) AS n FROM trades WHERE user_email = ?"
        params: list = [_email(user_email)]
        if account_id:
            sql += " AND account_id = ?"
            params.append(str(account_id))
        rows = self._read(sql, tuple(params))
        return int(rows[0]["n"]) if rows else 0

    def trades_version(self, user_email: str) -> str:
        """
        A short string that changes whenever this user's journal changes.

        The API turns it into an `ETag`, so a phone reopening the app gets a 304
        and re-downloads nothing. Built from the row count and the newest
        `updated_at`: a save bumps the timestamp, a delete bumps the count, and
        the pair moves for either.

        Hashed here rather than in the route, because the route layer is not
        allowed to compute anything — and because a caller should not have to
        know what the version is made of to compare two of them.
        """
        import hashlib

        rows = self._read(
            "SELECT COUNT(*) AS n, COALESCE(MAX(updated_at), '') AS newest "
            "FROM trades WHERE user_email = ?", (_email(user_email),))
        if not rows:
            return "empty"
        digest = hashlib.sha256(
            f"{rows[0]['n']}:{rows[0]['newest']}".encode()).hexdigest()
        return digest[:16]

    def trade_symbols(self, user_email: str) -> list[str]:
        rows = self._read(
            "SELECT DISTINCT symbol FROM trades WHERE user_email = ? ORDER BY symbol",
            (_email(user_email),),
        )
        return [r["symbol"] for r in rows]
