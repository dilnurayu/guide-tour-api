from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import BookGuide, BookTour, User
from db.schemas import BookGuideCreate, BookGuideOut, BookTourCreate, BookTourOut
from db.get_db import get_async_session
from core.security import tourist_required

router = APIRouter(prefix="/bookings", tags=["bookings"])

#Booking a Guide
@router.post("/guides", response_model=BookGuideOut)
async def book_guide(
    data: BookGuideCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(tourist_required),
):
    new_booking = BookGuide(
        tourist_id=current_user.user_id,
        guide_id=data.guide_id,
        reserve_count=data.reserve_count,
    )
    session.add(new_booking)
    await session.commit()
    await session.refresh(new_booking)
    return new_booking

#Booking a Tour
@router.post("/tours", response_model=BookTourOut)
async def book_tour(
        data: BookTourCreate,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(tourist_required),
):
    new_booking = BookTour(
        tourist_id=current_user.user_id,
        tour_id=data.tour_id,
        reserve_count=data.reserve_count,

    )
    session.add(new_booking)
    await session.commit()
    await session.refresh(new_booking)
    return new_booking


@router.get("/guides/{booking_id}", response_model=BookGuideOut)
async def get_guide_booking(
        booking_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(BookGuide).where(BookGuide.book_id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    return booking


@router.get("/tours/{booking_id}", response_model=BookTourOut)
async def get_tour_booking(
        booking_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(BookTour).where(BookTour.book_id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    return booking