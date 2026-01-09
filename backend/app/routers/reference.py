"""
Reference Data API Routes

Endpoints for countries, industries, and rating spreads.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Country, Industry
from app.models.schemas import CountryResponse, IndustryResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/countries", response_model=list[CountryResponse])
async def list_countries(
    search: Optional[str] = Query(None, description="Search by country name"),
    db: AsyncSession = Depends(get_db)
):
    """List all countries with equity risk premiums."""
    query = select(Country).order_by(Country.name)

    if search:
        query = query.where(Country.name.ilike(f"%{search}%"))

    result = await db.execute(query)
    countries = result.scalars().all()
    return countries


@router.get("/countries/{country_id}", response_model=CountryResponse)
async def get_country(country_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific country by ID."""
    result = await db.execute(select(Country).where(Country.id == country_id))
    country = result.scalar_one_or_none()

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    return country


@router.get("/countries/by-name/{name}", response_model=CountryResponse)
async def get_country_by_name(name: str, db: AsyncSession = Depends(get_db)):
    """Get a country by name."""
    result = await db.execute(select(Country).where(Country.name == name))
    country = result.scalar_one_or_none()

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    return country


@router.get("/industries", response_model=list[IndustryResponse])
async def list_industries(
    region: Optional[str] = Query(None, description="Filter by region (US or Global)"),
    search: Optional[str] = Query(None, description="Search by industry name"),
    db: AsyncSession = Depends(get_db)
):
    """List all industries with averages."""
    query = select(Industry).order_by(Industry.name)

    if region:
        query = query.where(Industry.region == region)

    if search:
        query = query.where(Industry.name.ilike(f"%{search}%"))

    result = await db.execute(query)
    industries = result.scalars().all()
    return industries


@router.get("/industries/{industry_id}", response_model=IndustryResponse)
async def get_industry(industry_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific industry by ID."""
    result = await db.execute(select(Industry).where(Industry.id == industry_id))
    industry = result.scalar_one_or_none()

    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")

    return industry


@router.get("/industries/by-name/{name}", response_model=IndustryResponse)
async def get_industry_by_name(
    name: str,
    region: str = Query("US", description="Region (US or Global)"),
    db: AsyncSession = Depends(get_db)
):
    """Get an industry by name and region."""
    result = await db.execute(
        select(Industry).where(Industry.name == name, Industry.region == region)
    )
    industry = result.scalar_one_or_none()

    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")

    return industry


@router.get("/ratings")
async def list_rating_spreads():
    """List all rating spreads."""
    from app.services.synthetic_rating import RATING_SPREADS
    return [
        {"rating": rating, "spread": spread}
        for rating, spread in RATING_SPREADS.items()
    ]
