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
import math
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


# =============================================================================
# DIFFICULTY, SECURITY AND FEES
# =============================================================================

RETARGET_INTERVAL = 2016            # blocks between two difficulty adjustments
RETARGET_SECONDS = RETARGET_INTERVAL * TARGET_SPACING_MINUTES * 60   # two weeks
MAX_RETARGET_FACTOR = 4


def retarget(difficulty: float, actual_seconds: float) -> float:
    """
    The difficulty after an adjustment period that took `actual_seconds`. Faster
    than two weeks, difficulty rises; slower, it falls. The protocol caps the
    change at a factor of four in either direction.
    """
    if difficulty <= 0 or actual_seconds <= 0:
        raise ValueError("difficulty and duration must be positive")
    bounded = min(max(actual_seconds, RETARGET_SECONDS / MAX_RETARGET_FACTOR),
                  RETARGET_SECONDS * MAX_RETARGET_FACTOR)
    return difficulty * RETARGET_SECONDS / bounded


def minutes_between_blocks(hashrate_share: float) -> float:
    """How long, on average, a miner holding this share of the hashrate waits for a block."""
    if not 0 < hashrate_share <= 1:
        raise ValueError("a share is between 0 (excluded) and 1")
    return TARGET_SPACING_MINUTES / hashrate_share


def attacker_success(q: float, z: int) -> float:
    """
    The probability that an attacker with a share `q` of the hashrate ever
    catches up from `z` blocks behind, as computed in section 11 of the white
    paper (Nakamoto, 2008). With q of one half or more, the attacker always
    succeeds eventually.
    """
    if not 0 <= q < 1 or z < 0:
        raise ValueError("q is between 0 and 1, z is not negative")
    p = 1 - q
    if q >= p:
        return 1.0
    lam = z * q / p
    total = 1.0
    poisson = math.exp(-lam)
    for k in range(z + 1):
        if k:
            poisson *= lam / k
        total -= poisson * (1 - (q / p) ** (z - k))
    return total


def confirmations_needed(q: float, threshold: float = 0.001) -> int:
    """The smallest number of confirmations for which the attacker's chance falls under `threshold`."""
    if q >= 0.5:
        raise ValueError("no number of confirmations protects against a majority")
    z = 0
    while attacker_success(q, z) >= threshold:
        z += 1
    return z


def catch_up_rows(shares=(0.10, 0.20, 0.30), depth: int = 24) -> list[dict]:
    """The attacker's chance after 0 to `depth` confirmations, for the chart of the security lesson."""
    return [{"confirmations": z, **{f"q{round(q * 100)}": attacker_success(q, z) for q in shares}}
            for z in range(depth + 1)]


def fee_sats(vbytes: int, sats_per_vbyte: float) -> float:
    """A transaction pays for its size, not for the amount it moves."""
    return vbytes * sats_per_vbyte


def estimated_date(from_height: int, from_date: _dt.date, target_height: int) -> _dt.date:
    """When a future block should be mined, at ten minutes per block from a known one."""
    minutes = (target_height - from_height) * TARGET_SPACING_MINUTES
    return from_date + _dt.timedelta(minutes=minutes)


# =============================================================================
# FROM BLOCK HEADERS
# =============================================================================

MAX_TARGET = 0xFFFF * 2 ** 208      # the target of difficulty 1, encoded as bits 0x1d00ffff


def target_from_bits(bits: int) -> int:
    """The target a block hash must stay under, decoded from the header's compact `bits` field."""
    exponent, mantissa = bits >> 24, bits & 0xFFFFFF
    return mantissa * 2 ** (8 * (exponent - 3))


def difficulty_from_bits(bits: int) -> float:
    """Difficulty as Bitcoin Core reports it: the difficulty-1 target divided by the block's target."""
    return MAX_TARGET / target_from_bits(bits)


def hashrate(difficulty: float, seconds_per_block: float) -> float:
    """
    The network's hashes per second implied by a difficulty and the observed
    time between blocks: each block takes difficulty × 2^32 hashes on average.
    """
    if difficulty <= 0 or seconds_per_block <= 0:
        raise ValueError("difficulty and block time must be positive")
    return difficulty * 2 ** 32 / seconds_per_block


def epoch_rows(headers: list[dict]) -> list[dict]:
    """
    One row per difficulty period, from the headers at the retarget heights
    (and the tip): the period's difficulty from its bits, its length in days,
    and the hashrate it implies, in exahashes per second.
    """
    rows = []
    for this, nxt in zip(headers, headers[1:]):
        blocks = nxt["height"] - this["height"]
        seconds = nxt["timestamp"] - this["timestamp"]
        if blocks < RETARGET_INTERVAL or seconds <= 0:
            continue                            # the open period at the tip is not complete
        diff = difficulty_from_bits(this["bits"])
        rows.append({"hauteur": this["height"],
                     "date": _dt.datetime.fromtimestamp(this["timestamp"], _dt.timezone.utc).date().isoformat(),
                     "difficulte": diff, "jours": round(seconds / 86400, 2),
                     "puissance": hashrate(diff, seconds / blocks) / 1e18})
    return rows
