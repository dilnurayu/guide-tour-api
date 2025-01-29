from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Region
from db.schemas import RegionCreate, RegionOut
from db.get_db import get_async_session

router = APIRouter(prefix="/regions", tags=["regions"])


@router.post("/", response_model=RegionOut)
async def create_region(
        region: RegionCreate,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Region).where(Region.region == region.region)
    )
    existing_region = result.scalar_one_or_none()

    if existing_region:
        raise HTTPException(status_code=400, detail="Region already exists.")

    new_region = Region(region=region.region)
    session.add(new_region)
    await session.commit()
    await session.refresh(new_region)
    return new_region


@router.get("/{region_id}", response_model=RegionOut)
async def get_region(
        region_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Region).where(Region.region_id == region_id)
    )
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="Region not found.")
    return region


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
    result = await session.execute(
        select(Region).where(Region.region_id == region_id)
    )
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="Region not found.")

    if region_data.region != region.region:
        result = await session.execute(
            select(Region).where(Region.region == region_data.region)
        )
        existing_region = result.scalar_one_or_none()
        if existing_region:
            raise HTTPException(status_code=400, detail="Region name already exists.")

    region.region = region_data.region
    await session.commit()
    await session.refresh(region)
    return region


@router.delete("/{region_id}")
async def delete_region(
        region_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Region).where(Region.region_id == region_id)
    )
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="Region not found.")

    await session.delete(region)
    await session.commit()
    return {"message": "Region deleted successfully"}