from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from db.models import Tour, User, Address, Language
from db.schemas import TourCreate, TourOut
from db.get_db import get_async_session
from typing import Optional, List
from datetime import date
from core.security import guide_required, validate_guide_resume

router = APIRouter(prefix="/tours", tags=["tours"])


@router.post("/")
async def create_tour(
    tour: TourCreate,
    session: AsyncSession = Depends(get_async_session),
    guide: User = Depends(validate_guide_resume),
):
    # Fetch addresses from DB
    addresses = await session.execute(
        select(Address).where(Address.address_id.in_(tour.destination_ids))
    )
    address_list = addresses.scalars().all()

    # Fetch languages from DB
    languages = await session.execute(
        select(Language).where(Language.language_id.in_(tour.language_ids))
    )
    language_list = languages.scalars().all()

    if len(address_list) != len(tour.destination_ids):
        raise HTTPException(status_code=400, detail="One or more address IDs are invalid.")

    if len(language_list) != len(tour.language_ids):
        raise HTTPException(status_code=400, detail="One or more language IDs are invalid.")

    new_tour = Tour(
        guide_id=guide.user_id,
        guest_count=tour.guest_count,
        price=tour.price,
        price_type=tour.price_type,
        payment_type=tour.payment_type,
        date=tour.date,
        departure_time=tour.departure_time,
        return_time=tour.return_time,
        duration=tour.duration,
        dress_code=tour.dress_code,
        not_included=tour.not_included,
        included=tour.included,
        photo_gallery=tour.photo_gallery,
        about=tour.about,
        addresses=address_list,
        languages=language_list,
    )

    session.add(new_tour)
    await session.commit()
    await session.refresh(new_tour)

    return {
        "msg": "success"
    }


@router.get("/{tour_id}", response_model=TourOut)
async def get_tour(
        tour_id: int,
        session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Tour)
        .options(selectinload(Tour.addresses), selectinload(Tour.languages))
        .where(Tour.tour_id == tour_id)
    )
    tour = result.scalar_one_or_none()

    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found.")

    return TourOut.from_orm(tour)


@router.get("/", response_model=List[TourOut])
async def list_tours(
    session: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    guide_id: Optional[int] = None,
):
    query = select(Tour).options(
        selectinload(Tour.addresses),
        selectinload(Tour.languages)
    )

    filters = []
    if min_price is not None:
        filters.append(Tour.price >= min_price)
    if max_price is not None:
        filters.append(Tour.price <= max_price)
    if date_from is not None:
        filters.append(Tour.date >= date_from)
    if date_to is not None:
        filters.append(Tour.date <= date_to)
    if guide_id is not None:
        filters.append(Tour.guide_id == guide_id)

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    tours = result.scalars().all()
    return [TourOut.from_orm(tour) for tour in tours]


@router.get("/guide/{guide_id}", response_model=List[TourOut])
async def list_tours_by_guide(
    guide_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Tour)
        .options(selectinload(Tour.addresses), selectinload(Tour.languages))
        .where(Tour.guide_id == guide_id)
    )
    tours = result.scalars().all()

    if not tours:
        raise HTTPException(status_code=404, detail="No tours found for this guide.")

    return [TourOut.from_orm(tour) for tour in tours]
