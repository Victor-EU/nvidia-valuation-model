"""
R&D Capitalization Converter

Capitalizes R&D expenses as an asset and amortizes over specified years.
Replicates the 'R&D converter' sheet from Excel.
"""

from dataclasses import dataclass


@dataclass
class RDInputs:
    """Inputs for R&D capitalization."""
    amortization_years: int = 5
    current_rd_expense: float = 0
    historical_rd: list[float] = None  # [year-1, year-2, ..., year-n]

    def __post_init__(self):
        if self.historical_rd is None:
            self.historical_rd = []


@dataclass
class RDResult:
    """R&D capitalization result."""
    research_asset_value: float
    current_amortization: float
    operating_income_adjustment: float
    tax_effect: float  # At marginal tax rate
    unamortized_by_year: list[dict]


def calculate_rd_capitalization(inputs: RDInputs, marginal_tax_rate: float = 0.25) -> RDResult:
    """
    Capitalize R&D expenses and calculate adjustments to operating income.

    The logic:
    1. Current year R&D is 100% unamortized (added to asset)
    2. Historical R&D is partially unamortized based on age
    3. Annual amortization reduces the asset
    4. Operating income adjustment = Current R&D - Amortization
    """
    if inputs.amortization_years <= 0:
        return RDResult(
            research_asset_value=0,
            current_amortization=0,
            operating_income_adjustment=0,
            tax_effect=0,
            unamortized_by_year=[]
        )

    unamortized_details = []
    total_asset_value = 0
    total_amortization = 0

    # Current year: 100% unamortized
    unamortized_details.append({
        "year": 0,
        "rd_expense": inputs.current_rd_expense,
        "unamortized_pct": 1.0,
        "unamortized_value": inputs.current_rd_expense,
        "amortization": 0  # No amortization in current year
    })
    total_asset_value += inputs.current_rd_expense

    # Historical years
    for i, rd_expense in enumerate(inputs.historical_rd):
        year_offset = i + 1  # -1, -2, -3, ...

        if year_offset >= inputs.amortization_years:
            # Fully amortized
            unamortized_pct = 0
        else:
            # Linear amortization: remaining years / total years
            unamortized_pct = (inputs.amortization_years - year_offset) / inputs.amortization_years

        unamortized_value = rd_expense * unamortized_pct
        annual_amortization = rd_expense / inputs.amortization_years if year_offset < inputs.amortization_years else 0

        unamortized_details.append({
            "year": -year_offset,
            "rd_expense": rd_expense,
            "unamortized_pct": unamortized_pct,
            "unamortized_value": unamortized_value,
            "amortization": annual_amortization
        })

        total_asset_value += unamortized_value
        total_amortization += annual_amortization

    # Operating income adjustment
    # Add back R&D expense, subtract amortization
    operating_adjustment = inputs.current_rd_expense - total_amortization

    # Tax effect (positive adjustment means higher taxes)
    tax_effect = operating_adjustment * marginal_tax_rate

    return RDResult(
        research_asset_value=total_asset_value,
        current_amortization=total_amortization,
        operating_income_adjustment=operating_adjustment,
        tax_effect=tax_effect,
        unamortized_by_year=unamortized_details
    )
