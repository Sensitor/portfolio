"""
Factor exposure engine.

Estimates what systematic risks a portfolio is actually taking, by regressing its
returns on a set of factor proxies built from liquid ETFs.

Method
------
Each style factor is a long/short spread between two ETFs (value minus growth,
small minus large, and so on), which nets out most of the market exposure and
leaves the style tilt. The market factor is the broad index in excess of the
risk-free rate. Portfolio excess returns are then regressed on all available
factors at once by ordinary least squares:

    r_p - rf = alpha + sum_k beta_k * F_k + epsilon

Multivariate rather than one factor at a time: run separately, correlated factors
each claim the same variance and the loadings do not add up to anything.

What these numbers are not
--------------------------
Loadings are estimates over one window, from proxies that are themselves
imperfect. They move with the window, they assume the relationship is linear and
stable, and a spread ETF is not the academic factor it stands in for. The module
reports standard errors, t-statistics and R-squared alongside every loading so a
weak fit is visible as a weak fit rather than presented as a fact.

No Streamlit here — callers fetch the proxy returns and pass them in.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import analytics as A

# =============================================================================
# FACTOR DEFINITIONS
# =============================================================================
# Each factor is (long leg, short leg or None, label). A None short leg means the
# factor is the long leg in excess of the risk-free rate.

FACTOR_SPECS = {
    "market": {
        "long": "SPY", "short": None,
        "en": "Market", "fr": "Marché",
        "desc_en": "Broad US equity market in excess of the risk-free rate.",
        "desc_fr": "Marché actions US large en excès du taux sans risque.",
    },
    "size": {
        "long": "IWM", "short": "SPY",
        "en": "Size", "fr": "Taille",
        "desc_en": "Small caps minus large caps. Positive means a small-cap tilt.",
        "desc_fr": "Petites capitalisations moins grandes. Positif = biais small cap.",
    },
    "value": {
        "long": "IWD", "short": "IWF",
        "en": "Value", "fr": "Value",
        "desc_en": "Value minus growth. Positive means a value tilt, negative a growth tilt.",
        "desc_fr": "Value moins croissance. Positif = biais value, négatif = biais croissance.",
    },
    "momentum": {
        "long": "MTUM", "short": "SPY",
        "en": "Momentum", "fr": "Momentum",
        "desc_en": "Recent winners minus the broad market.",
        "desc_fr": "Gagnants récents moins le marché large.",
    },
    "quality": {
        "long": "QUAL", "short": "SPY",
        "en": "Quality", "fr": "Qualité",
        "desc_en": "Profitable, low-leverage companies minus the broad market.",
        "desc_fr": "Entreprises rentables et peu endettées moins le marché large.",
    },
    "low_vol": {
        "long": "USMV", "short": "SPY",
        "en": "Low Volatility", "fr": "Faible Volatilité",
        "desc_en": "Minimum-volatility equities minus the broad market.",
        "desc_fr": "Actions à volatilité minimale moins le marché large.",
    },
    "duration": {
        "long": "TLT", "short": "SHY",
        "en": "Duration", "fr": "Duration",
        "desc_en": "Long Treasuries minus short Treasuries. Positive means rate-sensitive.",
        "desc_fr": "Obligations longues moins courtes. Positif = sensible aux taux.",
    },
    "credit": {
        "long": "HYG", "short": "IEF",
        "en": "Credit", "fr": "Crédit",
        "desc_en": "High yield minus Treasuries. Positive means credit-spread exposure.",
        "desc_fr": "Haut rendement moins emprunts d'État. Positif = exposition au spread de crédit.",
    },
    "inflation": {
        "long": "TIP", "short": "IEF",
        "en": "Inflation", "fr": "Inflation",
        "desc_en": "Inflation-linked minus nominal Treasuries — a breakeven proxy.",
        "desc_fr": "Obligations indexées moins nominales — proxy du point mort d'inflation.",
    },
    "commodities": {
        "long": "DBC", "short": None,
        "en": "Commodities", "fr": "Matières Premières",
        "desc_en": "Broad commodity basket in excess of the risk-free rate.",
        "desc_fr": "Panier large de matières premières en excès du taux sans risque.",
    },
    "usd": {
        "long": "UUP", "short": None,
        "en": "US Dollar", "fr": "Dollar US",
        "desc_en": "US dollar against a basket of major currencies.",
        "desc_fr": "Dollar US contre un panier de devises majeures.",
    },
}

FACTOR_ORDER = list(FACTOR_SPECS)


def required_tickers() -> list[str]:
    """Every ETF the factor set needs, deduplicated."""
    out: list[str] = []
    for spec in FACTOR_SPECS.values():
        for leg in (spec["long"], spec["short"]):
            if leg and leg not in out:
                out.append(leg)
    return out


# =============================================================================
# FACTOR CONSTRUCTION
# =============================================================================

def build_factors(proxy_returns: dict, rf: float = A.DEFAULT_RF) -> pd.DataFrame:
    """
    Build the factor return matrix from {ticker: return Series}.

    Factors whose legs are missing are dropped rather than approximated, so a
    portfolio analysed with partial data shows fewer factors instead of quietly
    wrong ones.
    """
    rf_daily = rf / A.TRADING_DAYS
    columns = {}

    for key, spec in FACTOR_SPECS.items():
        long_leg = proxy_returns.get(spec["long"])
        if long_leg is None or len(long_leg) < 60:
            continue
        if spec["short"] is None:
            columns[key] = long_leg - rf_daily
        else:
            short_leg = proxy_returns.get(spec["short"])
            if short_leg is None or len(short_leg) < 60:
                continue
            joined = pd.concat([long_leg, short_leg], axis=1, join="inner").dropna()
            if len(joined) < 60:
                continue
            columns[key] = joined.iloc[:, 0] - joined.iloc[:, 1]

    if not columns:
        return pd.DataFrame()
    return pd.DataFrame(columns).dropna()


# =============================================================================
# REGRESSION
# =============================================================================

def _ols(y: np.ndarray, X: np.ndarray) -> dict | None:
    """
    OLS with an intercept, returning coefficients and their standard errors.

    Uses lstsq rather than a normal-equation inverse: the factor matrix is
    correlated by construction and the normal equations are ill-conditioned.
    Returns None if the design matrix is rank deficient.
    """
    n, k = X.shape
    if n <= k + 2:
        return None

    design = np.column_stack([np.ones(n), X])
    coef, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    if rank < design.shape[1]:
        return None

    residuals = y - design @ coef
    dof = n - design.shape[1]
    sigma2 = float(residuals @ residuals) / dof

    try:
        cov = sigma2 * np.linalg.pinv(design.T @ design)
    except np.linalg.LinAlgError:
        return None
    stderr = np.sqrt(np.clip(np.diag(cov), 0, None))

    ss_res = float(residuals @ residuals)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    adj_r2 = 1 - (1 - r_squared) * (n - 1) / dof if dof > 0 else 0.0

    return {
        "coef": coef, "stderr": stderr,
        "r_squared": r_squared, "adj_r_squared": adj_r2,
        "n": n, "dof": dof,
    }


def factor_exposure(portfolio_returns, factors: pd.DataFrame,
                    rf: float = A.DEFAULT_RF) -> dict:
    """
    Regress portfolio excess returns on the factor matrix.

    Returns per-factor loading, standard error, t-statistic and significance,
    plus annualised alpha and the fit quality. `significant` uses |t| >= 2, the
    conventional rough cutoff — it is reported so weak loadings can be visually
    de-emphasised rather than silently dropped.
    """
    if factors is None or factors.empty or portfolio_returns is None:
        return {}

    joined = pd.concat([portfolio_returns.rename("y"), factors], axis=1,
                       join="inner").dropna()
    if len(joined) < 60:
        return {}

    rf_daily = rf / A.TRADING_DAYS
    y = (joined["y"] - rf_daily).to_numpy()
    names = [c for c in joined.columns if c != "y"]
    X = joined[names].to_numpy()

    fit = _ols(y, X)
    if fit is None:
        return {}

    coef, stderr = fit["coef"], fit["stderr"]
    loadings = []
    for i, name in enumerate(names):
        beta = float(coef[i + 1])
        se = float(stderr[i + 1])
        t_stat = beta / se if se > 0 else 0.0
        loadings.append({
            "factor": name,
            "loading": beta,
            "stderr": se,
            "t_stat": t_stat,
            "significant": abs(t_stat) >= 2.0,
        })

    loadings.sort(key=lambda d: abs(d["loading"]), reverse=True)

    return {
        "loadings": loadings,
        "alpha": float(coef[0]) * A.TRADING_DAYS,
        "alpha_t": float(coef[0] / stderr[0]) if stderr[0] > 0 else 0.0,
        "r_squared": fit["r_squared"],
        "adj_r_squared": fit["adj_r_squared"],
        "n_days": fit["n"],
        "n_factors": len(names),
    }


def factor_label(key: str, lang: str = "en") -> str:
    spec = FACTOR_SPECS.get(key, {})
    return spec.get(lang) or spec.get("en") or key


def factor_description(key: str, lang: str = "en") -> str:
    spec = FACTOR_SPECS.get(key, {})
    return spec.get(f"desc_{lang}") or spec.get("desc_en") or ""
