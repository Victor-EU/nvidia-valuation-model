"""
Calculation API Routes

Endpoints for running DCF valuations and calculations.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ValuationModel, Country, Industry
from app.models.schemas import ValuationResult, CostOfCapitalResult
from app.services.cost_of_capital import (
    CostOfCapitalInputs,
    calculate_cost_of_capital,
    calculate_operating_countries_erp,
)
from app.services.dcf_valuation import DCFInputs, SegmentInputs, calculate_dcf_valuation
from app.services.option_valuation import OptionInputs, calculate_black_scholes
from app.services.rd_converter import RDInputs, calculate_rd_capitalization
from app.services.synthetic_rating import (
    SyntheticRatingInputs,
    get_synthetic_rating,
    get_spread_for_rating,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_country_erp_lookup(db: AsyncSession) -> dict[str, float]:
    """Build country name to ERP lookup dictionary."""
    result = await db.execute(select(Country))
    countries = result.scalars().all()
    return {c.name: float(c.equity_risk_premium or 0) for c in countries}


async def get_industry_data(
    industry_name: str,
    region: str,
    db: AsyncSession
) -> dict:
    """Get industry averages for a specific industry."""
    result = await db.execute(
        select(Industry).where(Industry.name == industry_name, Industry.region == region)
    )
    industry = result.scalar_one_or_none()

    if industry:
        return {
            "unlevered_beta": float(industry.unlevered_beta or 1.0),
            "cost_of_capital": float(industry.cost_of_capital or 0.10),
            "operating_margin": float(industry.operating_margin or 0.15),
            "sales_to_capital": float(industry.sales_to_capital or 1.5),
            "revenue_growth": float(industry.revenue_growth_5yr or 0.05),
        }

    return {
        "unlevered_beta": 1.0,
        "cost_of_capital": 0.10,
        "operating_margin": 0.15,
        "sales_to_capital": 1.5,
        "revenue_growth": 0.05,
    }


@router.post("/{model_id}", response_model=ValuationResult)
async def calculate_valuation(model_id: str, db: AsyncSession = Depends(get_db)):
    """
    Run full DCF valuation for a model.

    Calculates:
    1. Cost of capital (WACC)
    2. R&D capitalization adjustments
    3. Option value (if applicable)
    4. 10-year projections per segment
    5. Terminal value
    6. Enterprise value to equity value bridge
    7. Value per share
    """
    # Load model with relationships
    result = await db.execute(
        select(ValuationModel)
        .options(selectinload(ValuationModel.segments), selectinload(ValuationModel.cost_of_capital))
        .where(ValuationModel.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    logger.info(f"Calculating valuation for model: {model.name}")

    # Extract data from JSONB fields
    base = model.base_year_data or {}
    drivers = model.value_drivers or {}
    market = model.market_inputs or {}
    rd = model.rd_settings or {}
    options = model.option_settings or {}
    overrides = model.overrides or {}

    # ========== 1. R&D Capitalization ==========
    rd_result = None
    rd_asset = 0
    rd_adjustment = 0

    if rd.get("capitalize_rd"):
        rd_inputs = RDInputs(
            amortization_years=rd.get("amortization_years", 5),
            current_rd_expense=rd.get("current_rd", 0),
            historical_rd=rd.get("rd_expenses", []),
        )
        rd_result = calculate_rd_capitalization(
            rd_inputs,
            marginal_tax_rate=base.get("marginal_tax_rate", 0.25)
        )
        rd_asset = rd_result.research_asset_value
        rd_adjustment = rd_result.operating_income_adjustment

    # ========== 2. Cost of Capital ==========
    country_erp_lookup = await get_country_erp_lookup(db)
    industry_data = await get_industry_data(
        market.get("industry_us", ""),
        "US",
        db
    )

    # Get operating countries ERP
    coc_settings = model.cost_of_capital
    operating_countries = []
    if coc_settings and coc_settings.operating_countries:
        operating_countries = coc_settings.operating_countries

    op_countries_erp = calculate_operating_countries_erp(operating_countries, country_erp_lookup)

    # Get country of incorporation ERP
    country_erp = country_erp_lookup.get(market.get("country", "United States"), 0.05)

    # Determine cost of debt
    if coc_settings and coc_settings.debt_approach == "actual_rating":
        rating_spread = get_spread_for_rating(coc_settings.actual_rating or "A2/A") or 0.0142
    else:
        synthetic = get_synthetic_rating(SyntheticRatingInputs(
            ebit=base.get("operating_income", 0) + rd_adjustment,
            interest_expense=base.get("interest_expense", 0),
            firm_type=coc_settings.firm_type if coc_settings else 1
        ))
        rating_spread = synthetic.estimated_spread

    coc_inputs = CostOfCapitalInputs(
        approach=coc_settings.approach if coc_settings else "detailed",
        direct_coc=float(coc_settings.direct_coc) if coc_settings and coc_settings.direct_coc else None,
        shares_outstanding=base.get("shares", 0),
        stock_price=base.get("stock_price", 0),
        risk_free_rate=market.get("risk_free_rate", 0.045),
        beta_approach=coc_settings.beta_approach if coc_settings else "single_business_us",
        unlevered_beta=industry_data["unlevered_beta"],
        direct_beta=float(coc_settings.direct_beta) if coc_settings and coc_settings.direct_beta else None,
        erp_approach=coc_settings.erp_approach if coc_settings else "operating_countries",
        direct_erp=float(coc_settings.direct_erp) if coc_settings and coc_settings.direct_erp else None,
        operating_countries_erp=op_countries_erp if op_countries_erp > 0 else country_erp,
        country_of_incorporation_erp=country_erp,
        book_debt=base.get("book_debt", 0),
        interest_expense=base.get("interest_expense", 0),
        debt_maturity=float(coc_settings.debt_maturity) if coc_settings else 3,
        actual_rating_spread=rating_spread,
        marginal_tax_rate=base.get("marginal_tax_rate", 0.25),
        industry_coc=industry_data["cost_of_capital"],
    )

    coc_result = calculate_cost_of_capital(coc_inputs)

    # Determine stable WACC
    if overrides.get("override_stable_coc") and overrides.get("stable_coc"):
        stable_wacc = overrides["stable_coc"]
    else:
        stable_wacc = coc_result.stable_wacc

    # ========== 3. Option Value ==========
    option_value = 0
    if options.get("has_options"):
        option_inputs = OptionInputs(
            stock_price=base.get("stock_price", 0),
            strike_price=options.get("avg_strike", 0),
            time_to_maturity=options.get("avg_maturity", 5),
            volatility=options.get("std_dev", 0.40),
            risk_free_rate=market.get("risk_free_rate", 0.045),
            num_options=options.get("num_options", 0),
            shares_outstanding=base.get("shares", 0),
        )
        option_result = calculate_black_scholes(option_inputs)
        option_value = option_result.total_option_value

    # ========== 4. Build Segment Inputs ==========
    segment_inputs = []

    # Calculate base revenues for 'rest' segment (total - AI - Auto)
    total_revenues = base.get("revenues", 0)
    ai_revenues = 0
    auto_revenues = 0

    for seg in model.segments:
        seg_inputs = seg.inputs or {}
        if seg.segment_type == "ai":
            ai_revenues = (seg_inputs.get("total_market_current", 0) *
                          seg_inputs.get("market_share_current", 0))
        elif seg.segment_type == "auto":
            auto_revenues = (seg_inputs.get("total_market_current", 0) *
                            seg_inputs.get("market_share_current", 0))

    rest_revenues = total_revenues - ai_revenues - auto_revenues

    # Validate: segment revenues shouldn't exceed total revenue
    if rest_revenues < 0:
        logger.warning(
            f"Segment revenues exceed total: AI=${ai_revenues/1e9:.1f}B + Auto=${auto_revenues/1e9:.1f}B = "
            f"${(ai_revenues + auto_revenues)/1e9:.1f}B > Total=${total_revenues/1e9:.1f}B. "
            f"Rest segment will be negative (${rest_revenues/1e9:.1f}B). "
            "Check segment market size and share inputs."
        )
        raise HTTPException(
            status_code=400,
            detail=f"Segment revenues (AI: ${ai_revenues/1e9:.1f}B + Auto: ${auto_revenues/1e9:.1f}B = ${(ai_revenues + auto_revenues)/1e9:.1f}B) "
                   f"exceed total company revenue (${total_revenues/1e9:.1f}B). "
                   "Please reduce market size or market share for AI/Auto segments."
        )

    for seg in model.segments:
        seg_inputs = seg.inputs or {}

        if seg.segment_type == "rest":
            segment_inputs.append(SegmentInputs(
                name=seg.name,
                segment_type="rest",
                base_revenues=rest_revenues,
                base_operating_margin=(base.get("operating_income", 0) + rd_adjustment) / total_revenues if total_revenues > 0 else 0,
            ))
        else:
            segment_inputs.append(SegmentInputs(
                name=seg.name,
                segment_type=seg.segment_type,
                total_market_current=seg_inputs.get("total_market_current"),
                total_market_year10=seg_inputs.get("total_market_year10"),
                market_share_current=seg_inputs.get("market_share_current"),
                market_share_year10=seg_inputs.get("market_share_year10"),
                operating_margin_current=seg_inputs.get("operating_margin_current"),
                operating_margin_year10=seg_inputs.get("operating_margin_year10"),
            ))

    # ========== 5. Run DCF Valuation ==========
    dcf_inputs = DCFInputs(
        total_revenues=total_revenues,
        total_operating_income=base.get("operating_income", 0) + rd_adjustment,
        book_equity=base.get("book_equity", 0),
        book_debt=base.get("book_debt", 0),
        cash=base.get("cash", 0),
        cross_holdings=base.get("cross_holdings", 0),
        minority_interests=base.get("minority_interests", 0),
        shares_outstanding=base.get("shares", 0),
        stock_price=base.get("stock_price", 0),
        effective_tax_rate=base.get("effective_tax_rate", 0.21),
        marginal_tax_rate=base.get("marginal_tax_rate", 0.25),
        revenue_growth_yr1=drivers.get("revenue_growth_yr1", 0.10),
        operating_margin_yr1=drivers.get("operating_margin_yr1", 0.20),
        compounded_growth_2_5=drivers.get("compounded_growth_2_5", 0.10),
        target_margin=drivers.get("target_margin", 0.20),
        convergence_year=drivers.get("convergence_year", 5),
        sales_to_capital_1_5=drivers.get("sales_to_capital_1_5", 2.0),
        sales_to_capital_6_10=drivers.get("sales_to_capital_6_10", 2.0),
        risk_free_rate=market.get("risk_free_rate", 0.045),
        initial_wacc=coc_result.wacc,
        stable_wacc=stable_wacc,
        override_stable_roic=overrides.get("override_stable_roic", False),
        stable_roic=overrides.get("stable_roic"),
        reinvestment_lag=overrides.get("reinvestment_lag", 1),
        failure_probability=overrides.get("failure_prob", 0) if overrides.get("override_failure") else 0,
        distress_proceeds_type=overrides.get("distress_proceeds_type", "V"),
        distress_proceeds_pct=overrides.get("distress_proceeds_pct", 0.5),
        nol=overrides.get("nol", 0) if overrides.get("override_nol") else 0,
        override_growth=overrides.get("override_growth", False),
        perpetual_growth=overrides.get("perpetual_growth"),
        rd_asset_value=rd_asset,
        rd_operating_adjustment=rd_adjustment,
        option_value=option_value,
        segments=segment_inputs,
    )

    dcf_result = calculate_dcf_valuation(dcf_inputs)

    # ========== 6. Format Response ==========
    from app.models.schemas import SegmentProjections, YearProjection

    segment_projections = []
    for sp in dcf_result.segment_projections:
        projections = [
            YearProjection(
                year=p.year,
                revenue_growth=p.revenue_growth,
                revenues=p.revenues,
                operating_margin=p.operating_margin,
                ebit=p.ebit,
                ebit_1_t=p.ebit_1_t,
                reinvestment=p.reinvestment,
                fcff=p.fcff,
                cost_of_capital=p.cost_of_capital,
                discount_factor=p.cumulative_discount_factor,
                pv_fcff=p.pv_fcff,
            )
            for p in sp.projections
        ]

        segment_projections.append(SegmentProjections(
            segment_name=sp.segment_name,
            segment_type=sp.segment_type,
            projections=projections,
            terminal_value=sp.terminal_value,
            pv_terminal=sp.pv_terminal,
            segment_value=sp.segment_value,
        ))

    logger.info(f"Valuation complete. Value per share: ${dcf_result.value_per_share:.2f}")

    return ValuationResult(
        segment_projections=segment_projections,
        cost_of_capital=CostOfCapitalResult(
            approach=coc_result.approach,
            risk_free_rate=coc_result.risk_free_rate,
            unlevered_beta=coc_result.unlevered_beta,
            levered_beta=coc_result.levered_beta,
            equity_risk_premium=coc_result.equity_risk_premium,
            cost_of_equity=coc_result.cost_of_equity,
            pretax_cost_of_debt=coc_result.pretax_cost_of_debt,
            after_tax_cost_of_debt=coc_result.after_tax_cost_of_debt,
            equity_weight=coc_result.equity_weight,
            debt_weight=coc_result.debt_weight,
            wacc=coc_result.wacc,
            stable_wacc=stable_wacc,
        ),
        pv_fcff_total=dcf_result.pv_fcff_total,
        pv_terminal_total=dcf_result.pv_terminal_total,
        going_concern_value=dcf_result.going_concern_value,
        failure_adjustment=dcf_result.failure_adjustment,
        operating_assets_value=dcf_result.operating_assets_value,
        debt=dcf_result.debt,
        minority_interests=dcf_result.minority_interests,
        cash=dcf_result.cash,
        non_operating_assets=dcf_result.non_operating_assets,
        equity_value=dcf_result.equity_value,
        option_value=dcf_result.option_value,
        equity_in_common=dcf_result.equity_in_common,
        shares_outstanding=dcf_result.shares_outstanding,
        value_per_share=dcf_result.value_per_share,
        current_price=dcf_result.current_price,
        price_to_value=dcf_result.price_to_value,
        rd_asset_value=rd_asset if rd_result else None,
        rd_amortization=rd_result.current_amortization if rd_result else None,
        rd_operating_adjustment=rd_adjustment if rd_result else None,
    )
