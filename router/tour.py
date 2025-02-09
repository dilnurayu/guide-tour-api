from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from db.models import Tour, User, Address, Language
from db.schemas import TourCreate, TourOut
from db.get_db import get_async_session
from typing import Optional, List
from datetime import date
from core.security import guide_required, validate_guide_resume
import os
import uuid
from datetime import datetime
import aiofiles

router = APIRouter(prefix="/tours", tags=["tours"])


async def save_upload_file(upload_file: UploadFile) -> str:
    UPLOAD_DIR = "uploads/tours"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = os.path.splitext(upload_file.filename)[1]
    filename = f"{timestamp}_{unique_id}{file_extension}"

    file_path = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await upload_file.read()
        await out_file.write(content)

    return f"/uploads/tours/{filename}"




@router.post("/")
async def create_tour(
    tour_data: str = Form(...),
    photos: List[UploadFile] = File(None),
    session: AsyncSession = Depends(get_async_session),
    guide: User = Depends(validate_guide_resume)
):
    try:
        tour_data_obj = TourCreate.parse_raw(tour_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Tour Data: {e}")

    addresses = await session.execute(
        select(Address).where(Address.address_id.in_(tour_data_obj.destination_ids))
    )
    address_list = addresses.scalars().all()

    languages = await session.execute(
        select(Language).where(Language.language_id.in_(tour_data_obj.language_ids))
    )
    language_list = languages.scalars().all()

    if len(address_list) != len(tour_data_obj.destination_ids):
        raise HTTPException(status_code=400, detail="One or more address IDs are invalid.")
    if len(language_list) != len(tour_data_obj.language_ids):
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

    tour_dict = tour_data_obj.dict()

    if isinstance(tour_dict.get("date"), datetime):
        tour_dict["date"] = tour_dict["date"].date()

    if photo_urls:
        tour_dict['photo_gallery'] = photo_urls

    tour_dict.pop("destination_ids", None)
    tour_dict.pop("language_ids", None)

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
            selectinload(Tour.languages)
        )
        .where(Tour.guide_id == current_user.user_id)
    )
    tours = result.scalars().all()
    if not tours:
        raise HTTPException(status_code=404, detail="No tours found for this guide.")
    return [TourOut.from_orm(tour) for tour in tours]


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
