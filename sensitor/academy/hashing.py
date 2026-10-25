"""
The two ideas behind a block chain, small enough to run on a page.

`digest` is SHA-256, the function Bitcoin uses (twice, on a binary header).
`mine` is a toy proof of work: find a number that, appended to the data, gives
a digest starting with a given count of zeros. Bitcoin's real target works on
the same principle at an incomparably higher difficulty (about 6 × 10^23 tries
per block on average in October 2026, against 65 536 for four zeros here);
nothing here touches a real network or a real key.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

MAX_ZEROS = 5                   # beyond this, a page would wait too long


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Mined:
    nonce: int
    digest: str
    tries: int


def mine(data: str, zeros: int, *, limit: int = 5_000_000) -> Mined | None:
    """The first nonce whose digest of `data` + nonce starts with `zeros` zeros, or None past `limit` tries."""
    if not 0 <= zeros <= MAX_ZEROS:
        raise ValueError(f"between 0 and {MAX_ZEROS} zeros")
    prefix = "0" * zeros
    for nonce in range(limit):
        value = digest(f"{data}{nonce}")
        if value.startswith(prefix):
            return Mined(nonce, value, nonce + 1)
    return None


def expected_tries(zeros: int) -> int:
    """Each hexadecimal zero divides the chance by 16."""
    return 16 ** zeros


def chain(blocks: list[str], zeros: int = 0) -> list[Mined]:
    """
    Each block's digest covers the previous block's digest: change one block
    and every digest after it changes too.
    """
    out: list[Mined] = []
    previous = "0" * 64
    for data in blocks:
        mined = mine(previous + data, zeros)
        out.append(mined)
        previous = mined.digest
    return out
