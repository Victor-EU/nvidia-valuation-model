"""
DCF Valuation Engine

Core DCF calculation logic that replicates the 'Valuation output' sheet from Excel.
Supports multi-segment valuation with:
- Revenue projections with growth rate decay
- Operating margin convergence
- Reinvestment with configurable lag
- Terminal value (Gordon Growth)
- Time-varying cost of capital
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class SegmentInputs:
    """Inputs for a business segment."""
    name: str
    segment_type: str  # 'rest', 'ai', 'auto'

    # Base year
    base_revenues: float = 0
    base_operating_margin: float = 0

    # For 'rest' segment - uses global drivers
    # For 'ai'/'auto' segments - uses market-based inputs
    total_market_current: Optional[float] = None
    total_market_year10: Optional[float] = None
    market_share_current: Optional[float] = None
    market_share_year10: Optional[float] = None
    operating_margin_current: Optional[float] = None
    operating_margin_year10: Optional[float] = None


@dataclass
class DCFInputs:
    """All inputs needed for DCF valuation."""
    # Base year data
    total_revenues: float = 0
    total_operating_income: float = 0
    book_equity: float = 0
    book_debt: float = 0
    cash: float = 0
    cross_holdings: float = 0
    minority_interests: float = 0
    shares_outstanding: float = 0
    stock_price: float = 0
    effective_tax_rate: float = 0.21
    marginal_tax_rate: float = 0.25

    # Value drivers
    revenue_growth_yr1: float = 0.10
    operating_margin_yr1: float = 0.20
    compounded_growth_2_5: float = 0.10
    target_margin: float = 0.20
    convergence_year: int = 5
    sales_to_capital_1_5: float = 2.0
    sales_to_capital_6_10: float = 2.0

    # Market inputs
    risk_free_rate: float = 0.045

    # Cost of capital
    initial_wacc: float = 0.10
    stable_wacc: float = 0.085

    # Overrides
    override_stable_roic: bool = False
    stable_roic: Optional[float] = None
    reinvestment_lag: int = 1  # 0-3 years
    failure_probability: float = 0
    distress_proceeds_type: str = "V"  # B=book, V=fair value
    distress_proceeds_pct: float = 0.5
    nol: float = 0
    override_growth: bool = False
    perpetual_growth: Optional[float] = None

    # R&D adjustments
    rd_asset_value: float = 0
    rd_operating_adjustment: float = 0

    # Lease adjustments
    lease_debt_value: float = 0
    lease_operating_adjustment: float = 0

    # Option value
    option_value: float = 0

    # Segments
    segments: list[SegmentInputs] = field(default_factory=list)


@dataclass
class YearProjection:
    """Projection for a single year."""
    year: int
    revenue_growth: float
    revenues: float
    operating_margin: float
    ebit: float
    tax_rate: float
    ebit_1_t: float
    reinvestment: float
    fcff: float
    nol_remaining: float
    cost_of_capital: float
    discount_factor: float
    cumulative_discount_factor: float
    pv_fcff: float


@dataclass
class SegmentProjections:
    """Complete projections for a segment."""
    segment_name: str
    segment_type: str
    base_revenues: float
    base_margin: float
    base_ebit: float
    projections: list[YearProjection]
    terminal_fcff: float
    terminal_value: float
    pv_terminal: float
    segment_value: float


@dataclass
class DCFResult:
    """Complete DCF valuation result."""
    segment_projections: list[SegmentProjections]

    # Aggregate values
    pv_fcff_total: float
    pv_terminal_total: float
    going_concern_value: float

    # Adjustments
    failure_adjustment: float
    operating_assets_value: float

    # Bridge to equity
    debt: float
    minority_interests: float
    cash: float
    non_operating_assets: float
    equity_value: float
    option_value: float
    equity_in_common: float

    # Per share
    shares_outstanding: float
    value_per_share: float
    current_price: float
    price_to_value: float

    # Invested capital and ROIC
    base_invested_capital: float
    year10_invested_capital: float
    year10_roic: float
    stable_roic: float


def calculate_growth_rate(
    year: int,
    initial_growth: float,
    risk_free_rate: float,
    override_growth: bool = False,
    perpetual_growth: Optional[float] = None
) -> float:
    """
    Calculate growth rate for a given year.

    Years 1-5: Constant at initial growth
    Years 6-10: Linear decay to risk-free rate (or perpetual growth)
    Terminal: Risk-free rate (or perpetual growth)
    """
    terminal_growth = perpetual_growth if override_growth and perpetual_growth is not None else risk_free_rate

    if year <= 5:
        return initial_growth
    elif year <= 10:
        # Linear interpolation from year 5 to year 10
        progress = (year - 5) / 5
        return initial_growth - (initial_growth - terminal_growth) * progress
    else:
        return terminal_growth


def calculate_margin(
    year: int,
    initial_margin: float,
    target_margin: float,
    convergence_year: int
) -> float:
    """
    Calculate operating margin for a given year with convergence to target.

    Margin converges linearly to target by convergence_year.
    """
    if year >= convergence_year:
        return target_margin
    else:
        # Linear interpolation
        progress = year / convergence_year
        return initial_margin + (target_margin - initial_margin) * progress


def calculate_tax_rate(
    year: int,
    effective_rate: float,
    marginal_rate: float,
    override_tax: bool = False
) -> float:
    """
    Calculate tax rate for a given year.

    Years 1-5: Effective rate
    Years 6-10: Linear transition to marginal rate
    Terminal: Marginal rate (unless overridden)
    """
    if override_tax:
        return effective_rate

    if year <= 5:
        return effective_rate
    elif year <= 10:
        progress = (year - 5) / 5
        return effective_rate + (marginal_rate - effective_rate) * progress
    else:
        return marginal_rate


def calculate_wacc(
    year: int,
    initial_wacc: float,
    stable_wacc: float
) -> float:
    """
    Calculate WACC for a given year.

    Years 1-5: Initial WACC
    Years 6-10: Linear transition to stable WACC
    Terminal: Stable WACC
    """
    if year <= 5:
        return initial_wacc
    elif year <= 10:
        progress = (year - 5) / 5
        return initial_wacc - (initial_wacc - stable_wacc) * progress
    else:
        return stable_wacc


def calculate_market_based_revenues(
    year: int,
    total_market_current: float,
    total_market_year10: float,
    market_share_current: float,
    market_share_year10: float
) -> tuple[float, float, float]:
    """
    Calculate revenues based on total market size and market share.
    Used for AI and Auto segments.

    Returns: (total_market, market_share, revenues)
    """
    if year <= 5:
        # First 5 years: more rapid market growth (60% of total growth)
        market_growth_factor = 0.6
        year5_market = total_market_current + (total_market_year10 - total_market_current) * market_growth_factor
        progress = year / 5
        total_market = total_market_current + (year5_market - total_market_current) * progress
    else:
        # Years 6-10: remaining market growth
        market_growth_factor = 0.6
        year5_market = total_market_current + (total_market_year10 - total_market_current) * market_growth_factor
        progress = (year - 5) / 5
        total_market = year5_market + (total_market_year10 - year5_market) * progress

    # Market share changes linearly over 10 years
    share_progress = year / 10
    market_share = market_share_current + (market_share_year10 - market_share_current) * share_progress

    revenues = total_market * market_share
    return total_market, market_share, revenues


def calculate_segment_projections(
    segment: SegmentInputs,
    inputs: DCFInputs,
) -> SegmentProjections:
    """
    Calculate 10-year projections and terminal value for a single segment.
    """
    projections = []
    cumulative_df = 1.0
    nol = inputs.nol if segment.segment_type == "rest" else 0  # Only apply NOL to first segment

    # Track invested capital for ROIC calculation
    invested_capital = inputs.book_equity + inputs.book_debt - inputs.cash + inputs.rd_asset_value

    # Determine base values
    if segment.segment_type == "rest":
        # Rest segment uses global value drivers
        base_revenues = segment.base_revenues
        initial_margin = inputs.operating_margin_yr1
        target_margin = inputs.target_margin
        initial_growth = inputs.revenue_growth_yr1
    else:
        # AI/Auto segments use market-based inputs
        base_revenues = (segment.total_market_current or 0) * (segment.market_share_current or 0)
        initial_margin = segment.operating_margin_current or inputs.operating_margin_yr1
        target_margin = segment.operating_margin_year10 or inputs.target_margin
        initial_growth = 0  # Will be calculated from market dynamics

    prev_revenues = base_revenues
    terminal_growth = inputs.perpetual_growth if inputs.override_growth else inputs.risk_free_rate

    for year in range(1, 11):
        # Revenue calculation
        if segment.segment_type == "rest":
            growth = calculate_growth_rate(
                year, initial_growth, inputs.risk_free_rate,
                inputs.override_growth, inputs.perpetual_growth
            )
            revenues = prev_revenues * (1 + growth)
        else:
            # Market-based revenue calculation
            _, _, revenues = calculate_market_based_revenues(
                year,
                segment.total_market_current or 0,
                segment.total_market_year10 or 0,
                segment.market_share_current or 0,
                segment.market_share_year10 or 0
            )
            growth = (revenues / prev_revenues - 1) if prev_revenues > 0 else 0

        # Operating margin
        margin = calculate_margin(
            year,
            initial_margin,
            target_margin,
            inputs.convergence_year
        )

        # EBIT
        ebit = revenues * margin

        # Tax rate
        tax_rate = calculate_tax_rate(
            year,
            inputs.effective_tax_rate,
            inputs.marginal_tax_rate
        )

        # EBIT(1-t) with NOL handling
        if ebit <= 0:
            ebit_1_t = ebit
            nol = nol - ebit  # Add loss to NOL
        elif nol > ebit:
            ebit_1_t = ebit  # Fully shielded by NOL
            nol = nol - ebit
        elif nol > 0:
            taxable = ebit - nol
            ebit_1_t = ebit - taxable * tax_rate
            nol = 0
        else:
            ebit_1_t = ebit * (1 - tax_rate)

        # Reinvestment (with lag)
        sales_to_capital = inputs.sales_to_capital_1_5 if year <= 5 else inputs.sales_to_capital_6_10

        # Calculate future revenue for reinvestment with lag
        if inputs.reinvestment_lag == 0:
            # No lag: reinvestment based on current year growth
            delta_revenue = revenues - prev_revenues
        elif inputs.reinvestment_lag == 1:
            # 1-year lag (default): reinvestment for next year's growth
            if segment.segment_type == "rest":
                next_growth = calculate_growth_rate(
                    year + 1, initial_growth, inputs.risk_free_rate,
                    inputs.override_growth, inputs.perpetual_growth
                )
                next_revenues = revenues * (1 + next_growth)
            else:
                _, _, next_revenues = calculate_market_based_revenues(
                    year + 1,
                    segment.total_market_current or 0,
                    segment.total_market_year10 or 0,
                    segment.market_share_current or 0,
                    segment.market_share_year10 or 0
                )
            delta_revenue = next_revenues - revenues
        else:
            # 2 or 3 year lag
            lag = inputs.reinvestment_lag
            if segment.segment_type == "rest":
                future_growth = calculate_growth_rate(
                    min(year + lag, 11), initial_growth, inputs.risk_free_rate,
                    inputs.override_growth, inputs.perpetual_growth
                )
                # Project forward
                future_revenues = revenues
                for _ in range(lag):
                    future_revenues *= (1 + future_growth)
                prior_revenues = revenues
                for _ in range(lag - 1):
                    prior_revenues *= (1 + future_growth)
                delta_revenue = future_revenues - prior_revenues
            else:
                _, _, future_revenues = calculate_market_based_revenues(
                    min(year + lag, 10),
                    segment.total_market_current or 0,
                    segment.total_market_year10 or 0,
                    segment.market_share_current or 0,
                    segment.market_share_year10 or 0
                )
                _, _, prior_revenues = calculate_market_based_revenues(
                    min(year + lag - 1, 10),
                    segment.total_market_current or 0,
                    segment.total_market_year10 or 0,
                    segment.market_share_current or 0,
                    segment.market_share_year10 or 0
                )
                delta_revenue = future_revenues - prior_revenues

        reinvestment = delta_revenue / sales_to_capital if sales_to_capital > 0 else 0
        reinvestment = max(0, reinvestment)  # Can't have negative reinvestment

        # FCFF
        fcff = ebit_1_t - reinvestment

        # Cost of capital and discount factor
        wacc = calculate_wacc(year, inputs.initial_wacc, inputs.stable_wacc)
        discount_factor = 1 / (1 + wacc)
        cumulative_df *= discount_factor

        # Present value
        pv_fcff = fcff * cumulative_df

        # Track invested capital
        invested_capital += reinvestment

        projections.append(YearProjection(
            year=year,
            revenue_growth=growth,
            revenues=revenues,
            operating_margin=margin,
            ebit=ebit,
            tax_rate=tax_rate,
            ebit_1_t=ebit_1_t,
            reinvestment=reinvestment,
            fcff=fcff,
            nol_remaining=nol,
            cost_of_capital=wacc,
            discount_factor=discount_factor,
            cumulative_discount_factor=cumulative_df,
            pv_fcff=pv_fcff,
        ))

        prev_revenues = revenues

    # Terminal value calculation
    year10 = projections[-1]
    terminal_margin = target_margin

    # Terminal EBIT(1-t)
    terminal_revenues = year10.revenues * (1 + terminal_growth)
    terminal_ebit = terminal_revenues * terminal_margin
    terminal_ebit_1_t = terminal_ebit * (1 - inputs.marginal_tax_rate)

    # Terminal reinvestment rate
    stable_roic = inputs.stable_roic if inputs.override_stable_roic else inputs.stable_wacc
    if stable_roic > 0:
        reinvestment_rate = terminal_growth / stable_roic
    else:
        reinvestment_rate = 0

    terminal_reinvestment = terminal_ebit_1_t * reinvestment_rate
    terminal_fcff = terminal_ebit_1_t - terminal_reinvestment

    # Gordon Growth terminal value
    if inputs.stable_wacc > terminal_growth:
        terminal_value = terminal_fcff / (inputs.stable_wacc - terminal_growth)
    else:
        terminal_value = 0

    # Present value of terminal value
    pv_terminal = terminal_value * year10.cumulative_discount_factor

    # Total segment value
    pv_fcff_sum = sum(p.pv_fcff for p in projections)
    segment_value = pv_fcff_sum + pv_terminal

    return SegmentProjections(
        segment_name=segment.name,
        segment_type=segment.segment_type,
        base_revenues=base_revenues,
        base_margin=segment.base_operating_margin,
        base_ebit=base_revenues * segment.base_operating_margin,
        projections=projections,
        terminal_fcff=terminal_fcff,
        terminal_value=terminal_value,
        pv_terminal=pv_terminal,
        segment_value=segment_value,
    )


def calculate_dcf_valuation(inputs: DCFInputs) -> DCFResult:
    """
    Calculate complete DCF valuation across all segments.
    """
    # Calculate projections for each segment
    segment_projections = []
    for segment in inputs.segments:
        proj = calculate_segment_projections(segment, inputs)
        segment_projections.append(proj)

    # Aggregate values
    pv_fcff_total = sum(sp.segment_value - sp.pv_terminal for sp in segment_projections)
    pv_terminal_total = sum(sp.pv_terminal for sp in segment_projections)
    going_concern_value = sum(sp.segment_value for sp in segment_projections)

    # Failure adjustment
    if inputs.failure_probability > 0:
        if inputs.distress_proceeds_type == "B":
            distress_value = (inputs.book_equity + inputs.book_debt) * inputs.distress_proceeds_pct
        else:
            distress_value = going_concern_value * inputs.distress_proceeds_pct

        operating_assets_value = (
            going_concern_value * (1 - inputs.failure_probability) +
            distress_value * inputs.failure_probability
        )
        failure_adjustment = going_concern_value - operating_assets_value
    else:
        operating_assets_value = going_concern_value
        failure_adjustment = 0

    # Bridge to equity value
    debt = inputs.book_debt + inputs.lease_debt_value
    equity_value = (
        operating_assets_value -
        debt -
        inputs.minority_interests +
        inputs.cash +
        inputs.cross_holdings
    )

    # Subtract option value
    equity_in_common = equity_value - inputs.option_value

    # Per share
    value_per_share = equity_in_common / inputs.shares_outstanding if inputs.shares_outstanding > 0 else 0
    price_to_value = inputs.stock_price / value_per_share if value_per_share > 0 else 0

    # Calculate ROIC metrics
    base_invested_capital = inputs.book_equity + inputs.book_debt - inputs.cash + inputs.rd_asset_value

    # Year 10 invested capital (sum of reinvestments)
    total_reinvestment = sum(
        sum(p.reinvestment for p in sp.projections)
        for sp in segment_projections
    )
    year10_invested_capital = base_invested_capital + total_reinvestment

    # Year 10 ROIC
    year10_ebit_1_t = sum(sp.projections[-1].ebit_1_t for sp in segment_projections)
    year10_roic = year10_ebit_1_t / year10_invested_capital if year10_invested_capital > 0 else 0

    # Stable ROIC
    stable_roic = inputs.stable_roic if inputs.override_stable_roic else inputs.stable_wacc

    return DCFResult(
        segment_projections=segment_projections,
        pv_fcff_total=pv_fcff_total,
        pv_terminal_total=pv_terminal_total,
        going_concern_value=going_concern_value,
        failure_adjustment=failure_adjustment,
        operating_assets_value=operating_assets_value,
        debt=debt,
        minority_interests=inputs.minority_interests,
        cash=inputs.cash,
        non_operating_assets=inputs.cross_holdings,
        equity_value=equity_value,
        option_value=inputs.option_value,
        equity_in_common=equity_in_common,
        shares_outstanding=inputs.shares_outstanding,
        value_per_share=value_per_share,
        current_price=inputs.stock_price,
        price_to_value=price_to_value,
        base_invested_capital=base_invested_capital,
        year10_invested_capital=year10_invested_capital,
        year10_roic=year10_roic,
        stable_roic=stable_roic,
    )
