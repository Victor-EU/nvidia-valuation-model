"""
Valuation Model API Routes

CRUD operations for valuation models.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ValuationModel, BusinessSegment, CostOfCapitalSettings
from app.models.schemas import (
    ValuationModelCreate,
    ValuationModelUpdate,
    ValuationModelResponse,
    ValuationModelListResponse,
    BusinessSegmentCreate,
    BusinessSegmentResponse,
    CostOfCapitalCreate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ValuationModelResponse)
async def create_model(
    model_data: ValuationModelCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new valuation model."""
    logger.info(f"Creating valuation model: {model_data.name}")

    # Create main model
    model = ValuationModel(
        name=model_data.name,
        company_name=model_data.company_name,
        valuation_date=model_data.valuation_date,
        currency=model_data.currency,
        base_year_data=model_data.base_year_data.model_dump(),
        value_drivers=model_data.value_drivers.model_dump(),
        market_inputs=model_data.market_inputs.model_dump(),
        rd_settings=model_data.rd_settings.model_dump(),
        lease_settings=model_data.lease_settings.model_dump(),
        option_settings=model_data.option_settings.model_dump(),
        overrides=model_data.overrides.model_dump(),
    )
    db.add(model)
    await db.flush()  # Get model.id

    # Create segments
    for seg_data in model_data.segments:
        segment = BusinessSegment(
            model_id=model.id,
            name=seg_data.name,
            segment_type=seg_data.segment_type,
            segment_order=seg_data.segment_order,
            inputs=seg_data.inputs.model_dump(),
        )
        db.add(segment)

    # Create cost of capital settings
    if model_data.cost_of_capital:
        coc = CostOfCapitalSettings(
            model_id=model.id,
            approach=model_data.cost_of_capital.approach,
            direct_coc=model_data.cost_of_capital.direct_coc,
            beta_approach=model_data.cost_of_capital.beta_approach,
            direct_beta=model_data.cost_of_capital.direct_beta,
            erp_approach=model_data.cost_of_capital.erp_approach,
            direct_erp=model_data.cost_of_capital.direct_erp,
            operating_countries=[c.model_dump() for c in model_data.cost_of_capital.operating_countries],
            debt_approach=model_data.cost_of_capital.debt_approach,
            actual_rating=model_data.cost_of_capital.actual_rating,
            firm_type=model_data.cost_of_capital.firm_type,
            debt_maturity=model_data.cost_of_capital.debt_maturity,
            preferred_shares=model_data.cost_of_capital.preferred_shares,
            preferred_price=model_data.cost_of_capital.preferred_price,
            preferred_dividend=model_data.cost_of_capital.preferred_dividend,
        )
        db.add(coc)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(ValuationModel)
        .options(selectinload(ValuationModel.segments), selectinload(ValuationModel.cost_of_capital))
        .where(ValuationModel.id == model.id)
    )
    model = result.scalar_one()

    logger.info(f"Created valuation model: {model.id}")
    return model


@router.get("", response_model=list[ValuationModelListResponse])
async def list_models(db: AsyncSession = Depends(get_db)):
    """List all valuation models."""
    result = await db.execute(
        select(ValuationModel).order_by(ValuationModel.updated_at.desc())
    )
    models = result.scalars().all()
    return models


@router.get("/{model_id}", response_model=ValuationModelResponse)
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific valuation model with all data."""
    result = await db.execute(
        select(ValuationModel)
        .options(selectinload(ValuationModel.segments), selectinload(ValuationModel.cost_of_capital))
        .where(ValuationModel.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return model


@router.put("/{model_id}", response_model=ValuationModelResponse)
async def update_model(
    model_id: str,
    model_data: ValuationModelUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a valuation model."""
    result = await db.execute(
        select(ValuationModel)
        .options(selectinload(ValuationModel.segments), selectinload(ValuationModel.cost_of_capital))
        .where(ValuationModel.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Update fields if provided
    update_data = model_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            if hasattr(value, "model_dump"):
                value = value.model_dump()
            setattr(model, field, value)

    await db.commit()
    await db.refresh(model)

    logger.info(f"Updated valuation model: {model_id}")
    return model


@router.delete("/{model_id}")
async def delete_model(model_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a valuation model."""
    result = await db.execute(select(ValuationModel).where(ValuationModel.id == model_id))
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    await db.delete(model)
    await db.commit()

    logger.info(f"Deleted valuation model: {model_id}")
    return {"status": "deleted", "id": str(model_id)}


# Segment endpoints

@router.post("/{model_id}/segments", response_model=BusinessSegmentResponse)
async def add_segment(
    model_id: str,
    segment_data: BusinessSegmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a business segment to a model."""
    result = await db.execute(select(ValuationModel).where(ValuationModel.id == model_id))
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    segment = BusinessSegment(
        model_id=model_id,
        name=segment_data.name,
        segment_type=segment_data.segment_type,
        segment_order=segment_data.segment_order,
        inputs=segment_data.inputs.model_dump(),
    )
    db.add(segment)
    await db.commit()
    await db.refresh(segment)

    return segment


@router.delete("/{model_id}/segments/{segment_id}")
async def delete_segment(
    model_id: str,
    segment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a business segment."""
    result = await db.execute(
        select(BusinessSegment).where(
            BusinessSegment.id == segment_id,
            BusinessSegment.model_id == model_id
        )
    )
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    await db.delete(segment)
    await db.commit()

    return {"status": "deleted", "id": str(segment_id)}


# Cost of capital endpoints

@router.put("/{model_id}/cost-of-capital")
async def update_cost_of_capital(
    model_id: str,
    coc_data: CostOfCapitalCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update cost of capital settings for a model."""
    result = await db.execute(
        select(CostOfCapitalSettings).where(CostOfCapitalSettings.model_id == model_id)
    )
    coc = result.scalar_one_or_none()

    if coc:
        # Update existing
        for field, value in coc_data.model_dump().items():
            if field == "operating_countries":
                value = [c.model_dump() if hasattr(c, "model_dump") else c for c in value]
            setattr(coc, field, value)
    else:
        # Create new
        coc = CostOfCapitalSettings(
            model_id=model_id,
            **{
                k: ([c.model_dump() for c in v] if k == "operating_countries" else v)
                for k, v in coc_data.model_dump().items()
            }
        )
        db.add(coc)

    await db.commit()
    await db.refresh(coc)

    return {"status": "updated", "id": str(coc.id)}
