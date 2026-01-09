from sqlalchemy import Column, Integer, String, Numeric

from app.database import Base


class SyntheticRating(Base):
    """Interest coverage ratio to credit rating mapping."""

    __tablename__ = "synthetic_ratings"

    id = Column(Integer, primary_key=True, index=True)
    firm_type = Column(String(50), nullable=False)  # 'large', 'small', 'financial'
    icr_min = Column(Numeric(12, 6))
    icr_max = Column(Numeric(12, 6))
    rating = Column(String(10), nullable=False)
    spread = Column(Numeric(12, 8), nullable=False)

    def __repr__(self):
        return f"<SyntheticRating {self.firm_type}: {self.rating}>"


class RatingSpread(Base):
    """Credit rating to default spread mapping."""

    __tablename__ = "rating_spreads"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(String(10), nullable=False, unique=True)
    spread = Column(Numeric(12, 8), nullable=False)

    def __repr__(self):
        return f"<RatingSpread {self.rating}: {self.spread}>"
