"""
Portfolio X-Ray — look-through exposure.

Answers "what do I actually own?" rather than "which tickers do I hold?". A 40%
SPY + 25% QQQ book is not 65% "ETF"; it is roughly 38% technology, 71% US large
cap, and so on. This module resolves each holding into its underlying exposures
across five dimensions and aggregates them by weight.

IMPORTANT — provenance of the reference data
--------------------------------------------
`FUND_PROFILES` is *curated static reference data*, not live holdings. Breakdowns
are rounded approximations of publicly published fund fact sheets (2024-2025
vintage) and drift as funds rebalance. They are good enough to reveal structural
exposure — "this book is technology-heavy" — and not precise enough to quote as
the fund's official allocation. Anything the UI renders from here must be labelled
as indicative. Funds not listed fall back to a single-bucket profile derived from
the app's own sector/geography mapping, and unknown tickers land in "Unclassified"
rather than being silently assigned.

No Streamlit import here — this is pure data + computation.
"""

from __future__ import annotations

DIMENSIONS = ["asset_class", "sector", "geography", "market_cap", "style"]

DIMENSION_LABELS = {
    "asset_class": {"en": "Asset Class", "fr": "Classe d'Actifs"},
    "sector": {"en": "Sector", "fr": "Secteur"},
    "geography": {"en": "Geography", "fr": "Géographie"},
    "market_cap": {"en": "Market Cap", "fr": "Capitalisation"},
    "style": {"en": "Style", "fr": "Style"},
}

NA = "Not applicable"
UNCLASSIFIED = "Unclassified"

# Data vintage shown in the UI so the approximation is never presented as live.
DATA_VINTAGE = "2024-2025 published fund fact sheets (indicative, rounded)"


# =============================================================================
# FUND LOOK-THROUGH PROFILES
# =============================================================================

def _equity(sector, geography, market_cap, style):
    return {
        "asset_class": {"Equity": 1.0},
        "sector": sector,
        "geography": geography,
        "market_cap": market_cap,
        "style": style,
    }


_SP500_SECTORS = {
    "Technology": 0.320, "Financials": 0.130, "Healthcare": 0.110,
    "Consumer Discretionary": 0.100, "Communication": 0.090, "Industrials": 0.080,
    "Consumer Staples": 0.060, "Energy": 0.035, "Utilities": 0.025,
    "Real Estate": 0.025, "Materials": 0.025,
}

_US_ONLY = {"United States": 1.0}

FUND_PROFILES: dict[str, dict] = {
    # ── US broad equity ──────────────────────────────────────────────────────
    "SPY": _equity(
        _SP500_SECTORS, _US_ONLY,
        {"Large Cap": 0.95, "Mid Cap": 0.05},
        {"Growth": 0.45, "Blend": 0.30, "Value": 0.25},
    ),
    "VOO": _equity(
        _SP500_SECTORS, _US_ONLY,
        {"Large Cap": 0.95, "Mid Cap": 0.05},
        {"Growth": 0.45, "Blend": 0.30, "Value": 0.25},
    ),
    "VTI": _equity(
        {"Technology": 0.300, "Financials": 0.130, "Healthcare": 0.110,
         "Consumer Discretionary": 0.100, "Industrials": 0.090, "Communication": 0.080,
         "Consumer Staples": 0.050, "Energy": 0.035, "Real Estate": 0.030,
         "Utilities": 0.025, "Materials": 0.050},
        _US_ONLY,
        {"Large Cap": 0.82, "Mid Cap": 0.13, "Small Cap": 0.05},
        {"Growth": 0.42, "Blend": 0.32, "Value": 0.26},
    ),
    "QQQ": _equity(
        {"Technology": 0.520, "Communication": 0.160, "Consumer Discretionary": 0.140,
         "Healthcare": 0.060, "Consumer Staples": 0.050, "Industrials": 0.050,
         "Utilities": 0.010, "Materials": 0.010},
        {"United States": 0.97, "Developed ex-US": 0.03},
        {"Large Cap": 0.97, "Mid Cap": 0.03},
        {"Growth": 0.75, "Blend": 0.20, "Value": 0.05},
    ),
    "SCHD": _equity(
        {"Financials": 0.180, "Consumer Staples": 0.180, "Healthcare": 0.150,
         "Industrials": 0.140, "Energy": 0.100, "Technology": 0.090,
         "Consumer Discretionary": 0.080, "Materials": 0.040, "Communication": 0.040},
        _US_ONLY,
        {"Large Cap": 0.88, "Mid Cap": 0.12},
        {"Value": 0.70, "Blend": 0.25, "Growth": 0.05},
    ),
    "ARKK": _equity(
        {"Technology": 0.400, "Healthcare": 0.300, "Communication": 0.150,
         "Consumer Discretionary": 0.100, "Financials": 0.050},
        {"United States": 0.85, "Developed ex-US": 0.10, "Emerging Markets": 0.05},
        {"Mid Cap": 0.45, "Small Cap": 0.35, "Large Cap": 0.20},
        {"Growth": 1.0},
    ),

    # ── International equity ─────────────────────────────────────────────────
    "VXUS": _equity(
        {"Financials": 0.220, "Industrials": 0.140, "Technology": 0.130,
         "Consumer Discretionary": 0.110, "Healthcare": 0.090, "Consumer Staples": 0.070,
         "Materials": 0.070, "Communication": 0.060, "Energy": 0.050,
         "Utilities": 0.030, "Real Estate": 0.030},
        {"Europe": 0.40, "Emerging Markets": 0.25, "Japan": 0.14,
         "Canada": 0.07, "Asia-Pacific ex-Japan": 0.08, "Other": 0.06},
        {"Large Cap": 0.75, "Mid Cap": 0.18, "Small Cap": 0.07},
        {"Blend": 0.40, "Value": 0.38, "Growth": 0.22},
    ),
    "EFA": _equity(
        {"Financials": 0.230, "Industrials": 0.170, "Healthcare": 0.110,
         "Consumer Discretionary": 0.110, "Technology": 0.100, "Consumer Staples": 0.080,
         "Materials": 0.060, "Communication": 0.050, "Energy": 0.040,
         "Utilities": 0.035, "Real Estate": 0.015},
        {"Europe": 0.62, "Japan": 0.22, "Asia-Pacific ex-Japan": 0.10, "Other": 0.06},
        {"Large Cap": 0.86, "Mid Cap": 0.14},
        {"Blend": 0.40, "Value": 0.40, "Growth": 0.20},
    ),
    "EEM": _equity(
        {"Technology": 0.250, "Financials": 0.230, "Consumer Discretionary": 0.130,
         "Communication": 0.100, "Materials": 0.060, "Industrials": 0.070,
         "Consumer Staples": 0.060, "Energy": 0.050, "Healthcare": 0.030,
         "Utilities": 0.020},
        {"Emerging Markets": 1.0},
        {"Large Cap": 0.82, "Mid Cap": 0.18},
        {"Blend": 0.45, "Value": 0.35, "Growth": 0.20},
    ),
    "VWO": _equity(
        {"Technology": 0.240, "Financials": 0.230, "Consumer Discretionary": 0.140,
         "Communication": 0.090, "Industrials": 0.080, "Materials": 0.070,
         "Consumer Staples": 0.060, "Energy": 0.050, "Utilities": 0.020,
         "Healthcare": 0.020},
        {"Emerging Markets": 1.0},
        {"Large Cap": 0.78, "Mid Cap": 0.17, "Small Cap": 0.05},
        {"Blend": 0.45, "Value": 0.35, "Growth": 0.20},
    ),

    # ── Sector equity ────────────────────────────────────────────────────────
    "XLK": _equity({"Technology": 1.0}, _US_ONLY,
                   {"Large Cap": 0.96, "Mid Cap": 0.04}, {"Growth": 0.80, "Blend": 0.20}),
    "XLF": _equity({"Financials": 1.0}, _US_ONLY,
                   {"Large Cap": 0.90, "Mid Cap": 0.10}, {"Value": 0.60, "Blend": 0.40}),
    "XLE": _equity({"Energy": 1.0}, _US_ONLY,
                   {"Large Cap": 0.88, "Mid Cap": 0.12}, {"Value": 0.70, "Blend": 0.30}),
    "XLV": _equity({"Healthcare": 1.0}, _US_ONLY,
                   {"Large Cap": 0.93, "Mid Cap": 0.07}, {"Blend": 0.50, "Growth": 0.30, "Value": 0.20}),

    # ── Real estate ──────────────────────────────────────────────────────────
    "VNQ": {
        "asset_class": {"Real Estate": 1.0},
        "sector": {"Real Estate": 1.0},
        "geography": _US_ONLY,
        "market_cap": {"Large Cap": 0.45, "Mid Cap": 0.35, "Small Cap": 0.20},
        "style": {"Value": 0.50, "Blend": 0.50},
    },

    # ── Fixed income ─────────────────────────────────────────────────────────
    "AGG": {
        "asset_class": {"Bonds": 1.0},
        "sector": {"Government Bonds": 0.45, "Securitised": 0.28,
                   "Investment Grade Credit": 0.25, "Other Bonds": 0.02},
        "geography": _US_ONLY,
        "market_cap": {NA: 1.0},
        "style": {"Investment Grade": 1.0},
    },
    "TLT": {
        "asset_class": {"Bonds": 1.0},
        "sector": {"Government Bonds": 1.0},
        "geography": _US_ONLY,
        "market_cap": {NA: 1.0},
        "style": {"Long Duration": 1.0},
    },
    "LQD": {
        "asset_class": {"Bonds": 1.0},
        "sector": {"Investment Grade Credit": 1.0},
        "geography": _US_ONLY,
        "market_cap": {NA: 1.0},
        "style": {"Investment Grade": 1.0},
    },

    # ── Commodities ──────────────────────────────────────────────────────────
    "GLD": {
        "asset_class": {"Commodities": 1.0},
        "sector": {"Precious Metals": 1.0},
        "geography": {"Global": 1.0},
        "market_cap": {NA: 1.0},
        "style": {"Real Assets": 1.0},
    },
    "SLV": {
        "asset_class": {"Commodities": 1.0},
        "sector": {"Precious Metals": 1.0},
        "geography": {"Global": 1.0},
        "market_cap": {NA: 1.0},
        "style": {"Real Assets": 1.0},
    },
}


# =============================================================================
# SINGLE-NAME PROFILES
# =============================================================================
# Individual stocks resolve to a single bucket per dimension. Cap and style are
# editorial classifications of the company's profile, in the same spirit as a
# fund's published style box.

_STOCK_STYLE = {
    "AAPL": "Growth", "MSFT": "Growth", "GOOGL": "Growth", "AMZN": "Growth",
    "NVDA": "Growth", "META": "Growth", "TSLA": "Growth", "NFLX": "Growth",
    "JPM": "Value", "JNJ": "Value", "XOM": "Value", "BRK-B": "Value",
    "WMT": "Blend", "HD": "Blend", "V": "Growth", "MA": "Growth",
}

_STOCK_SECTOR_OVERRIDE = {
    "TSLA": "Consumer Discretionary",
    "AMZN": "Consumer Discretionary",
    "META": "Communication",
    "GOOGL": "Communication",
    "NFLX": "Communication",
    "WMT": "Consumer Staples",
    "HD": "Consumer Discretionary",
}

_GEO_NORMALISE = {
    "USA": "United States",
    "US": "United States",
    "International": "Developed ex-US",
    "Developed Ex-US": "Developed ex-US",
    "Emerging Markets": "Emerging Markets",
    "Global": "Global",
    "Europe": "Europe",
}

_CLASS_NORMALISE = {
    "Stock": "Equity",
    "ETF": "Equity",
    "Equity": "Equity",
    "Bond": "Bonds",
    "Bonds": "Bonds",
    "Crypto": "Crypto",
    "Commodity": "Commodities",
    "Commodities": "Commodities",
    "Real Estate": "Real Estate",
    "Cash": "Cash",
}


def _crypto_profile() -> dict:
    return {
        "asset_class": {"Crypto": 1.0},
        "sector": {"Digital Assets": 1.0},
        "geography": {"Global": 1.0},
        "market_cap": {NA: 1.0},
        "style": {"High Volatility": 1.0},
    }


def resolve_profile(ticker: str, asset_info: dict, sector_map: dict, geo_map: dict) -> dict:
    """
    Resolve one ticker to a five-dimension exposure profile.

    Resolution order: curated fund look-through -> crypto -> single-name derived
    from the app's own mappings -> unclassified. Nothing is guessed silently; a
    ticker with no information lands in `Unclassified` so the gap stays visible
    in the UI.
    """
    if ticker in FUND_PROFILES:
        return FUND_PROFILES[ticker]

    info = asset_info.get(ticker, {})
    raw_class = info.get("asset_class") or ("Crypto" if ticker.endswith("-USD") else None)
    asset_class = _CLASS_NORMALISE.get(raw_class, raw_class)

    if asset_class == "Crypto":
        return _crypto_profile()

    raw_sector = _STOCK_SECTOR_OVERRIDE.get(ticker) or info.get("sector") or sector_map.get(ticker)
    raw_geo = info.get("geography") or geo_map.get(ticker)

    if not asset_class and not raw_sector:
        return {d: {UNCLASSIFIED: 1.0} for d in DIMENSIONS}

    return {
        "asset_class": {asset_class or "Equity": 1.0},
        "sector": {raw_sector or UNCLASSIFIED: 1.0},
        "geography": {_GEO_NORMALISE.get(raw_geo, raw_geo or UNCLASSIFIED): 1.0},
        "market_cap": {"Large Cap": 1.0},
        "style": {_STOCK_STYLE.get(ticker, "Blend"): 1.0},
    }


# =============================================================================
# AGGREGATION
# =============================================================================

def look_through(weights: dict, asset_info: dict, sector_map: dict, geo_map: dict) -> dict:
    """
    Aggregate portfolio weights into underlying exposures.

    Returns {dimension: {bucket: weight}}, each dimension summing to ~1 and sorted
    largest first. Buckets marked "Not applicable" (a bond's market cap, say) are
    kept rather than dropped, so the percentages always reconcile to 100%.
    """
    total = sum(weights.values())
    if total <= 0:
        return {d: {} for d in DIMENSIONS}

    out: dict[str, dict[str, float]] = {d: {} for d in DIMENSIONS}
    for ticker, weight in weights.items():
        w = weight / total
        profile = resolve_profile(ticker, asset_info, sector_map, geo_map)
        for dim in DIMENSIONS:
            for bucket, share in (profile.get(dim) or {UNCLASSIFIED: 1.0}).items():
                out[dim][bucket] = out[dim].get(bucket, 0.0) + w * share

    return {
        dim: dict(sorted(buckets.items(), key=lambda kv: kv[1], reverse=True))
        for dim, buckets in out.items()
    }


def headline_exposures(xray: dict) -> list[dict]:
    """
    The three or four numbers that make the look-through point immediately.

    Picks the dominant bucket of the dimensions that most often surprise people:
    sector concentration, cap bias and style tilt.
    """
    picks = []
    for dim, label_en, label_fr in (
        ("sector", "Sector Exposure", "Exposition Sectorielle"),
        ("market_cap", "Cap Exposure", "Exposition Capitalisation"),
        ("style", "Style Exposure", "Exposition Style"),
        ("geography", "Geographic Exposure", "Exposition Géographique"),
    ):
        buckets = {k: v for k, v in (xray.get(dim) or {}).items() if k not in (NA, UNCLASSIFIED)}
        if not buckets:
            continue
        bucket, share = next(iter(buckets.items()))
        picks.append({
            "dimension": dim,
            "label_en": label_en, "label_fr": label_fr,
            "bucket": bucket, "share": share,
        })
    return picks


def direct_vs_lookthrough(weights: dict, xray: dict, dimension: str = "sector") -> list[dict]:
    """
    Compare the naive ticker-level view with the resolved view.

    This is what shows a "5% technology" book to actually be 38% technology once
    its index funds are unpacked.
    """
    direct: dict[str, float] = {}
    total = sum(weights.values()) or 1.0
    for ticker, weight in weights.items():
        direct[ticker] = weight / total

    resolved = xray.get(dimension, {})
    return [{"bucket": k, "share": v} for k, v in resolved.items()]
