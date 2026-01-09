"""
Cost of Capital Calculation Engine

Implements 4 methods for calculating WACC:
1. Direct input
2. Detailed (CAPM with operating country ERP)
3. Industry average
4. Histogram-based

Replicates the logic from the Excel 'Cost of capital worksheet' sheet.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class CostOfCapitalInputs:
    """Inputs for cost of capital calculation."""
    # Approach
    approach: str = "detailed"  # 'direct', 'detailed', 'industry', 'histogram'
    direct_coc: Optional[float] = None

    # Equity inputs
    shares_outstanding: float = 0
    stock_price: float = 0
    risk_free_rate: float = 0.045

    # Beta inputs
    beta_approach: str = "single_business_us"
    unlevered_beta: float = 1.0
    direct_beta: Optional[float] = None

    # ERP inputs
    erp_approach: str = "operating_countries"
    direct_erp: Optional[float] = None
    operating_countries_erp: Optional[float] = None  # Pre-calculated weighted ERP
    country_of_incorporation_erp: Optional[float] = None
    operating_regions_erp: Optional[float] = None

    # Debt inputs
    book_debt: float = 0
    interest_expense: float = 0
    debt_maturity: float = 3
    debt_approach: str = "actual_rating"
    actual_rating_spread: Optional[float] = None
    synthetic_rating_spread: Optional[float] = None
    direct_cost_of_debt: Optional[float] = None
    country_default_spread: float = 0

    # Tax
    marginal_tax_rate: float = 0.25

    # Operating leases
    lease_debt_value: float = 0

    # Convertible debt
    convertible_book_value: float = 0
    convertible_interest: float = 0
    convertible_maturity: float = 0
    convertible_market_value: float = 0

    # Preferred stock
    preferred_shares: int = 0
    preferred_price: float = 0
    preferred_dividend: float = 0

    # Industry averages (for industry average approach)
    industry_coc: Optional[float] = None
    industry_rf_at_calc: float = 0.0388  # Historical RF when industry CoC was calculated


@dataclass
class CostOfCapitalResult:
    """Result of cost of capital calculation."""
    approach: str
    risk_free_rate: float
    unlevered_beta: float
    levered_beta: float
    equity_risk_premium: float
    cost_of_equity: float
    pretax_cost_of_debt: float
    after_tax_cost_of_debt: float
    market_value_equity: float
    market_value_debt: float
    market_value_preferred: float
    equity_weight: float
    debt_weight: float
    preferred_weight: float
    wacc: float
    stable_wacc: float


def calculate_operating_countries_erp(
    countries: list[dict],
    country_erp_lookup: dict[str, float]
) -> float:
    """
    Calculate revenue-weighted equity risk premium from operating countries.

    Args:
        countries: List of {country: str, revenues: float}
        country_erp_lookup: Dict mapping country name to ERP

    Returns:
        Weighted average ERP
    """
    if not countries:
        return 0.0

    total_revenue = sum(c.get("revenues", 0) for c in countries)
    if total_revenue == 0:
        return 0.0

    weighted_erp = 0.0
    for c in countries:
        country_name = c.get("country", "")
        revenues = c.get("revenues", 0)
        erp = country_erp_lookup.get(country_name, 0.0)
        weight = revenues / total_revenue
        weighted_erp += erp * weight

    return weighted_erp


def calculate_levered_beta(
    unlevered_beta: float,
    debt: float,
    equity: float,
    tax_rate: float
) -> float:
    """
    Calculate levered beta using Hamada equation.

    Formula: β_levered = β_unlevered × (1 + (1 - t) × (D/E))
    """
    if equity <= 0:
        return unlevered_beta

    debt_to_equity = debt / equity
    return unlevered_beta * (1 + (1 - tax_rate) * debt_to_equity)


def estimate_market_value_of_debt(
    book_value: float,
    interest_expense: float,
    pretax_cost_of_debt: float,
    maturity: float
) -> float:
    """
    Estimate market value of debt using present value of coupon payments.

    Formula: MV = Interest × (1 - (1+r)^-n) / r + BV / (1+r)^n
    """
    if pretax_cost_of_debt <= 0 or maturity <= 0:
        return book_value

    r = pretax_cost_of_debt
    n = maturity

    # Present value of coupon payments
    pv_coupons = interest_expense * (1 - (1 + r) ** (-n)) / r

    # Present value of principal
    pv_principal = book_value / ((1 + r) ** n)

    return pv_coupons + pv_principal


def calculate_cost_of_capital(inputs: CostOfCapitalInputs) -> CostOfCapitalResult:
    """
    Calculate weighted average cost of capital using specified approach.

    Replicates the logic from Excel 'Cost of capital worksheet'.
    """
    # ============ Direct Input Approach ============
    if inputs.approach == "direct" and inputs.direct_coc is not None:
        return CostOfCapitalResult(
            approach="direct",
            risk_free_rate=inputs.risk_free_rate,
            unlevered_beta=inputs.unlevered_beta,
            levered_beta=inputs.unlevered_beta,
            equity_risk_premium=0,
            cost_of_equity=inputs.direct_coc,
            pretax_cost_of_debt=inputs.direct_coc,
            after_tax_cost_of_debt=inputs.direct_coc * (1 - inputs.marginal_tax_rate),
            market_value_equity=inputs.shares_outstanding * inputs.stock_price,
            market_value_debt=inputs.book_debt,
            market_value_preferred=0,
            equity_weight=1.0,
            debt_weight=0.0,
            preferred_weight=0.0,
            wacc=inputs.direct_coc,
            stable_wacc=inputs.direct_coc,
        )

    # ============ Detailed Calculation ============

    # Market value of equity
    mv_equity = inputs.shares_outstanding * inputs.stock_price

    # Equity Risk Premium
    if inputs.erp_approach == "will_input" and inputs.direct_erp is not None:
        erp = inputs.direct_erp
    elif inputs.erp_approach == "country_of_incorporation":
        erp = inputs.country_of_incorporation_erp or 0.05
    elif inputs.erp_approach == "operating_regions":
        erp = inputs.operating_regions_erp or 0.05
    else:  # operating_countries (default)
        erp = inputs.operating_countries_erp or 0.05

    # Pre-tax Cost of Debt
    if inputs.debt_approach == "direct_input" and inputs.direct_cost_of_debt is not None:
        pretax_cost_of_debt = inputs.direct_cost_of_debt
    elif inputs.debt_approach == "synthetic_rating":
        pretax_cost_of_debt = inputs.risk_free_rate + (inputs.synthetic_rating_spread or 0) + inputs.country_default_spread
    else:  # actual_rating
        pretax_cost_of_debt = inputs.risk_free_rate + (inputs.actual_rating_spread or 0) + inputs.country_default_spread

    # Market value of straight debt
    mv_straight_debt = estimate_market_value_of_debt(
        inputs.book_debt,
        inputs.interest_expense,
        pretax_cost_of_debt,
        inputs.debt_maturity
    )

    # Value of debt in operating leases
    mv_lease_debt = inputs.lease_debt_value

    # Convertible debt - estimate straight debt portion
    if inputs.convertible_market_value > 0 and inputs.convertible_maturity > 0:
        mv_convertible_debt = estimate_market_value_of_debt(
            inputs.convertible_book_value,
            inputs.convertible_interest,
            pretax_cost_of_debt,
            inputs.convertible_maturity
        )
        mv_convertible_equity = inputs.convertible_market_value - mv_convertible_debt
    else:
        mv_convertible_debt = 0
        mv_convertible_equity = 0

    # Total debt
    total_debt = mv_straight_debt + mv_convertible_debt + mv_lease_debt

    # Preferred stock
    mv_preferred = inputs.preferred_shares * inputs.preferred_price
    cost_of_preferred = (inputs.preferred_dividend / inputs.preferred_price) if inputs.preferred_price > 0 else 0

    # Total market value of capital
    total_equity = mv_equity + mv_convertible_equity
    total_capital = total_equity + total_debt + mv_preferred

    if total_capital <= 0:
        total_capital = 1  # Avoid division by zero

    # Weights
    equity_weight = total_equity / total_capital
    debt_weight = total_debt / total_capital
    preferred_weight = mv_preferred / total_capital

    # Levered Beta
    if inputs.beta_approach == "direct_input" and inputs.direct_beta is not None:
        levered_beta = inputs.direct_beta
    else:
        levered_beta = calculate_levered_beta(
            inputs.unlevered_beta,
            total_debt,
            total_equity,
            inputs.marginal_tax_rate
        )

    # Cost of Equity (CAPM)
    cost_of_equity = inputs.risk_free_rate + levered_beta * erp

    # After-tax Cost of Debt
    after_tax_cost_of_debt = pretax_cost_of_debt * (1 - inputs.marginal_tax_rate)

    # WACC
    wacc = (
        equity_weight * cost_of_equity +
        debt_weight * after_tax_cost_of_debt +
        preferred_weight * cost_of_preferred
    )

    # Stable WACC (default: risk-free + 4.5%)
    stable_wacc = inputs.risk_free_rate + 0.045

    # ============ Industry Average Approach ============
    if inputs.approach == "industry" and inputs.industry_coc is not None:
        # Adjust for risk-free rate difference
        rf_diff = inputs.risk_free_rate - inputs.industry_rf_at_calc
        adjusted_wacc = inputs.industry_coc + rf_diff
        return CostOfCapitalResult(
            approach="industry",
            risk_free_rate=inputs.risk_free_rate,
            unlevered_beta=inputs.unlevered_beta,
            levered_beta=levered_beta,
            equity_risk_premium=erp,
            cost_of_equity=cost_of_equity,
            pretax_cost_of_debt=pretax_cost_of_debt,
            after_tax_cost_of_debt=after_tax_cost_of_debt,
            market_value_equity=total_equity,
            market_value_debt=total_debt,
            market_value_preferred=mv_preferred,
            equity_weight=equity_weight,
            debt_weight=debt_weight,
            preferred_weight=preferred_weight,
            wacc=adjusted_wacc,
            stable_wacc=stable_wacc,
        )

    return CostOfCapitalResult(
        approach="detailed",
        risk_free_rate=inputs.risk_free_rate,
        unlevered_beta=inputs.unlevered_beta,
        levered_beta=levered_beta,
        equity_risk_premium=erp,
        cost_of_equity=cost_of_equity,
        pretax_cost_of_debt=pretax_cost_of_debt,
        after_tax_cost_of_debt=after_tax_cost_of_debt,
        market_value_equity=total_equity,
        market_value_debt=total_debt,
        market_value_preferred=mv_preferred,
        equity_weight=equity_weight,
        debt_weight=debt_weight,
        preferred_weight=preferred_weight,
        wacc=wacc,
        stable_wacc=stable_wacc,
    )


def calculate_time_varying_wacc(
    initial_wacc: float,
    stable_wacc: float,
    year: int,
    transition_start: int = 5,
    transition_end: int = 10
) -> float:
    """
    Calculate WACC for a specific year with linear transition to stable.

    Years 1-5: Initial WACC
    Years 6-10: Linear transition to stable WACC
    Year 10+: Stable WACC
    """
    if year <= transition_start:
        return initial_wacc
    elif year >= transition_end:
        return stable_wacc
    else:
        # Linear interpolation
        progress = (year - transition_start) / (transition_end - transition_start)
        return initial_wacc - (initial_wacc - stable_wacc) * progress
