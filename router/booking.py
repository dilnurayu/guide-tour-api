from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import BookGuide, BookTour, User, Tour
from db.schemas import BookGuideCreate, BookGuideOut, BookTourCreate, BookTourOut
from db.get_db import get_async_session
from core.security import tourist_required, validate_guide_resume
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/guides", response_model=BookGuideOut)
async def book_guide(
    data: BookGuideCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(tourist_required),
):
    new_booking = BookGuide(
        tourist_id=current_user.user_id,
        guide_id=data.guide_id,
        tour_date=data.tour_date,
        reserve_count=data.reserve_count,
        language_id=data.language_id,
        message=data.message,
    )
    session.add(new_booking)
    await session.commit()
    await session.refresh(new_booking)
    return new_booking


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
        language_id=data.language_id,
        message=data.message,
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


@router.put("/guides/{booking_id}/confirm")
async def confirm_guide_booking(
        booking_id: int,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(validate_guide_resume)
):
    result = await session.execute(
        select(BookGuide).where(BookGuide.book_id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    if booking.guide_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to confirm this booking.")

    booking.confirmed = True

    await session.commit()
    await session.refresh(booking)
    return {"msg": "Booking Confirmed"}




@router.put("/tour/{booking_id}/confirm")
async def confirm_tour_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(validate_guide_resume)
):
    result = await session.execute(
        select(BookTour)
        .options(joinedload(BookTour.tour))
        .where(BookTour.book_id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    if booking.tour is None or booking.tour.guide_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to confirm this tour.")

    booking.confirmed = True
    await session.commit()
    await session.refresh(booking)
    return {"msg": "Booking Confirmed"}



@router.get("/guides/guide/me", response_model=List[BookGuideOut])
async def list_my_guide_bookings(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(validate_guide_resume)
):
    result = await session.execute(
        select(BookGuide)
        .where(BookGuide.guide_id == current_user.user_id)
    )
    bookings = result.scalars().all()
    if not bookings:
        raise HTTPException(status_code=404, detail="No guide bookings found for this guide.")
    return bookings

@router.get("/tours/guide/me", response_model=List[BookTourOut])
async def list_my_tour_bookings(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(validate_guide_resume)
):
    stmt = (
        select(BookTour)
        .join(Tour, BookTour.tour_id == Tour.tour_id)
        .where(Tour.guide_id == current_user.user_id)
        .options(joinedload(BookTour.tour))
    )
    result = await session.execute(stmt)
    bookings = result.scalars().all()
    if not bookings:
        raise HTTPException(status_code=404, detail="No tour bookings found for your tours.")
    return bookings

@router.get("/guides/tourist/me", response_model=List[BookGuideOut])
async def list_my_guide_bookings_tourist(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(tourist_required)
):
    result = await session.execute(
        select(BookGuide)
        .where(BookGuide.tourist_id == current_user.user_id)
    )
    bookings = result.scalars().all()
    if not bookings:
        raise HTTPException(status_code=404, detail="No guide bookings found for this tourist.")
    return bookings

@router.get("/tours/tourist/me", response_model=List[BookTourOut])
async def list_my_tour_bookings_tourist(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(tourist_required)
):
    result = await session.execute(
        select(BookTour)
        .where(BookTour.tourist_id == current_user.user_id)
    )
    bookings = result.scalars().all()
    if not bookings:
        raise HTTPException(status_code=404, detail="No tour bookings found for this tourist.")
    return bookings