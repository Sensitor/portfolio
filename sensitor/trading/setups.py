"""
Setup and mistake taxonomies.

The built-in vocabulary a trader tags trades with, plus the helpers that keep
custom tags usable alongside it.

Why a taxonomy at all: analytics grouped by free text fragments immediately — a
trader who writes "FVG", "fvg" and "Fair Value Gap" on three trades gets three
buckets of one instead of one bucket of three, and every per-setup statistic
becomes noise. `canonical()` folds the known spellings; anything genuinely new
is kept as the trader wrote it rather than discarded.

The list below is not prescriptive. It covers the ICT/SMC vocabulary and the
classical one because those are what the brief names, and custom tags are
first-class everywhere the built-ins are.
"""

from __future__ import annotations

import re

# ── Setups ───────────────────────────────────────────────────────────────────
# key -> (english label, french label, family, aliases)

SETUPS = {
    "bos": ("Break of Structure", "Rupture de Structure", "smc",
            ("break of structure", "breakofstructure", "structure break")),
    "choch": ("Change of Character", "Changement de Caractère", "smc",
              ("change of character", "chuch", "ch och")),
    "fvg": ("Fair Value Gap", "Fair Value Gap", "smc",
            ("fair value gap", "imbalance", "gap")),
    "order_block": ("Order Block", "Order Block", "smc",
                    ("ob", "orderblock", "order block")),
    "ote": ("Optimal Trade Entry", "Entrée Optimale", "smc",
            ("optimal trade entry", "golden pocket")),
    "liquidity_sweep": ("Liquidity Sweep", "Balayage de Liquidité", "smc",
                        ("sweep", "liquidity grab", "stop hunt", "raid")),
    "breaker": ("Breaker Block", "Breaker Block", "smc", ("breaker",)),
    "breakout": ("Breakout", "Cassure", "classical",
                 ("break out", "range break")),
    "reversal": ("Reversal", "Retournement", "classical",
                 ("mean reversal", "turn")),
    "trend_following": ("Trend Following", "Suivi de Tendance", "classical",
                        ("trend", "with trend", "continuation")),
    "mean_reversion": ("Mean Reversion", "Retour à la Moyenne", "classical",
                       ("mean revert", "fade")),
    "range": ("Range", "Range", "classical", ("range trade", "consolidation")),
    "news": ("News", "Actualité", "event", ("event", "data release", "nfp")),
}

SETUP_FAMILIES = {
    "smc": {"en": "Smart Money", "fr": "Smart Money"},
    "classical": {"en": "Classical", "fr": "Classique"},
    "event": {"en": "Event", "fr": "Événement"},
    "custom": {"en": "Custom", "fr": "Personnalisé"},
}

# ── Mistakes ─────────────────────────────────────────────────────────────────
# The behaviours the psychology module looks for. Each is something the trader
# records about themselves — none is inferred from price data.

MISTAKES = {
    "fomo": ("FOMO entry", "Entrée FOMO",
             ("fear of missing out", "chased", "chasing")),
    "revenge": ("Revenge trade", "Trade de revanche", ("revenge trading",)),
    "overtrading": ("Overtrading", "Surtrading", ("too many trades",)),
    "hesitation": ("Hesitation", "Hésitation", ("hesitated", "late entry")),
    "early_exit": ("Exited early", "Sortie anticipée",
                   ("cut winner", "closed early")),
    "moved_stop": ("Moved stop loss", "Stop déplacé",
                   ("widened stop", "removed stop")),
    "oversized": ("Increased risk", "Risque augmenté",
                  ("oversized", "too big", "size up")),
    "no_stop": ("No stop loss", "Pas de stop", ("without stop",)),
    "off_plan": ("Traded outside plan", "Hors plan",
                 ("not in plan", "unplanned", "no setup")),
    "averaged_down": ("Averaged down", "Moyenne à la baisse", ("added to loser",)),
}

# ── Other vocabularies ───────────────────────────────────────────────────────

TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"]

MARKET_REGIMES = {
    "trending": {"en": "Trending", "fr": "Tendanciel"},
    "ranging": {"en": "Ranging", "fr": "En range"},
    "volatile": {"en": "Volatile", "fr": "Volatil"},
    "quiet": {"en": "Quiet", "fr": "Calme"},
}

EMOTIONS = {
    "calm": {"en": "Calm", "fr": "Calme"},
    "confident": {"en": "Confident", "fr": "Confiant"},
    "anxious": {"en": "Anxious", "fr": "Anxieux"},
    "impatient": {"en": "Impatient", "fr": "Impatient"},
    "frustrated": {"en": "Frustrated", "fr": "Frustré"},
    "euphoric": {"en": "Euphoric", "fr": "Euphorique"},
    "fearful": {"en": "Fearful", "fr": "Craintif"},
    "bored": {"en": "Bored", "fr": "Ennuyé"},
}


# =============================================================================
# NORMALISATION
# =============================================================================

def _alias_index(catalogue: dict) -> dict:
    """Map every spelling of every entry to its key."""
    index = {}
    for key, entry in catalogue.items():
        index[key] = key
        index[_slug(key)] = key
        index[_slug(entry[0])] = key
        index[_slug(entry[1])] = key
        for alias in entry[-1]:
            index[_slug(alias)] = key
    return index


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


_SETUP_INDEX = _alias_index(SETUPS)
_MISTAKE_INDEX = _alias_index(MISTAKES)


def canonical_setup(tag: str) -> str:
    """
    Fold a setup tag onto its canonical key.

    Unknown tags come back normalised but intact — a trader's own vocabulary is
    as valid as the built-in one, it just has no translation or family.
    """
    if not tag:
        return ""
    return _SETUP_INDEX.get(_slug(tag), str(tag).strip())


def canonical_mistake(tag: str) -> str:
    if not tag:
        return ""
    return _MISTAKE_INDEX.get(_slug(tag), str(tag).strip())


def canonical_setups(tags) -> list[str]:
    """Fold a list, dropping empties and duplicates while keeping order."""
    seen, out = set(), []
    for tag in tags or []:
        key = canonical_setup(tag)
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def canonical_mistakes(tags) -> list[str]:
    seen, out = set(), []
    for tag in tags or []:
        key = canonical_mistake(tag)
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


# =============================================================================
# LABELS
# =============================================================================

def setup_label(key: str, lang: str = "en") -> str:
    entry = SETUPS.get(key)
    if not entry:
        return str(key).replace("_", " ").title()
    return entry[1] if lang == "fr" else entry[0]


def mistake_label(key: str, lang: str = "en") -> str:
    entry = MISTAKES.get(key)
    if not entry:
        return str(key).replace("_", " ").title()
    return entry[1] if lang == "fr" else entry[0]


def setup_family(key: str) -> str:
    entry = SETUPS.get(key)
    return entry[2] if entry else "custom"


def is_custom_setup(key: str) -> bool:
    return key not in SETUPS


def known_setups(family: str | None = None) -> list[str]:
    if family is None:
        return list(SETUPS)
    return [k for k, v in SETUPS.items() if v[2] == family]


def combination_key(setups) -> str:
    """
    A stable label for a setup combination.

    "BOS + FVG" and "FVG + BOS" are the same confluence and must land in the same
    bucket, so the parts are sorted before joining.
    """
    keys = sorted(canonical_setups(setups))
    return " + ".join(keys) if keys else "untagged"


def combination_label(key: str, lang: str = "en") -> str:
    if key == "untagged":
        return "Untagged" if lang == "en" else "Non étiqueté"
    return " + ".join(setup_label(part, lang) for part in key.split(" + "))
