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

DROPBOX_ACCESS_TOKEN = "sl.u.AFgJhC98Nde0lLx73gsxSKbjvmrRYgRUbksbfQYduQ6F5-kmX4Q-0XKtH25-KxvOd0WEHCFhQ3d-vITiRg2aAJ6jgxW3lVC3-H58eB2EWqAqvNzONFfqarHoU6FM5wu2LldgRfajkC_-gA9dRx6NhEfyx1ilDPT2kRMv7gqhvUy3yqlk3wG9nFyG09q54KNJ3sDrvMpSKYqCIgoDOLAgEdvDtrGcwvhL9iAeesrbxn9QcJSjpPKV0-jg3sJ6VID6za7mGieKV1W04Ef-pa9kqTGsHKe8tjw80Kk708t-f0K4AAwVo773LX3uUITgXy7LDgU2kuMVqltbPqk5ch90bQ5GUlcmqNaTrAqZv1BvpRyaG6aXnTpTTtIrdQ2dxOCfQ7gcpyLZmMNmVX7Vi0wVEOZg9d0CCTZxqtcZW8l5CwQ4BjLR4enzKEOpdf31Z1dYFapGBBt-n0vu8TU1sQmHkePfyJDlamsVrLuUm36AwzUI4Yul_6qMQZrop_7QraB9GTR-5NNrpJpaYCbBKffMrRHYvC9xkRjDEjsDJOkdFcnL-HZB8g6I5X_D_PnxBDf52xqQnIWYuwtQrZUTCokLwXUaQavpkuG8pDUVRYjbnhLMk2rZrQqSZ0mAed21rCK0y15LJPfJVx5dM3F7fgLRRQ4N42pQwRlPtrehPXFORqZWZH9BuFxiciSG09Wk3PJJolLSI9N7CU26BfTiKQLL59IWSVSfLPYLQ5sQaBWXgk-v4b1i4lDjKjGwhonbl88ml2EAfNnpWef5z_pj-bZvgsOKSXejDXkU0CDY2C9Wj5e5AGWH8Xc6IqB1D5cSO1Lqh_YeaR1uKBoQAmTJKD9g9MoFrGYNh7LBileHBx3HZsmH5yredYI-8caMvDS_jERf_cLD9D3aez63fu-b10XLuvm4Eix5gQjRlzQjcVWrPYMg_zBLtkpFtFHwauGSDysONylcZnPbpDxVg5aEFZHoptWtZhdwzQvnf0ZCY4zt59mWldKvCTQLGHuXZEJZEVPMFTpqa9pBPDFxEUaViSVF-sHsGnWD2bfQFxi0M3eMSg_q2W6RGBS97pXUjAZbZvdE0Dk8l-Cs8IkBqo34n1rw4_ohNmDpGhQkednkyIj3YQ_2Or-l3y7mTf7cmJM3_sfxIxsFmcpIAuzp8mk5P5P3ejbFGAAnkm06oqHUTaLXNmxcAN09-mnJFg0Be3PBwS-S3XznheM7hiOT9J7zr7X-RxjSfW5hcSSsQ8Qv69w3H4oDscipKpWxht5d7D5dBWRNYAyI65sngNkOZ2Sk-F8AJVqm"
async def save_upload_file(upload_file: UploadFile) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = os.path.splitext(upload_file.filename)[1]
    filename = f"{timestamp}_{unique_id}{file_extension}"
    dropbox_path = f"/uploads/tours/{filename}"

    file_content = await upload_file.read()

    def upload_to_dropbox() -> str:
        try:
            dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
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
            selectinload(Tour.languages),
            selectinload(Tour.tour_reviews)
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

    return [TourOut.from_orm(tour) for tour in tours]


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

    return [TourOut.from_orm(tour) for tour in tours]


@router.put("/{tour_id}")
async def edit_tour(
        tour_id: int,
        tour_data: str = Form(...),
        session: AsyncSession = Depends(get_async_session),
        guide: User = Depends(validate_guide_resume)
):
    try:
        tour_data_obj = TourCreate.parse_raw(tour_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Tour Data: {e}")

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
        select(Address).where(Address.address_id.in_(tour_data_obj.destination_ids))
    )
    address_list = addresses.scalars().all()
    if len(address_list) != len(tour_data_obj.destination_ids):
        raise HTTPException(status_code=400, detail="One or more address IDs are invalid.")

    languages = await session.execute(
        select(Language).where(Language.language_id.in_(tour_data_obj.language_ids))
    )
    language_list = languages.scalars().all()
    if len(language_list) != len(tour_data_obj.language_ids):
        raise HTTPException(status_code=400, detail="One or more language IDs are invalid.")

    tour_dict = tour_data_obj.dict()

    if isinstance(tour_dict.get("date"), datetime):
        tour_dict["date"] = tour_dict["date"].date()

    tour_dict.pop("destination_ids", None)
    tour_dict.pop("language_ids", None)

    tour_dict.pop("photo_gallery", None)

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
