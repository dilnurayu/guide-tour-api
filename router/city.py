from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import City
from db.schemas import CityCreate, CityOut
from db.get_db import get_async_session

router = APIRouter(prefix="/cities", tags=["cities"])


@router.post("/", response_model=CityOut)
async def create_city(
        city: CityCreate,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(City).where(City.city == city.city)
    )
    existing_city = result.scalar_one_or_none()

    if existing_city:
        raise HTTPException(status_code=400, detail="City already exists.")

    new_city = City(region_id=city.region_id, city=city.city)
    session.add(new_city)
    await session.commit()
    await session.refresh(new_city)
    return new_city


@router.get("/{city_id}", response_model=CityOut)
async def get_city(
        city_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(City).where(City.city_id == city_id)
    )
    city = result.scalar_one_or_none()

    if not city:
        raise HTTPException(status_code=404, detail="City not found.")
    return city


@router.get("/", response_model=list[CityOut])
async def list_cities(
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(City))
    cities = result.scalars().all()
    return cities