from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from db.models import Tour, User
from db.schemas import TourCreate, TourOut
from db.get_db import get_async_session
from typing import Optional
from datetime import date
from core.security import guide_required, validate_guide_resume

router = APIRouter(prefix="/tours", tags=["tours"])


@router.post("/", response_model=TourOut)
async def create_tour(
    tour: TourCreate,
    session: AsyncSession = Depends(get_async_session),
    guide: User = Depends(validate_guide_resume),
):
    new_tour = Tour(
        guide_id=guide.user_id,
        address_id=tour.address_id,
        language=tour.language,
        guest_count=tour.guest_count,
        price=tour.price,
        price_type=tour.price_type,
        payment_type=tour.payment_type,
        date=tour.date,
        duration=tour.duration,
        about=tour.about,
    )

    session.add(new_tour)
    await session.commit()
    await session.refresh(new_tour)

    return new_tour


@router.get("/{tour_id}", response_model=TourOut)
async def get_tour(
    tour_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Tour).where(Tour.tour_id == tour_id)
    )
    tour = result.scalar_one_or_none()

    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found.")
    return tour


@router.get("/", response_model=list[TourOut])
async def list_tours(
    session: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    language: Optional[str] = None,
    guide_id: Optional[int] = None,
):
    query = select(Tour)

    filters = []
    if min_price is not None:
        filters.append(Tour.price >= min_price)
    if max_price is not None:
        filters.append(Tour.price <= max_price)
    if date_from is not None:
        filters.append(Tour.date >= date_from)
    if date_to is not None:
        filters.append(Tour.date <= date_to)
    if language is not None:
        filters.append(Tour.language == language)
    if guide_id is not None:
        filters.append(Tour.guide_id == guide_id)

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    tours = result.scalars().all()
    return tours


@router.get("/guide/{guide_id}", response_model=list[TourOut])
async def list_tours_by_guide(
    guide_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Tour).where(Tour.guide_id == guide_id)
    )
    tours = result.scalars().all()

    if not tours:
        raise HTTPException(status_code=404, detail="No tours found for this guide.")

    return tours
