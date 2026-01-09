"""
Employee Stock Option Valuation

Implements the dilution-adjusted Black-Scholes model from the 'Option value' sheet.
"""

import math
from dataclasses import dataclass
from scipy.stats import norm


@dataclass
class OptionInputs:
    """Inputs for option valuation."""
    stock_price: float
    strike_price: float
    time_to_maturity: float  # years
    volatility: float  # standard deviation
    risk_free_rate: float
    dividend_yield: float = 0.0
    num_options: float = 0  # millions
    shares_outstanding: float = 0  # millions


@dataclass
class OptionResult:
    """Black-Scholes option valuation result."""
    d1: float
    d2: float
    n_d1: float
    n_d2: float
    adjusted_stock_price: float
    value_per_option: float
    total_option_value: float


def calculate_black_scholes(inputs: OptionInputs) -> OptionResult:
    """
    Calculate option value using dilution-adjusted Black-Scholes.

    The model adjusts for dilution that occurs when options are exercised,
    as new shares are issued which reduces value per share.
    """
    if inputs.num_options <= 0 or inputs.shares_outstanding <= 0:
        return OptionResult(
            d1=0, d2=0, n_d1=0, n_d2=0,
            adjusted_stock_price=inputs.stock_price,
            value_per_option=0,
            total_option_value=0
        )

    # Initial estimate for iterative solution
    option_value_estimate = max(0, inputs.stock_price - inputs.strike_price)

    # Iterative calculation (options depend on their own value due to dilution)
    for _ in range(10):  # Usually converges in 2-3 iterations
        # Adjusted stock price accounts for dilution
        adjusted_s = (
            (inputs.stock_price * inputs.shares_outstanding +
             option_value_estimate * inputs.num_options) /
            (inputs.shares_outstanding + inputs.num_options)
        )

        # Dividend-adjusted interest rate
        div_adj_rate = inputs.risk_free_rate - inputs.dividend_yield

        # Black-Scholes parameters
        variance = inputs.volatility ** 2
        sqrt_t = math.sqrt(inputs.time_to_maturity)

        if inputs.strike_price <= 0 or adjusted_s <= 0 or sqrt_t <= 0:
            break

        d1 = (
            (math.log(adjusted_s / inputs.strike_price) +
             (div_adj_rate + variance / 2) * inputs.time_to_maturity) /
            (inputs.volatility * sqrt_t)
        )

        d2 = d1 - inputs.volatility * sqrt_t

        # Cumulative normal distribution
        n_d1 = norm.cdf(d1)
        n_d2 = norm.cdf(d2)

        # Option value (call option)
        option_value = (
            math.exp(-inputs.dividend_yield * inputs.time_to_maturity) * adjusted_s * n_d1 -
            inputs.strike_price * math.exp(-inputs.risk_free_rate * inputs.time_to_maturity) * n_d2
        )

        # Check for convergence
        if abs(option_value - option_value_estimate) < 0.0001:
            break

        option_value_estimate = option_value

    total_value = option_value_estimate * inputs.num_options

    return OptionResult(
        d1=d1,
        d2=d2,
        n_d1=n_d1,
        n_d2=n_d2,
        adjusted_stock_price=adjusted_s,
        value_per_option=option_value_estimate,
        total_option_value=total_value
    )
