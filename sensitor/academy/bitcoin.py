"""
Bitcoin's issuance, computed from the protocol rules.

Pure integer arithmetic in satoshis, the way the reference implementation does
it: the block subsidy starts at 50 BTC and is halved, by a right shift, every
210 000 blocks; after 64 halvings it is zero. Summing it gives the supply
schedule, and the familiar total of 20 999 999.9769 BTC falls out of the
rounding, not out of a constant.

Heights are facts of the protocol. Dates are not: past halving dates are the
recorded dates of the halving blocks, and future ones are estimates at the
target spacing of ten minutes per block, flagged as such wherever they are used.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

COIN = 100_000_000                  # satoshis per bitcoin
INITIAL_SUBSIDY = 50 * COIN
HALVING_INTERVAL = 210_000          # blocks
TARGET_SPACING_MINUTES = 10
LAST_HALVING_EPOCH = 64             # from here the shifted subsidy is zero

GENESIS_DATE = _dt.date(2009, 1, 3)
# Dates on which the halving blocks were mined (210 000, 420 000, 630 000, 840 000).
RECORDED_HALVINGS = {
    1: _dt.date(2012, 11, 28),
    2: _dt.date(2016, 7, 9),
    3: _dt.date(2020, 5, 11),
    4: _dt.date(2024, 4, 20),
}


def block_subsidy(height: int) -> int:
    """New satoshis created by the block at `height`, before fees."""
    if height < 0:
        raise ValueError("a block height cannot be negative")
    halvings = height // HALVING_INTERVAL
    if halvings >= LAST_HALVING_EPOCH:
        return 0
    return INITIAL_SUBSIDY >> halvings


def supply_after(height: int) -> int:
    """Satoshis issued by blocks 0 to `height` included, genesis block counted."""
    if height < 0:
        raise ValueError("a block height cannot be negative")
    total, start = 0, 0
    while start <= height:
        subsidy = block_subsidy(start)
        if subsidy == 0:
            break
        end = min(height, start + HALVING_INTERVAL - 1)
        total += subsidy * (end - start + 1)
        start += HALVING_INTERVAL
    return total


def total_supply() -> int:
    """Every satoshi the schedule will ever issue."""
    return supply_after(LAST_HALVING_EPOCH * HALVING_INTERVAL)


@dataclass(frozen=True)
class Epoch:
    number: int                 # 0 for the first 210 000 blocks
    start_height: int
    subsidy: int                # satoshis per block during the epoch
    supply_at_end: int          # satoshis issued once the epoch is over
    start_date: _dt.date
    estimated: bool             # True when `start_date` is a projection

    @property
    def share_issued(self) -> float:
        return self.supply_at_end / total_supply()


def epoch_start_date(number: int) -> tuple[_dt.date, bool]:
    """(date, estimated) for the first block of epoch `number`."""
    if number == 0:
        return GENESIS_DATE, False
    if number in RECORDED_HALVINGS:
        return RECORDED_HALVINGS[number], False
    last = max(RECORDED_HALVINGS)
    minutes = (number - last) * HALVING_INTERVAL * TARGET_SPACING_MINUTES
    return RECORDED_HALVINGS[last] + _dt.timedelta(minutes=minutes), True


def epochs(count: int = 34) -> list[Epoch]:
    """The first `count` epochs; 33 of them carry a non-zero subsidy."""
    out = []
    for n in range(count):
        start = n * HALVING_INTERVAL
        date, estimated = epoch_start_date(n)
        out.append(Epoch(n, start, block_subsidy(start), supply_after(start + HALVING_INTERVAL - 1),
                         date, estimated))
    return out


def issuance_rows() -> list[dict]:
    """
    One row per halving epoch, for the issuance chart: the year the epoch
    starts, the subsidy and the supply at its end, in bitcoins.
    """
    return [{"annee": round(e.start_date.year + (e.start_date.timetuple().tm_yday - 1) / 365.25, 2),
             "date": e.start_date.isoformat(),
             "recompense": e.subsidy / COIN,
             "offre": e.supply_at_end / COIN,
             "part": round(e.share_issued * 100, 4),
             "estimation": e.estimated}
            for e in epochs(13)]
