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

@router.post("/guides")
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
    return {"msg": "Book created successfully"}


@router.post("/tours")
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
    return {"msg": "Book created successfully"}


# @router.get("/guides/{booking_id}", response_model=BookGuideOut)
# async def get_guide_booking(
#     booking_id: int,
#     session: AsyncSession = Depends(get_async_session)
# ):
#     result = await session.execute(
#         select(BookGuide).where(BookGuide.book_id == booking_id)
#     )
#     booking = result.scalar_one_or_none()
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found.")
#     return booking
#
# @router.get("/tours/{booking_id}", response_model=BookTourOut)
# async def get_tour_booking(
#     booking_id: int,
#     session: AsyncSession = Depends(get_async_session)
# ):
#     result = await session.execute(
#         select(BookTour).where(BookTour.book_id == booking_id)
#     )
#     booking = result.scalar_one_or_none()
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found.")
#     return booking

#HERE WE ARE CONFIRMING THE GUIDE BOOKING
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



#HERE WE ARE CONFIRMING THE TOUR BOOKING
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


# HERE WE ARE LISTING THE GUIDE'S BOOKINGS
@router.get("/guides/guide/me", response_model=List[BookGuideOut])
async def list_my_guide_bookings(
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(validate_guide_resume)
):
    result = await session.execute(
        select(BookGuide, User.name.label("tourist_name"), User.profile_photo.label("tourist_photo"))
        .join(User, BookGuide.tourist_id == User.user_id)
        .where(BookGuide.guide_id == current_user.user_id)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail="No guide bookings found for this guide.")

    bookings = [
        BookGuideOut.from_orm(booking, tourist_name=tourist_name, tourist_photo=tourist_photo)
        for booking, tourist_name, tourist_photo in rows
    ]
    return bookings


# HERE WE ARE LISTING THE GUIDE'S TOUR BOOKINGS
@router.get("/tours/guide/me", response_model=List[BookTourOut])
async def list_my_tour_bookings(
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(validate_guide_resume)
):
    stmt = (
        select(BookTour, User.name.label("tourist_name"), Tour.title.label("tour_title"),
               User.profile_photo.label("tourist_photo"))
        .join(Tour, BookTour.tour_id == Tour.tour_id)
        .join(User, BookTour.tourist_id == User.user_id)
        .where(Tour.guide_id == current_user.user_id)
        .options(joinedload(BookTour.tour))
    )
    result = await session.execute(stmt)
    rows = result.all()
    if not rows:
        raise HTTPException(status_code=404, detail="No tour bookings found for your tours.")
    bookings = [
        BookTourOut.from_orm(booking, tourist_name=tourist_name, tour_title=tour_title, tourist_photo=tourist_photo)
        for booking, tourist_name, tour_title, tourist_photo in rows
    ]
    return bookings

# HERE WE ARE LISTING TOURIST'S GUIDE BOOKING
@router.get("/guides/tourist/me", response_model=List[BookGuideOut])
async def list_my_guide_bookings_tourist(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(tourist_required)
):
    result = await session.execute(
        select(BookGuide, User.name.label("guide_name"), User.profile_photo.label("guide_photo"))
        .join(User, BookGuide.guide_id == User.user_id)
        .where(BookGuide.tourist_id == current_user.user_id)
    )
    rows = result.all()
    if not rows:
        raise HTTPException(status_code=404, detail="No guide bookings found for this tourist.")
    bookings = [
        BookGuideOut.from_orm(booking, guide_name=guide_name, guide_photo=guide_photo)
        for booking, guide_name, guide_photo in rows
    ]
    return bookings

# HERE WE ARE LISTING TOURIST'S TOUR BOOKING
@router.get("/tours/tourist/me", response_model=List[BookTourOut])
async def list_my_tour_bookings_tourist(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(tourist_required)
):
    stmt = (
        select(BookTour, Tour.title.label("tour_title"), User.name.label("guide_name"),
               User.profile_photo.label("guide_photo"))
        .join(Tour, BookTour.tour_id == Tour.tour_id)
        .join(User, Tour.guide_id == User.user_id)
        .where(BookTour.tourist_id == current_user.user_id)
    )
    result = await session.execute(stmt)
    rows = result.all()
    if not rows:
        raise HTTPException(status_code=404, detail="No tour bookings found for this tourist.")
    bookings = [
        BookTourOut.from_orm(booking, tour_title=tour_title, guide_name=guide_name, guide_photo=guide_photo)
        for booking, tour_title, guide_name, guide_photo in rows
    ]
    return bookings