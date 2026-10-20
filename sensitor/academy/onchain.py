"""
Bitcoin metrics read from the chain itself, without any price.

The inputs are facts any node reports: a block's height, timestamp, number
of transactions, size, weight, and the outputs of its coinbase transaction.
Fees follow from the protocol: what the coinbase pays minus the subsidy.
Pools are named from the tag miners write in their coinbase, when they write
one. Price-based indicators (realized price, MVRV, NUPL) are shown only on a
constructed example: their real series need a licensed price history.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Sequence

from . import bitcoin as B

MAX_WEIGHT = 4_000_000      # weight units in a block since SegWit; before it, 1 MB × 4

# Coinbase tags of the main pools, as they write them (ASCII, case-insensitive).
POOL_TAGS: tuple[tuple[str, str], ...] = (
    ("Foundry USA", r"foundry"),
    ("AntPool", r"antpool"),
    ("F2Pool", r"f2pool|\xe4\xb8\x83\xe5\xbd\xa9\xe7\xa5\x9e\xe4\xbb\x99\xe9\xb1\xbc"),
    ("ViaBTC", r"viabtc"),
    ("Binance Pool", r"binance"),
    ("MARA Pool", r"mara"),
    ("SpiderPool", r"spiderpool"),
    ("Luxor", r"luxor"),
    ("Braiins (Slush Pool)", r"/slush/|braiins"),
    ("BTC.com", r"btc\.com|btccom"),
    ("Poolin", r"poolin"),
    ("Huobi Pool", r"huobi|htpool"),
    ("OKExPool", r"okex|okpool"),
    ("SBI Crypto", r"sbicrypto|sbi crypto"),
    ("OCEAN", r"ocean"),
    ("SecPool", r"secpool"),
    ("BTC.TOP", r"btc\.top"),
    ("Bitfury", r"bitfury"),
    ("BW Pool", r"bw pool|bw\.com|bwpool"),
    ("GHash.IO", r"ghash"),
    ("BTC Guild", r"btc guild|btcguild"),
    ("Eligius", r"eligius"),
    ("KnCMiner", r"kncminer"),
    ("BTCC", r"/btcc/"),
    ("KanoPool", r"kano"),
    ("BitClub", r"bitclub"),
    ("Bitcoin.com", r"bitcoin\.com"),
    ("1THash", r"1thash"),
    ("Canoe", r"canoe"),
    ("BitMinter", r"bitminter"),
    ("58COIN", r"58coin"),
    ("DPOOL", r"dpool"),
    ("Bixin (HaoBTC)", r"haobtc|bixin"),
    ("GBMiners", r"gbminers"),
)


@dataclass(frozen=True)
class Sample:
    day: str                # YYYY-MM-DD
    height: int
    tx_count: int
    size: int               # bytes
    weight: int             # weight units
    reward: int             # satoshis paid by the coinbase
    coinbase: str = ""      # the coinbase input script, hexadecimal

    @property
    def fees(self) -> int:
        """Satoshis of fees: what the coinbase claimed above the subsidy. Never negative."""
        return max(0, self.reward - B.block_subsidy(self.height))

    @property
    def fee_share(self) -> float:
        return self.fees / self.reward if self.reward else 0.0

    @property
    def fullness(self) -> float:
        return self.weight / MAX_WEIGHT


def pool_of(coinbase_hex: str) -> str:
    """The pool named in a coinbase script, or « Non identifié » when no known tag is found."""
    try:
        text = bytes.fromhex(coinbase_hex).decode("latin-1").lower()
    except ValueError:
        return "Non identifié"
    for name, pattern in POOL_TAGS:
        if re.search(pattern, text):
            return name
    return "Non identifié"


def monthly(samples: Iterable[Sample]) -> dict[str, list[Sample]]:
    out: dict[str, list[Sample]] = {}
    for s in samples:
        out.setdefault(s.day[:7], []).append(s)
    return out


def blocks_per_day(month: str, periods: Sequence[dict]) -> float:
    """Blocks a day during `month`, from the difficulty period that contains its middle."""
    mid = f"{month}-15"
    best = None
    for p in periods:
        if p["date"] <= mid:
            best = p
    if best is None:
        best = periods[0]
    return 2016 / best["jours"]


def hashrate_on(month: str, periods: Sequence[dict]) -> float:
    mid = f"{month}-15"
    best = periods[0]
    for p in periods:
        if p["date"] <= mid:
            best = p
    return best["puissance"]


def monthly_rows(samples: Iterable[Sample], periods: Sequence[dict]) -> list[dict]:
    """One row a month: averages over the sampled blocks, scaled with the observed block rate."""
    rows = []
    for month, group in sorted(monthly(samples).items()):
        bpd = blocks_per_day(month, periods)
        reward = mean(s.reward for s in group) / B.COIN
        fees = mean(s.fees for s in group) / B.COIN
        hashrate = hashrate_on(month, periods)
        rows.append({
            "mois": f"{month}-01",
            "echantillon": len(group),
            "transactions_par_jour": round(mean(s.tx_count for s in group) * bpd),
            "frais_par_bloc": round(fees, 4),
            "part_frais": round(mean(s.fee_share for s in group) * 100, 2),
            "remplissage": round(mean(s.fullness for s in group) * 100, 1),
            "taille_mo": round(mean(s.size for s in group) / 1e6, 3),
            "revenu_jour": round(reward * bpd, 1),
            "revenu_par_eh": round(reward * bpd / hashrate, 6) if hashrate >= 0.001 else None,
        })
    return rows


def pool_shares(samples: Iterable[Sample], year: str) -> dict[str, float]:
    """Shares of the sampled blocks of `year`, by pool tag, in percent."""
    group = [s for s in samples if s.day.startswith(year)]
    counts: dict[str, int] = {}
    for s in group:
        name = pool_of(s.coinbase)
        counts[name] = counts.get(name, 0) + 1
    return {k: v / len(group) * 100 for k, v in sorted(counts.items(), key=lambda kv: -kv[1])}


def nakamoto_coefficient(shares: dict[str, float]) -> int | None:
    """
    How many identified pools together exceed half of the blocks, the largest
    first; None when the identified pools do not reach half, as in the years
    when most miners did not tag their blocks.
    """
    total = 0.0
    ranked = sorted((v for k, v in shares.items() if k != "Non identifié"), reverse=True)
    for i, share in enumerate(ranked):
        total += share
        if total > 50:
            return i + 1
    return None


# =============================================================================
# PRICE-BASED INDICATORS, ON A CONSTRUCTED EXAMPLE
# =============================================================================

@dataclass(frozen=True)
class Coin:
    units: float
    last_moved_price: float     # the price when these coins last changed hands


def realized_price(coins: Sequence[Coin]) -> float:
    """Average price at which the coins last moved: the realized cap divided by the supply."""
    supply = sum(c.units for c in coins)
    return sum(c.units * c.last_moved_price for c in coins) / supply


def mvrv(price: float, coins: Sequence[Coin]) -> float:
    """Market value over realized value: above 1, holders are on average in profit."""
    return price / realized_price(coins)


def nupl(price: float, coins: Sequence[Coin]) -> float:
    """Net unrealized profit or loss, as a share of the market value."""
    return 1 - realized_price(coins) / price


# A constructed market of 1 000 coins, for the lesson only.
EXAMPLE_COINS = (Coin(400, 10.0), Coin(300, 25.0), Coin(200, 60.0), Coin(100, 90.0))
EXAMPLE_PRICES = (20, 30, 45, 60, 80, 95, 70, 50, 35, 25, 22, 30, 40, 55)


def indicator_rows() -> list[dict]:
    """A constructed cycle: the market price against a realized price that moves as coins change hands."""
    rows = []
    coins = list(EXAMPLE_COINS)
    for month, price in enumerate(EXAMPLE_PRICES, start=1):
        # each month, 5 % of the oldest coins change hands at the month's price
        moved = coins[0].units * 0.05
        coins[0] = Coin(coins[0].units - moved, coins[0].last_moved_price)
        coins.append(Coin(moved, price))
        rp = realized_price(coins)
        rows.append({"mois": month, "prix": price, "prix_realise": round(rp, 2),
                     "mvrv": round(price / rp, 2), "nupl": round(1 - rp / price, 2)})
    return rows


def slug(name: str) -> str:
    """A column name for a pool: lower case, ASCII letters and underscores."""
    import unicodedata
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")
