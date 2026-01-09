import uuid
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Integer, Numeric, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class ValuationModel(Base):
    """Main valuation model containing all inputs and settings."""

    __tablename__ = "valuation_models"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    company_name = Column(String(100))
    valuation_date = Column(Date)
    currency = Column(String(3), default="USD")

    # Company fundamentals
    # {revenues, operating_income, interest_expense, book_equity, book_debt,
    #  cash, cross_holdings, minority_interests, shares, stock_price,
    #  effective_tax_rate, marginal_tax_rate, last_year_revenues, last_year_ebit}
    base_year_data = Column(JSON, default=dict)

    # Value drivers
    # {revenue_growth_yr1, operating_margin_yr1, compounded_growth_2_5,
    #  target_margin, convergence_year, sales_to_capital_1_5, sales_to_capital_6_10}
    value_drivers = Column(JSON, default=dict)

    # Market inputs
    # {risk_free_rate, country, industry_us, industry_global}
    market_inputs = Column(JSON, default=dict)

    # R&D settings
    # {capitalize_rd, amortization_years, current_rd, rd_expenses: [y-1, y-2, ...]}
    rd_settings = Column(JSON, default=dict)

    # Operating lease settings
    # {has_leases, lease_expense, commitments: [y1, y2, y3, y4, y5, beyond]}
    lease_settings = Column(JSON, default=dict)

    # Employee options
    # {has_options, num_options, avg_strike, avg_maturity, std_dev}
    option_settings = Column(JSON, default=dict)

    # Override assumptions
    # {override_stable_coc, stable_coc, override_stable_roic, stable_roic,
    #  override_failure, failure_prob, distress_proceeds_type, distress_proceeds_pct,
    #  override_reinvestment_lag, reinvestment_lag, override_tax_rate, override_nol, nol,
    #  override_risk_free, future_risk_free, override_growth}
    overrides = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    segments = relationship("BusinessSegment", back_populates="model", cascade="all, delete-orphan")
    cost_of_capital = relationship("CostOfCapitalSettings", back_populates="model", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ValuationModel {self.name}>"


class BusinessSegment(Base):
    """Business segment with specific inputs for multi-segment valuation."""

    __tablename__ = "business_segments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_id = Column(String(36), ForeignKey("valuation_models.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    segment_type = Column(String(50))  # 'rest', 'ai', 'auto'
    segment_order = Column(Integer, default=0)

    # Segment-specific inputs
    # For AI/Auto: {total_market_current, total_market_year10,
    #              market_share_current, market_share_year10,
    #              operating_margin_current, operating_margin_year10}
    # For Rest: uses global value drivers
    inputs = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    model = relationship("ValuationModel", back_populates="segments")

    def __repr__(self):
        return f"<BusinessSegment {self.name}>"


class CostOfCapitalSettings(Base):
    """Cost of capital calculation settings."""

    __tablename__ = "cost_of_capital_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_id = Column(String(36), ForeignKey("valuation_models.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Approach: 'direct', 'detailed', 'industry', 'histogram'
    approach = Column(String(50), default="detailed")

    # Direct input
    direct_coc = Column(Numeric(12, 8))

    # Beta calculation
    beta_approach = Column(String(50), default="single_business_us")
    direct_beta = Column(Numeric(12, 8))

    # ERP calculation
    erp_approach = Column(String(50), default="operating_countries")
    direct_erp = Column(Numeric(12, 8))
    operating_countries = Column(JSON, default=list)  # [{country, revenues}, ...]

    # Debt inputs
    debt_approach = Column(String(50), default="actual_rating")
    actual_rating = Column(String(10))
    firm_type = Column(Integer, default=1)  # 1=large, 2=small
    debt_maturity = Column(Numeric(8, 4), default=3)

    # Preferred stock
    preferred_shares = Column(Integer)
    preferred_price = Column(Numeric(12, 4))
    preferred_dividend = Column(Numeric(12, 4))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    model = relationship("ValuationModel", back_populates="cost_of_capital")

    def __repr__(self):
        return f"<CostOfCapitalSettings {self.approach}>"
