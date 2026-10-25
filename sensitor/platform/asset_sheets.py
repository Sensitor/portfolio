"""
The asset library's sheets, as the platform writes them.

The analyzer's catalogue (`investment.assets.ASSET_INFO`) carries prose with
figures nobody sources (fees, market shares, user counts), allocation ranges
and sizing advice. The platform shows its own sheets instead, kept as content in
`content/portfolio/fiches.toml`: for each asset what it is, the role it is
usually given in a portfolio, and the limit of that role. `problems()` holds them
to the house rules, and the tests run it.

No Streamlit.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

SHEETS_PATH = Path(__file__).resolve().parents[2] / "content" / "portfolio" / "fiches.toml"
FIELDS = ("description", "role", "limite")

NAMED = ("S&P 500", "CAC 40", "Nasdaq-100", "Layer 2", "60/40")   # names that carry digits and no figure
FIGURE = re.compile(r"(?<![A-Za-z])\d")                            # a digit not part of a word, as in Web3
# Wording that would turn a sheet into advice or a promise.
ADVICE = ("attendez-vous", "dimensionner", "par défaut", "indispensable", "recommand", "conseill", "il faut",
          "vous devez", "achetez", "vendez", "garanti", "sans risque", "à coup sûr")
DASHES = (chr(0x2014), chr(0x2013))                               # em and en dash


@dataclass(frozen=True)
class Sheet:
    description: str
    role: str
    limite: str


def has_figure(text: str) -> bool:
    for name in NAMED:
        text = text.replace(name, "")
    return bool(FIGURE.search(text))


def plain(text: str | None) -> str:
    """Prose without its figures: a bracket holding one goes, then any sentence still holding one."""
    text = re.sub(r"\s*\([^)]*\)", lambda m: "" if has_figure(m.group()) else m.group(), str(text or ""))
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(x for x in sentences if x and not has_figure(x))


def _read(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


@lru_cache(maxsize=1)
def load() -> dict[str, Sheet]:
    """Every sheet by symbol. Shared content, the same for every visitor."""
    return {ticker: Sheet(*(str(raw.get(f, "")).strip() for f in FIELDS)) for ticker, raw in _read(SHEETS_PATH).items()}


def problems(tickers, path: Path = SHEETS_PATH) -> list[str]:
    """Every way the sheets break the rules: coverage, empty fields, figures, advice, dashes."""
    raw = _read(path)
    found = []
    for ticker in sorted(set(tickers) - set(raw)):
        found.append(f"{ticker}: pas de fiche")
    for ticker in sorted(set(raw) - set(tickers)):
        found.append(f"{ticker}: fiche sans actif dans la bibliothèque")
    for ticker, entry in raw.items():
        extra = set(entry) - set(FIELDS)
        if extra:
            found.append(f"{ticker}: champs inconnus {sorted(extra)}")
        for field in FIELDS:
            text = str(entry.get(field, "")).strip()
            if not text:
                found.append(f"{ticker}.{field}: vide")
                continue
            if has_figure(text):
                found.append(f"{ticker}.{field}: un chiffre")
            if any(d in text for d in DASHES):
                found.append(f"{ticker}.{field}: un tiret long")
            lower = text.lower()
            for word in ADVICE:
                if word in lower:
                    found.append(f"{ticker}.{field}: « {word} »")
            if not text.endswith((".", "»", "?")):
                found.append(f"{ticker}.{field}: pas de point final")
    return found
