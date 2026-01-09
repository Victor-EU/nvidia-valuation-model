"""
Synthetic Credit Rating Estimation

Estimates credit rating from Interest Coverage Ratio (ICR).
Replicates the 'Synthetic rating' sheet from Excel.
"""

from dataclasses import dataclass
from typing import Optional


# Rating tables based on Damodaran's data
# Format: (icr_min, icr_max, rating, spread)

LARGE_MANUFACTURING_RATINGS = [
    (-100000, 0.199999, "D2/D", 0.20),
    (0.2, 0.649999, "C2/C", 0.175),
    (0.65, 0.799999, "Ca2/CC", 0.1578),
    (0.8, 1.249999, "Caa/CCC", 0.1157),
    (1.25, 1.499999, "B3/B-", 0.0737),
    (1.5, 1.749999, "B2/B", 0.0526),
    (1.75, 1.999999, "B1/B+", 0.0455),
    (2.0, 2.249999, "Ba2/BB", 0.0313),
    (2.25, 2.499999, "Ba1/BB+", 0.0242),
    (2.5, 2.999999, "Baa2/BBB", 0.02),
    (3.0, 4.249999, "A3/A-", 0.0162),
    (4.25, 5.499999, "A2/A", 0.0142),
    (5.5, 6.499999, "A1/A+", 0.0123),
    (6.5, 8.499999, "Aa2/AA", 0.0085),
    (8.5, 100000, "Aaa/AAA", 0.0069),
]

SMALL_RISKY_RATINGS = [
    (-100000, 0.499999, "D2/D", 0.20),
    (0.5, 0.799999, "C2/C", 0.175),
    (0.8, 1.249999, "Ca2/CC", 0.1578),
    (1.25, 1.499999, "Caa/CCC", 0.1157),
    (1.5, 1.999999, "B3/B-", 0.0737),
    (2.0, 2.499999, "B2/B", 0.0526),
    (2.5, 2.999999, "B1/B+", 0.0455),
    (3.0, 3.499999, "Ba2/BB", 0.0313),
    (3.5, 3.999999, "Ba1/BB+", 0.0242),
    (4.0, 4.499999, "Baa2/BBB", 0.02),
    (4.5, 5.999999, "A3/A-", 0.0162),
    (6.0, 7.499999, "A2/A", 0.0142),
    (7.5, 9.499999, "A1/A+", 0.0123),
    (9.5, 12.499999, "Aa2/AA", 0.0085),
    (12.5, 100000, "Aaa/AAA", 0.0069),
]

# Rating to spread lookup for actual ratings
RATING_SPREADS = {
    "Aaa/AAA": 0.0069,
    "Aa1/AA+": 0.0078,
    "Aa2/AA": 0.0085,
    "Aa3/AA-": 0.0094,
    "A1/A+": 0.0123,
    "A2/A": 0.0142,
    "A3/A-": 0.0162,
    "Baa1/BBB+": 0.0181,
    "Baa2/BBB": 0.02,
    "Baa3/BBB-": 0.0225,
    "Ba1/BB+": 0.0242,
    "Ba2/BB": 0.0313,
    "Ba3/BB-": 0.0375,
    "B1/B+": 0.0455,
    "B2/B": 0.0526,
    "B3/B-": 0.0737,
    "Caa/CCC": 0.1157,
    "Ca2/CC": 0.1578,
    "C2/C": 0.175,
    "D2/D": 0.20,
}


@dataclass
class SyntheticRatingInputs:
    """Inputs for synthetic rating estimation."""
    ebit: float
    interest_expense: float
    firm_type: int = 1  # 1 = large manufacturing, 2 = small/risky


@dataclass
class SyntheticRatingResult:
    """Synthetic rating estimation result."""
    interest_coverage_ratio: float
    estimated_rating: str
    estimated_spread: float
    rating_table_used: str


def get_synthetic_rating(inputs: SyntheticRatingInputs) -> SyntheticRatingResult:
    """
    Estimate credit rating from interest coverage ratio.

    The interest coverage ratio (ICR) = EBIT / Interest Expense
    Different thresholds apply for large vs small/risky firms.
    """
    # Calculate ICR
    if inputs.interest_expense <= 0:
        icr = 1000000  # Very high coverage if no interest
    elif inputs.ebit < 0:
        icr = -100000  # Negative coverage
    else:
        icr = inputs.ebit / inputs.interest_expense

    # Select rating table
    if inputs.firm_type == 2:
        rating_table = SMALL_RISKY_RATINGS
        table_name = "small_risky"
    else:
        rating_table = LARGE_MANUFACTURING_RATINGS
        table_name = "large_manufacturing"

    # Find matching rating
    rating = "D2/D"
    spread = 0.20

    for icr_min, icr_max, r, s in rating_table:
        if icr_min <= icr <= icr_max:
            rating = r
            spread = s
            break

    return SyntheticRatingResult(
        interest_coverage_ratio=icr,
        estimated_rating=rating,
        estimated_spread=spread,
        rating_table_used=table_name
    )


def get_spread_for_rating(rating: str) -> Optional[float]:
    """Get default spread for a given credit rating."""
    # Try exact match first
    if rating in RATING_SPREADS:
        return RATING_SPREADS[rating]

    # Try partial match (e.g., "A2/A" matches "A2/A")
    rating_upper = rating.upper()
    for key, spread in RATING_SPREADS.items():
        if rating_upper in key.upper() or key.upper() in rating_upper:
            return spread

    return None
