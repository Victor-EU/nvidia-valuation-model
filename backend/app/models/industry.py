from sqlalchemy import Column, Integer, String, Numeric, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class Industry(Base):
    """Industry averages for valuation benchmarking."""

    __tablename__ = "industries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    region = Column(String(20), default="US", index=True)  # US or Global

    # Basic metrics
    num_firms = Column(Integer)
    revenue_growth_5yr = Column(Numeric(12, 8))
    operating_margin = Column(Numeric(12, 8))
    after_tax_roc = Column(Numeric(12, 8))
    effective_tax_rate = Column(Numeric(12, 8))

    # Beta and risk
    unlevered_beta = Column(Numeric(12, 8))
    levered_beta = Column(Numeric(12, 8))
    cost_of_equity = Column(Numeric(12, 8))
    std_dev_stock = Column(Numeric(12, 8))

    # Debt metrics
    pretax_cost_of_debt = Column(Numeric(12, 8))
    debt_to_capital = Column(Numeric(12, 8))
    cost_of_capital = Column(Numeric(12, 8))

    # Efficiency
    sales_to_capital = Column(Numeric(12, 8))

    # Valuation multiples
    ev_to_sales = Column(Numeric(12, 8))
    ev_to_ebitda = Column(Numeric(12, 8))
    ev_to_ebit = Column(Numeric(12, 8))
    price_to_book = Column(Numeric(12, 8))
    trailing_pe = Column(Numeric(12, 8))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("name", "region", name="uq_industry_name_region"),
    )

    def __repr__(self):
        return f"<Industry {self.name} ({self.region})>"
