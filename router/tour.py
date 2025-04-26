import dropbox
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload
from starlette.concurrency import run_in_threadpool

from db.models import Tour, User, Address, Language, Resume
from db.schemas import TourCreate, TourOut
from db.get_db import get_async_session
from typing import Optional, List
from datetime import date
from core.security import validate_guide_resume
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/tours", tags=["tours"])

DROPBOX_APP_KEY = "c867asn0edqf8mv"
DROPBOX_REFRESH_TOKEN = "9GYSvVIsEVoAAAAAAAAAAaOekDg4O5OAKc0Xiet94FwkDB9DIRJHhdyGKn17tCDn"
DROPBOX_APP_SECRET = "wwzmagewt3iex43"

async def save_upload_file(upload_file: UploadFile) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = os.path.splitext(upload_file.filename)[1]
    filename = f"{timestamp}_{unique_id}{file_extension}"
    dropbox_path = f"/uploads/tours/{filename}"

    file_content = await upload_file.read()

    def upload_to_dropbox() -> str:
        try:
            dbx = dropbox.Dropbox(
                app_key=DROPBOX_APP_KEY,
                app_secret=DROPBOX_APP_SECRET,
                oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
            )
            dbx.files_upload(file_content, dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
            try:
                shared_link_metadata = dbx.sharing_create_shared_link_with_settings(dropbox_path)
                url = shared_link_metadata.url
            except dropbox.exceptions.ApiError as e:
                links = dbx.sharing_list_shared_links(path=dropbox_path, direct_only=True).links
                if links:
                    url = links[0].url
                else:
                    raise e
            direct_url = url.replace("&dl=0", "&raw=1")
            return direct_url

        except Exception as e:
            raise RuntimeError(f"Dropbox upload failed: {e}")

    public_url = await run_in_threadpool(upload_to_dropbox)
    return public_url


@router.post("/")
async def create_tour(
        tour_data: TourCreate,
        photos: List[UploadFile] = File(None),
        session: AsyncSession = Depends(get_async_session),
        guide: User = Depends(validate_guide_resume)
):
    addresses = await session.execute(
        select(Address).where(Address.address_id.in_(tour_data.destination_ids))
    )
    address_list = addresses.scalars().all()

    languages = await session.execute(
        select(Language).where(Language.language_id.in_(tour_data.language_ids))
    )
    language_list = languages.scalars().all()

    if len(address_list) != len(tour_data.destination_ids):
        raise HTTPException(status_code=400, detail="One or more address IDs are invalid.")
    if len(language_list) != len(tour_data.language_ids):
        raise HTTPException(status_code=400, detail="One or more language IDs are invalid.")

    photo_urls = []
    if photos:
        for photo in photos:
            if not photo.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Uploaded file is not an image")

            content = await photo.read(2 * 1024 * 1024 + 1)
            if len(content) > 2 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File size too large")

            await photo.seek(0)

            photo_url = await save_upload_file(photo)
            photo_urls.append(photo_url)

    # Convert to dict and prepare for database
    tour_dict = tour_data.dict(exclude={"destination_ids", "language_ids"})

    if isinstance(tour_dict.get("date"), datetime):
        tour_dict["date"] = tour_dict["date"].date()

    if photo_urls:
        tour_dict['photo_gallery'] = photo_urls

    new_tour = Tour(
        guide_id=guide.user_id,
        **tour_dict,
        addresses=address_list,
        languages=language_list,
    )

    session.add(new_tour)
    await session.commit()
    await session.refresh(new_tour)

    return {"msg": "success"}


@router.get("/me", response_model=List[TourOut])
async def list_my_tours(
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(validate_guide_resume)
):
    result = await session.execute(
        select(Tour)
        .options(
            selectinload(Tour.addresses),
            selectinload(Tour.languages),
            selectinload(Tour.tour_reviews)
        )
        .where(Tour.guide_id == current_user.user_id)
    )
    tours = result.scalars().all()
    if not tours:
        raise HTTPException(status_code=404, detail="No tours found for this guide.")

    # Process each tour to calculate average rating before conversion to schema
    response_tours = []
    for tour in tours:
        # Calculate average rating
        if tour.tour_reviews:
            avg_rating = sum(review.rating for review in tour.tour_reviews) / len(tour.tour_reviews)
        else:
            avg_rating = 0.0

        # Use ORM mode to convert to schema
        tour_out = TourOut.from_orm(tour)
        tour_out.average_rating = avg_rating
        response_tours.append(tour_out)

    return response_tours


@router.get("/{tour_id}", response_model=TourOut)
async def get_tour(
        tour_id: int,
        session: AsyncSession = Depends(get_async_session),
):
    async with session.begin():
        result = await session.execute(
            select(Tour)
            .options(
                selectinload(Tour.addresses),
                selectinload(Tour.languages),
                selectinload(Tour.tour_reviews)
            )
            .where(Tour.tour_id == tour_id)
        )
        tour = result.scalar_one_or_none()

        if not tour:
            raise HTTPException(status_code=404, detail="Tour not found")

        # Calculate average rating
        avg_rating = 0.0
        if tour.tour_reviews:
            avg_rating = sum(review.rating for review in tour.tour_reviews) / len(tour.tour_reviews)

        # Use ORM mode to convert to schema
        tour_out = TourOut.from_orm(tour)
        tour_out.average_rating = avg_rating

        return tour_out


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
        region_ids: Optional[List[int]] = Query(None),
        language_ids: Optional[List[int]] = Query(None),
        min_rating: Optional[float] = None,
        payment_type: Optional[str] = None,
        min_guest_count: Optional[int] = None,
        max_guest_count: Optional[int] = None,
):
    query = select(Tour).options(
        selectinload(Tour.addresses),
        selectinload(Tour.languages),
        selectinload(Tour.tour_reviews)
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

    if region_ids:
        filters.append(Tour.addresses.any(Address.region_id.in_(region_ids)))
    if language_ids:
        filters.append(Tour.languages.any(Language.language_id.in_(language_ids)))
    if min_rating is not None:
        filters.append(Tour.average_rating >= min_rating)
    if payment_type is not None:
        filters.append(Tour.payment_type == payment_type)
    if min_guest_count is not None:
        filters.append(Tour.guest_count >= min_guest_count)
    if max_guest_count is not None:
        filters.append(Tour.guest_count <= max_guest_count)

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    tours = result.scalars().all()

    # Process each tour to calculate average rating before conversion to schema
    response_tours = []
    for tour in tours:
        # Calculate average rating
        if tour.tour_reviews:
            avg_rating = sum(review.rating for review in tour.tour_reviews) / len(tour.tour_reviews)
        else:
            avg_rating = 0.0

        # Use ORM mode to convert to schema
        tour_out = TourOut.from_orm(tour)
        tour_out.average_rating = avg_rating
        response_tours.append(tour_out)

    return response_tours


@router.get("/resume/{resume_id}/tours", response_model=List[TourOut])
async def list_tours_by_resume(
        resume_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    resume_result = await session.execute(
        select(Resume.guide_id).where(Resume.resume_id == resume_id)
    )
    guide_id = resume_result.scalar_one_or_none()

    if guide_id is None:
        raise HTTPException(status_code=404, detail="Resume not found.")

    result = await session.execute(
        select(Tour)
        .options(
            selectinload(Tour.addresses),
            selectinload(Tour.languages),
            selectinload(Tour.tour_reviews)
        )
        .where(Tour.guide_id == guide_id)
    )
    tours = result.scalars().all()

    if not tours:
        raise HTTPException(status_code=404, detail="No tours found for this resume.")

    # Process each tour to calculate average rating before conversion to schema
    response_tours = []
    for tour in tours:
        # Calculate average rating
        if tour.tour_reviews:
            avg_rating = sum(review.rating for review in tour.tour_reviews) / len(tour.tour_reviews)
        else:
            avg_rating = 0.0

        # Use ORM mode to convert to schema
        tour_out = TourOut.from_orm(tour)
        tour_out.average_rating = avg_rating
        response_tours.append(tour_out)

    return response_tours


@router.put("/{tour_id}")
async def edit_tour(
        tour_id: int,
        tour_data: TourCreate,
        session: AsyncSession = Depends(get_async_session),
        guide: User = Depends(validate_guide_resume)
):
    result = await session.execute(
        select(Tour)
        .options(
            selectinload(Tour.addresses),
            selectinload(Tour.languages)
        )
        .where(and_(
            Tour.tour_id == tour_id,
            Tour.guide_id == guide.user_id
        ))
    )
    existing_tour = result.scalar_one_or_none()

    if not existing_tour:
        raise HTTPException(status_code=404, detail="Tour not found or you don't have permission to edit it")

    addresses = await session.execute(
        select(Address).where(Address.address_id.in_(tour_data.destination_ids))
    )
    address_list = addresses.scalars().all()
    if len(address_list) != len(tour_data.destination_ids):
        raise HTTPException(status_code=400, detail="One or more address IDs are invalid.")

    languages = await session.execute(
        select(Language).where(Language.language_id.in_(tour_data.language_ids))
    )
    language_list = languages.scalars().all()
    if len(language_list) != len(tour_data.language_ids):
        raise HTTPException(status_code=400, detail="One or more language IDs are invalid.")

    tour_dict = tour_data.dict(exclude={"destination_ids", "language_ids", "photo_gallery"})

    if isinstance(tour_dict.get("date"), datetime):
        tour_dict["date"] = tour_dict["date"].date()

    for key, value in tour_dict.items():
        setattr(existing_tour, key, value)

    existing_tour.addresses = address_list
    existing_tour.languages = language_list

    await session.commit()
    await session.refresh(existing_tour)

    return {"msg": "Tour updated successfully"}

@router.delete("/{tour_id}")
async def delete_tour(
    tour_id: int,
    session: AsyncSession = Depends(get_async_session),
    guide: User = Depends(validate_guide_resume)
):
    tour = await session.get(Tour, tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found.")
    if tour.guide_id != guide.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this tour.")

    await session.delete(tour)
    await session.commit()
    return {"message": "Tour deleted successfully"}
