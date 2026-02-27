from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Country(Base):
    """Country with equity risk premium data."""

    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    moodys_rating = Column(String(30))
    adj_default_spread = Column(Numeric(12, 8))
    equity_risk_premium = Column(Numeric(12, 8))
    country_risk_premium = Column(Numeric(12, 8))
    corporate_tax_rate = Column(Numeric(8, 6))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Country {self.name}>"
