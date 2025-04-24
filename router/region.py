from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Region
from db.schemas import RegionCreate, RegionOut
from db.get_db import get_async_session

router = APIRouter(prefix="/regions", tags=["regions"])

# Create Region
@router.post("/", response_model=RegionOut)
async def create_region(
        region: RegionCreate,
        session: AsyncSession = Depends(get_async_session)
):
    # Validation for Existing Region
    result = await session.execute(
        select(Region).where(Region.region == region.region)
    )
    existing_region = result.scalar_one_or_none()

    if existing_region:
        raise HTTPException(status_code=400, detail="Region already exists.")

    # Creating New Region
    new_region = Region(region=region.region)
    session.add(new_region)
    await session.commit()
    await session.refresh(new_region)
    return new_region

# Region by ID
@router.get("/{region_id}", response_model=RegionOut)
async def get_region(
        region_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Region).where(Region.region_id == region_id)
    )
    region = result.scalar_one_or_none()
    # Region not found Validation
    if not region:
        raise HTTPException(status_code=404, detail="Region not found.")
    return region


# Regions List
@router.get("/", response_model=list[RegionOut])
async def list_regions(
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Region))
    regions = result.scalars().all()
    return regions


@router.put("/{region_id}", response_model=RegionOut)
async def update_region(
        region_id: int,
        region_data: RegionCreate,
        session: AsyncSession = Depends(get_async_session)
):
    # Region look up by id
    result = await session.execute(
        select(Region).where(Region.region_id == region_id)
    )
    region = result.scalar_one_or_none()

    # Region Not Found Validation
    if not region:
        raise HTTPException(status_code=404, detail="Region not found.")

    # Region name conflict validation
    if region_data.region != region.region:
        result = await session.execute(
            select(Region).where(Region.region == region_data.region)
        )
        existing_region = result.scalar_one_or_none()
        if existing_region:
            raise HTTPException(status_code=400, detail="Region name already exists.")

    # Region update
    region.region = region_data.region
    await session.commit()
    await session.refresh(region)
    return region


@router.delete("/{region_id}")
async def delete_region(
        region_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    # Look for a Region by region_id
    result = await session.execute(
        select(Region).where(Region.region_id == region_id)
    )
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="Region not found.")

    # Region Deletion
    await session.delete(region)
    await session.commit()
    return {"message": "Region deleted successfully"}