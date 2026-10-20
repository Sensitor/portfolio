"""
The calculations taught in the Crypto track's first path: what an exchange
pool charges, what a transfer costs, what a backup protects against.

Pure functions, as in the other modules: a figure printed in a lesson is the
figure returned here. Nothing in this module touches a network, a wallet or a
key; the amounts are those of the lesson examples.
"""

from __future__ import annotations

BIP39_WORDS = 2048              # the BIP 39 word list
GWEI = 10 ** -9                 # one gwei in ether
SECONDS_PER_YEAR = 365.25 * 24 * 3600


# =============================================================================
# AUTOMATED MARKET MAKERS
# =============================================================================

def amm_out(reserve_in: float, reserve_out: float, amount_in: float, fee: float = 0.003) -> float:
    """
    What a constant-product pool (x × y = k) pays for `amount_in`, after its fee.
    The product of the two reserves stays the same, so every unit bought costs
    more than the one before.
    """
    if reserve_in <= 0 or reserve_out <= 0 or amount_in < 0 or not 0 <= fee < 1:
        raise ValueError("reserves must be positive, the amount and the fee not negative")
    effective = amount_in * (1 - fee)
    return reserve_out * effective / (reserve_in + effective)


def pool_price(reserve_in: float, reserve_out: float) -> float:
    """The price of one unit of the `out` asset, in units of the `in` asset, before any trade."""
    return reserve_in / reserve_out


def price_impact(reserve_in: float, reserve_out: float, amount_in: float, fee: float = 0.0) -> float:
    """How much more than the pool price the trade pays on average, as a fraction."""
    paid = amount_in / amm_out(reserve_in, reserve_out, amount_in, fee)
    return paid / pool_price(reserve_in, reserve_out) - 1


# =============================================================================
# TRANSFERS
# =============================================================================

def gas_fee_eth(gas_used: int, gwei_per_gas: float) -> float:
    """An Ethereum transaction pays its gas at a price in gwei: 21 000 gas for a plain transfer."""
    return gas_used * gwei_per_gas * GWEI


def depeg_value(amount: float, price: float) -> float:
    """What a stablecoin balance is worth, in its reference currency, at a market price."""
    return amount * price


# =============================================================================
# BACKUPS
# =============================================================================

def entropy_bits(words: int) -> int:
    """
    The secret in a BIP 39 phrase: 11 bits a word, minus one checksum bit for
    every 33. Twelve words carry 128 bits, twenty-four carry 256.
    """
    if words not in (12, 15, 18, 21, 24):
        raise ValueError("a BIP 39 phrase has 12, 15, 18, 21 or 24 words")
    total = words * 11
    return total - total // 33


def years_to_try(bits: int, per_second: float) -> float:
    """Years needed to try every secret of `bits` bits at `per_second` tries a second."""
    if per_second <= 0:
        raise ValueError("a positive rate is needed")
    return 2 ** bits / per_second / SECONDS_PER_YEAR


# =============================================================================
# ANALYSING A TOKEN
# =============================================================================

def market_cap(price: float, circulating: float) -> float:
    return price * circulating


def fully_diluted(price: float, max_supply: float) -> float:
    """The value of every token that will ever exist, at today's price."""
    return price * max_supply


def price_after_dilution(price: float, supply_before: float, supply_after: float) -> float:
    """The price at which the market capitalisation stays the same once new tokens circulate."""
    if supply_before <= 0 or supply_after < supply_before:
        raise ValueError("the supply cannot shrink in a dilution")
    return price * supply_before / supply_after


# =============================================================================
# DEFI
# =============================================================================

def health_factor(collateral_value: float, liquidation_threshold: float, debt: float) -> float:
    """Above 1 the loan is safe; at 1 it can be liquidated."""
    if debt <= 0:
        raise ValueError("no debt, no health factor")
    return collateral_value * liquidation_threshold / debt


def liquidation_price(collateral_units: float, debt: float, liquidation_threshold: float) -> float:
    """The collateral price at which the health factor reaches 1."""
    return debt / (collateral_units * liquidation_threshold)


def impermanent_loss(price_ratio: float) -> float:
    """
    What a 50 / 50 constant-product position is worth against simply holding
    the two assets, when one price moves by `price_ratio` against the other,
    before fees. Always zero or negative.
    """
    if price_ratio <= 0:
        raise ValueError("a price ratio is positive")
    return 2 * price_ratio ** 0.5 / (1 + price_ratio) - 1


# =============================================================================
# CHART ROWS (lesson examples)
# =============================================================================

def impermanent_loss_rows() -> list[dict]:
    """The loss against holding, for relative price moves from ÷10 to ×10."""
    ratios = [0.1, 0.15, 0.2, 0.25, 0.33, 0.5, 0.67, 0.8, 1, 1.25, 1.5, 2, 3, 4, 5, 6, 8, 10]
    return [{"rapport": r, "perte": round(impermanent_loss(r) * 100, 2)} for r in ratios]


def liquidation_rows(threshold: float = 0.8) -> list[dict]:
    """For each loan-to-value ratio, the fall of the collateral that triggers liquidation."""
    return [{"ratio": ltv, "baisse": round((ltv / 100 / threshold - 1) * 100, 1)} for ltv in range(10, 80, 5)]


# A constructed token for the unlock lesson: 10 billion tokens.
UNLOCK_EXAMPLE = {
    "lancement": (0.20, 0, 0),          # share, cliff in months, vesting months after the cliff
    "equipe": (0.20, 12, 24),
    "investisseurs": (0.15, 6, 18),
    "communaute": (0.45, 0, 48),
}


def unlocked_share(share: float, cliff: int, vesting: int, month: int) -> float:
    """The share of the supply released by `month`: nothing before the cliff, then linearly."""
    if month < cliff:
        return 0.0
    if vesting == 0:
        return share
    return share * min(1.0, (month - cliff) / vesting)


def unlock_rows(months: int = 48) -> list[dict]:
    return [{"mois": m, **{k: round(unlocked_share(*v, m) * 100, 2) for k, v in UNLOCK_EXAMPLE.items()}}
            for m in range(0, months + 1)]


def staking_rows(rate: float = 0.08, years: int = 10) -> list[dict]:
    """The share of the supply kept by someone who stakes and by someone who does not."""
    return [{"annee": y, "staking": 100.0, "sans_staking": round(100 / (1 + rate) ** y, 2)} for y in range(years + 1)]


def seed_strength_rows(per_second: float = 1e12) -> list[dict]:
    """Years to try every phrase, by number of words, at `per_second` tries a second."""
    return [{"mots": f"{w} mots", "annees": years_to_try(entropy_bits(w), per_second)} for w in (12, 15, 18, 21, 24)]


def gas_rows(eth_price: float = 3000.0) -> list[dict]:
    """What a transfer costs in dollars as the gas price rises, for ether and for a token."""
    return [{"gwei": g, "ether": round(gas_fee_eth(21_000, g) * eth_price, 2),
             "jeton": round(gas_fee_eth(65_000, g) * eth_price, 2)} for g in (1, 5, 10, 20, 30, 50, 75, 100)]


def impact_rows() -> list[dict]:
    """The price impact of a deposit in a constant-product pool, by its share of the reserve."""
    shares = (0.1, 0.5, 1, 2, 5, 10, 20, 30, 50)
    return [{"part": s, "impact": round(price_impact(100.0, 100.0, s) * 100, 2)} for s in shares]
