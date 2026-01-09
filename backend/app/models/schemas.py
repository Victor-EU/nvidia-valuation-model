from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID


# ============ Reference Data Schemas ============

class CountryBase(BaseModel):
    name: str
    moodys_rating: Optional[str] = None
    adj_default_spread: Optional[float] = None
    equity_risk_premium: Optional[float] = None
    country_risk_premium: Optional[float] = None
    corporate_tax_rate: Optional[float] = None


class CountryResponse(CountryBase):
    id: int

    class Config:
        from_attributes = True


class IndustryBase(BaseModel):
    name: str
    region: str = "US"
    num_firms: Optional[int] = None
    revenue_growth_5yr: Optional[float] = None
    operating_margin: Optional[float] = None
    after_tax_roc: Optional[float] = None
    effective_tax_rate: Optional[float] = None
    unlevered_beta: Optional[float] = None
    levered_beta: Optional[float] = None
    cost_of_equity: Optional[float] = None
    std_dev_stock: Optional[float] = None
    pretax_cost_of_debt: Optional[float] = None
    debt_to_capital: Optional[float] = None
    cost_of_capital: Optional[float] = None
    sales_to_capital: Optional[float] = None
    ev_to_sales: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    ev_to_ebit: Optional[float] = None
    price_to_book: Optional[float] = None
    trailing_pe: Optional[float] = None


class IndustryResponse(IndustryBase):
    id: int

    class Config:
        from_attributes = True


# ============ Base Year Data ============

class BaseYearData(BaseModel):
    revenues: float = Field(default=0, description="Total revenues in millions")
    operating_income: float = Field(default=0, description="Operating income (EBIT)")
    interest_expense: float = Field(default=0, description="Interest expense on debt")
    book_equity: float = Field(default=0, description="Book value of equity")
    book_debt: float = Field(default=0, description="Book value of debt")
    cash: float = Field(default=0, description="Cash and marketable securities")
    cross_holdings: float = Field(default=0, description="Cross holdings and non-operating assets")
    minority_interests: float = Field(default=0, description="Minority interests")
    shares: float = Field(default=0, description="Shares outstanding in millions")
    stock_price: float = Field(default=0, description="Current stock price")
    effective_tax_rate: float = Field(default=0.21, description="Effective tax rate")
    marginal_tax_rate: float = Field(default=0.25, description="Marginal tax rate")
    last_year_revenues: Optional[float] = Field(default=None, description="Previous year revenues")
    last_year_ebit: Optional[float] = Field(default=None, description="Previous year EBIT")


# ============ Value Drivers ============

class ValueDrivers(BaseModel):
    revenue_growth_yr1: float = Field(default=0.10, description="Revenue growth rate for year 1")
    operating_margin_yr1: float = Field(default=0.20, description="Operating margin for year 1")
    compounded_growth_2_5: float = Field(default=0.10, description="CAGR for years 2-5")
    target_margin: float = Field(default=0.20, description="Target operating margin")
    convergence_year: int = Field(default=5, description="Year to reach target margin")
    sales_to_capital_1_5: float = Field(default=2.0, description="Sales/Capital for years 1-5")
    sales_to_capital_6_10: float = Field(default=2.0, description="Sales/Capital for years 6-10")


# ============ Market Inputs ============

class MarketInputs(BaseModel):
    risk_free_rate: float = Field(default=0.045, description="Risk-free rate (10yr Treasury)")
    country: str = Field(default="United States", description="Country of incorporation")
    industry_us: str = Field(default="", description="US industry classification")
    industry_global: str = Field(default="", description="Global industry classification")


# ============ R&D Settings ============

class RDSettings(BaseModel):
    capitalize_rd: bool = Field(default=False, description="Whether to capitalize R&D")
    amortization_years: int = Field(default=5, description="Years to amortize R&D")
    current_rd: float = Field(default=0, description="Current year R&D expense")
    rd_expenses: list[float] = Field(default_factory=list, description="Historical R&D expenses [y-1, y-2, ...]")


# ============ Lease Settings ============

class LeaseSettings(BaseModel):
    has_leases: bool = Field(default=False, description="Whether company has operating leases")
    lease_expense: float = Field(default=0, description="Current year lease expense")
    commitments: list[float] = Field(default_factory=list, description="Lease commitments [y1, y2, y3, y4, y5, beyond]")


# ============ Option Settings ============

class OptionSettings(BaseModel):
    has_options: bool = Field(default=False, description="Whether company has employee options")
    num_options: float = Field(default=0, description="Number of options outstanding (millions)")
    avg_strike: float = Field(default=0, description="Average strike price")
    avg_maturity: float = Field(default=5, description="Average time to maturity (years)")
    std_dev: float = Field(default=0.40, description="Stock price standard deviation")


# ============ Override Settings ============

class Overrides(BaseModel):
    override_stable_coc: bool = Field(default=False)
    stable_coc: Optional[float] = Field(default=None, description="Stable cost of capital after year 10")
    override_stable_roic: bool = Field(default=False)
    stable_roic: Optional[float] = Field(default=None, description="Stable ROIC after year 10")
    override_failure: bool = Field(default=False)
    failure_prob: float = Field(default=0, description="Probability of failure")
    distress_proceeds_type: str = Field(default="V", description="B=Book value, V=Fair value")
    distress_proceeds_pct: float = Field(default=0.5, description="Proceeds as % of book/fair value")
    override_reinvestment_lag: bool = Field(default=False)
    reinvestment_lag: int = Field(default=1, description="Years between reinvestment and growth (0-3)")
    override_tax_rate: bool = Field(default=False)
    override_nol: bool = Field(default=False)
    nol: float = Field(default=0, description="Net operating loss carryforward")
    override_risk_free: bool = Field(default=False)
    future_risk_free: Optional[float] = Field(default=None, description="Risk-free rate after year 10")
    override_growth: bool = Field(default=False)
    perpetual_growth: Optional[float] = Field(default=None, description="Growth rate in perpetuity")


# ============ Segment Inputs ============

class SegmentInputs(BaseModel):
    total_market_current: Optional[float] = Field(default=None, description="Current total market size")
    total_market_year10: Optional[float] = Field(default=None, description="Year 10 total market size")
    market_share_current: Optional[float] = Field(default=None, description="Current market share (0-1)")
    market_share_year10: Optional[float] = Field(default=None, description="Year 10 market share (0-1)")
    operating_margin_current: Optional[float] = Field(default=None, description="Current operating margin")
    operating_margin_year10: Optional[float] = Field(default=None, description="Year 10 operating margin")


class BusinessSegmentCreate(BaseModel):
    name: str
    segment_type: str = "rest"  # 'rest', 'ai', 'auto'
    segment_order: int = 0
    inputs: SegmentInputs = Field(default_factory=SegmentInputs)


class BusinessSegmentResponse(BaseModel):
    id: UUID
    name: str
    segment_type: Optional[str]
    segment_order: int
    inputs: dict

    class Config:
        from_attributes = True


# ============ Cost of Capital Settings ============

class OperatingCountry(BaseModel):
    country: str
    revenues: float


class CostOfCapitalCreate(BaseModel):
    approach: str = "detailed"
    direct_coc: Optional[float] = None
    beta_approach: str = "single_business_us"
    direct_beta: Optional[float] = None
    erp_approach: str = "operating_countries"
    direct_erp: Optional[float] = None
    operating_countries: list[OperatingCountry] = Field(default_factory=list)
    debt_approach: str = "actual_rating"
    actual_rating: Optional[str] = None
    firm_type: int = 1
    debt_maturity: float = 3
    preferred_shares: Optional[int] = None
    preferred_price: Optional[float] = None
    preferred_dividend: Optional[float] = None


class CostOfCapitalResponse(CostOfCapitalCreate):
    id: UUID

    class Config:
        from_attributes = True


# ============ Valuation Model ============

class ValuationModelCreate(BaseModel):
    name: str
    company_name: Optional[str] = None
    valuation_date: Optional[date] = None
    currency: str = "USD"
    base_year_data: BaseYearData = Field(default_factory=BaseYearData)
    value_drivers: ValueDrivers = Field(default_factory=ValueDrivers)
    market_inputs: MarketInputs = Field(default_factory=MarketInputs)
    rd_settings: RDSettings = Field(default_factory=RDSettings)
    lease_settings: LeaseSettings = Field(default_factory=LeaseSettings)
    option_settings: OptionSettings = Field(default_factory=OptionSettings)
    overrides: Overrides = Field(default_factory=Overrides)
    segments: list[BusinessSegmentCreate] = Field(default_factory=list)
    cost_of_capital: Optional[CostOfCapitalCreate] = None


class ValuationModelUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    valuation_date: Optional[date] = None
    currency: Optional[str] = None
    base_year_data: Optional[BaseYearData] = None
    value_drivers: Optional[ValueDrivers] = None
    market_inputs: Optional[MarketInputs] = None
    rd_settings: Optional[RDSettings] = None
    lease_settings: Optional[LeaseSettings] = None
    option_settings: Optional[OptionSettings] = None
    overrides: Optional[Overrides] = None


class ValuationModelResponse(BaseModel):
    id: UUID
    name: str
    company_name: Optional[str]
    valuation_date: Optional[date]
    currency: str
    base_year_data: dict
    value_drivers: dict
    market_inputs: dict
    rd_settings: dict
    lease_settings: dict
    option_settings: dict
    overrides: dict
    segments: list[BusinessSegmentResponse]
    cost_of_capital: Optional[CostOfCapitalResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ValuationModelListResponse(BaseModel):
    id: UUID
    name: str
    company_name: Optional[str]
    valuation_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Calculation Results ============

class YearProjection(BaseModel):
    year: int
    revenue_growth: float
    revenues: float
    operating_margin: float
    ebit: float
    ebit_1_t: float
    reinvestment: float
    fcff: float
    cost_of_capital: float
    discount_factor: float
    pv_fcff: float


class SegmentProjections(BaseModel):
    segment_name: str
    segment_type: str
    projections: list[YearProjection]
    terminal_value: float
    pv_terminal: float
    segment_value: float


class CostOfCapitalResult(BaseModel):
    approach: str
    risk_free_rate: float
    unlevered_beta: float
    levered_beta: float
    equity_risk_premium: float
    cost_of_equity: float
    pretax_cost_of_debt: float
    after_tax_cost_of_debt: float
    equity_weight: float
    debt_weight: float
    wacc: float
    stable_wacc: float


class ValuationResult(BaseModel):
    segment_projections: list[SegmentProjections]
    cost_of_capital: CostOfCapitalResult

    # Value bridge
    pv_fcff_total: float
    pv_terminal_total: float
    going_concern_value: float
    failure_adjustment: float
    operating_assets_value: float
    debt: float
    minority_interests: float
    cash: float
    non_operating_assets: float
    equity_value: float
    option_value: float
    equity_in_common: float
    shares_outstanding: float
    value_per_share: float
    current_price: float
    price_to_value: float

    # R&D adjustments
    rd_asset_value: Optional[float] = None
    rd_amortization: Optional[float] = None
    rd_operating_adjustment: Optional[float] = None

    # Diagnostics
    diagnostics: Optional[dict] = None
