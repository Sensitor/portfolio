"""
Broker synchronisation.

Takes trades from any connector and puts them in the journal. Deliberately knows
nothing about MetaTrader: it asks a source for `fetch_trades()` and hands the
result to a store, so the second broker is a new connector and no change here.

The hard requirement is that re-syncing must not duplicate or overwrite.

**Not duplicate** is handled by the trade id: a connector derives it from the
broker's own position identifier, and the store upserts on `(user_email, id)`.
Pulling the same fortnight twice leaves the same rows.

**Not overwrite** is the harder half, and it is what `_preserve_journal` exists
for. The broker knows the prices; the trader knows why they took it. A re-sync
that wrote the broker's record straight over the row would erase the setup tags,
the emotion fields, the mistakes and the notes — the whole reason a journal is
worth keeping — and it would do it silently, on a button the user thinks is
read-only. So the incoming trade contributes execution facts, the stored trade
keeps everything a human typed, and the merge is per field rather than per row.

One deliberate exception: the stop. If the broker now reports a stop for a trade
that had none, take it — that is the broker correcting the record, not a human
annotation being lost.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Fields a human fills in. Never taken from a broker, never overwritten by one.
JOURNAL_FIELDS = (
    "setups", "mistakes", "timeframe", "market_regime",
    "setup_quality", "confidence", "notes",
    "emotion_before", "emotion_during", "emotion_after", "discipline",
    "image_pre", "image_post", "image_annotated",
)

# Free-text fields a connector may fill from the order comment, but only when
# the trader has not written something better there.
SOFT_FIELDS = ("entry_reason", "exit_reason")


@dataclass
class SyncResult:
    """What a sync did, in terms a user can be shown."""

    fetched: int = 0
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    annotations_kept: int = 0
    account_id: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def wrote(self) -> int:
        return self.added + self.updated

    def summary(self, lang: str = "en") -> str:
        if lang == "fr":
            return (f"{self.fetched} trades récupérés · {self.added} ajoutés · "
                    f"{self.updated} mis à jour · {self.unchanged} inchangés")
        return (f"{self.fetched} trades fetched · {self.added} added · "
                f"{self.updated} updated · {self.unchanged} unchanged")


def _preserve_journal(incoming, existing):
    """
    Merge one broker trade onto the stored one, keeping what a human wrote.

    Returns the trade to save. The broker's execution facts win; every field in
    `JOURNAL_FIELDS` is taken from the stored row, and the two free-text reason
    fields are kept only when the stored one is non-empty.
    """
    changes = {}
    for name in JOURNAL_FIELDS:
        stored = getattr(existing, name, None)
        if stored not in (None, "", [], {}):
            changes[name] = stored
    for name in SOFT_FIELDS:
        stored = getattr(existing, name, None)
        if stored:
            changes[name] = stored

    # The broker correcting its own record is not an annotation being lost, so a
    # stop that has appeared since the last sync is accepted.
    if incoming.stop_loss is None and existing.stop_loss is not None:
        changes["stop_loss"] = existing.stop_loss
    if incoming.take_profit is None and existing.take_profit is not None:
        changes["take_profit"] = existing.take_profit

    return (incoming.annotated(**changes) if changes else incoming), bool(changes)


def _execution_matches(a, b) -> bool:
    """Whether two trades describe the same execution, to stored precision."""
    def close(x, y, tolerance=1e-9):
        if x is None or y is None:
            return x is y or x == y
        return abs(float(x) - float(y)) <= tolerance

    return (
        a.symbol == b.symbol
        and a.direction == b.direction
        and close(a.entry_price, b.entry_price)
        and close(a.exit_price, b.exit_price)
        and close(a.size, b.size)
        and close(a.gross_pnl, b.gross_pnl)
        and close(a.commission, b.commission)
        and close(a.swap, b.swap)
        and close(a.stop_loss, b.stop_loss)
        and a.opened_at == b.opened_at
        and a.closed_at == b.closed_at
    )


def merge_trades(incoming, existing) -> tuple[list, SyncResult]:
    """
    Decide what to write, without touching a database.

    Split out from `sync_trades` so the merge rules can be tested against two
    plain lists — which is where the rule that matters lives, and it should not
    need a store stood up to check it.
    """
    by_id = {t.id: t for t in existing}
    result = SyncResult(fetched=len(incoming))
    to_write = []

    for trade in incoming:
        stored = by_id.get(trade.id)
        if stored is None:
            to_write.append(trade)
            result.added += 1
            continue

        merged, kept = _preserve_journal(trade, stored)
        if kept:
            result.annotations_kept += 1
        if _execution_matches(merged, stored):
            result.unchanged += 1
            continue
        to_write.append(merged)
        result.updated += 1

    return to_write, result


def sync_trades(source, store, user_email: str, *, since: datetime,
                until: datetime | None = None,
                include_open: bool = True) -> SyncResult:
    """
    Pull from a connector into a user's journal.

    `source` is anything with `fetch_trades(since, until)`, and optionally
    `fetch_open_positions()` and `account()`. `store` is a `database.Store`.
    Nothing is written for a user_email that is empty — a journal filed under
    nobody is a journal nobody can be shown.
    """
    if not (user_email or "").strip():
        raise ValueError("user_email is required")

    account = None
    if hasattr(source, "account"):
        try:
            account = source.account()
        except Exception:                            # noqa: BLE001
            account = None

    incoming = list(source.fetch_trades(since, until))
    if include_open and hasattr(source, "fetch_open_positions"):
        incoming += list(source.fetch_open_positions())

    account_id = account.id if account is not None else None
    # Every trade the user has, not just this account's. Scoping the lookup by
    # account looks tidier and is a trap: a trade stored before the account was
    # labelled, or under a label since changed, would not be found, every
    # incoming trade would look new, and the sync would overwrite the journal
    # with the broker's bare record — losing exactly the annotations the merge
    # rule below exists to protect. The merge keys on the trade id, so the extra
    # rows cost a dict lookup and nothing else.
    existing = store.list_trades(user_email)

    to_write, result = merge_trades(incoming, existing)
    result.account_id = account_id
    result.since = since
    result.until = until

    if account is not None:
        store.upsert_account(user_email, account.id, account.name,
                             broker=account.broker, currency=account.currency)
    if to_write:
        store.save_trades(user_email, to_write)
    return result


def default_window(store=None, user_email: str = "", account_id: str | None = None,
                   *, fallback_days: int = 365,
                   overlap_days: int = 3) -> datetime:
    """
    Where an incremental sync should start.

    The last stored close, minus a few days. The overlap is not laziness: a
    position open across the boundary of the previous sync had no closing deal
    then and would never be picked up by a window that began exactly where the
    last one ended. Re-fetching a few days costs nothing, because the upsert
    makes a repeat a no-op.
    """
    latest = None
    if store is not None and user_email:
        try:
            trades = store.list_trades(user_email, account_id=account_id, limit=1)
            latest = trades[0].closed_at if trades and trades[0].closed_at else None
        except Exception:                            # noqa: BLE001
            latest = None

    if latest is None:
        return datetime.now().replace(microsecond=0) - timedelta(days=fallback_days)
    return latest - timedelta(days=overlap_days)
