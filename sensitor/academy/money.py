"""
The mechanics taught in the course « La monnaie »: what a loan does to a bank's
balance sheet, what a loan costs, and why a bond's price falls when rates rise.

Pure functions, no Streamlit. The lessons quote figures these functions compute,
and the tests recompute every one of them.

These are accounting identities and textbook formulas, not models of an
economy: a balance sheet always balances, an annuity always repays its
principal. What they leave out (how much banks choose to lend, who wants to
borrow, what the central bank does next) is discussed in the lessons.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ── Balance sheets ───────────────────────────────────────────────────────────

@dataclass
class BalanceSheet:
    """A simplified bank balance sheet. Assets on the left, liabilities and equity on the right."""
    assets: dict[str, float] = field(default_factory=dict)
    liabilities: dict[str, float] = field(default_factory=dict)

    @property
    def total_assets(self) -> float:
        return sum(self.assets.values())

    @property
    def total_liabilities(self) -> float:
        return sum(self.liabilities.values())

    @property
    def balanced(self) -> bool:
        return abs(self.total_assets - self.total_liabilities) < 1e-9

    def copy(self) -> "BalanceSheet":
        return BalanceSheet(dict(self.assets), dict(self.liabilities))


def grant_loan(sheet: BalanceSheet, amount: float) -> BalanceSheet:
    """
    The bank credits the borrower's account: a new loan on the asset side, a new
    deposit on the liability side, for the same amount. Money is created.
    """
    if amount <= 0:
        raise ValueError("a loan must be positive")
    out = sheet.copy()
    out.assets["Crédits"] = out.assets.get("Crédits", 0.0) + amount
    out.liabilities["Dépôts"] = out.liabilities.get("Dépôts", 0.0) + amount
    return out


def repay_loan(sheet: BalanceSheet, amount: float) -> BalanceSheet:
    """Repayment does the reverse: the deposit used to repay disappears with the loan."""
    if amount <= 0:
        raise ValueError("a repayment must be positive")
    if amount > sheet.assets.get("Crédits", 0.0) or amount > sheet.liabilities.get("Dépôts", 0.0):
        raise ValueError("cannot repay more than the loans or the deposits on the sheet")
    out = sheet.copy()
    out.assets["Crédits"] -= amount
    out.liabilities["Dépôts"] -= amount
    return out


def transfer_out(sheet: BalanceSheet, amount: float) -> BalanceSheet:
    """
    A depositor pays someone at another bank: the deposit leaves, and the bank
    settles in central bank reserves. Both sides shrink; no money is created.
    """
    if amount <= 0:
        raise ValueError("a transfer must be positive")
    if amount > sheet.assets.get("Réserves", 0.0):
        raise ValueError("the bank lacks the reserves to settle this transfer")
    out = sheet.copy()
    out.assets["Réserves"] -= amount
    out.liabilities["Dépôts"] -= amount
    return out


# ── Loans ────────────────────────────────────────────────────────────────────

def payment(principal: float, annual_rate: float, years: int, periods_per_year: int = 12) -> float:
    """The constant instalment of a fully amortising loan."""
    if principal <= 0 or years <= 0 or periods_per_year <= 0:
        raise ValueError("principal, duration and frequency must be positive")
    n = years * periods_per_year
    r = annual_rate / periods_per_year
    if r == 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** -n)


def total_interest(principal: float, annual_rate: float, years: int, periods_per_year: int = 12) -> float:
    return payment(principal, annual_rate, years, periods_per_year) * years * periods_per_year - principal


def amortisation_by_year(principal: float, annual_rate: float, years: int,
                         periods_per_year: int = 12) -> list[dict]:
    """Interest and principal repaid in each year, and the balance left at its end."""
    pay = payment(principal, annual_rate, years, periods_per_year)
    r = annual_rate / periods_per_year
    balance, rows = principal, []
    for year in range(1, years + 1):
        interest = capital = 0.0
        for _ in range(periods_per_year):
            i = balance * r
            interest += i
            capital += pay - i
            balance -= pay - i
        rows.append({"annee": year, "interets": round(interest, 2), "capital": round(capital, 2),
                     "restant": round(max(balance, 0.0), 2)})
    return rows


# The worked example of the lesson on interest, drawn as a chart.
EXAMPLE_LOAN = (200_000.0, 0.04, 20)


def example_amortisation_rows() -> list[dict]:
    return amortisation_by_year(*EXAMPLE_LOAN)


# ── Bonds ────────────────────────────────────────────────────────────────────

def bond_price(face: float, coupon_rate: float, years: int, market_yield: float) -> float:
    """Price of a bond paying an annual coupon, discounted at the market yield."""
    if face <= 0 or years <= 0:
        raise ValueError("face value and maturity must be positive")
    if market_yield <= -1:
        raise ValueError("the yield must be above -100 %")
    coupon = face * coupon_rate
    return sum(coupon / (1 + market_yield) ** t for t in range(1, years + 1)) + face / (1 + market_yield) ** years


def bond_yield(price: float, face: float, coupon_rate: float, years: int) -> float:
    """The yield that makes the bond worth `price`, by bisection."""
    if price <= 0:
        raise ValueError("the price must be positive")
    low, high = -0.99, 1.0
    for _ in range(200):
        mid = (low + high) / 2
        if bond_price(face, coupon_rate, years, mid) > price:
            low = mid
        else:
            high = mid
    return (low + high) / 2
