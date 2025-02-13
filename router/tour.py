import dropbox
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload
from starlette.concurrency import run_in_threadpool

from db.models import Tour, User, Address, Language
from db.schemas import TourCreate, TourOut
from db.get_db import get_async_session
from typing import Optional, List
from datetime import date
from core.security import validate_guide_resume
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/tours", tags=["tours"])

DROPBOX_ACCESS_TOKEN = "sl.u.AFiHxuBg0Jp_14vS5Zo8XmlMn3lqUllubX9TKSkJxRN2HUaUw6uZHe6nGIrdx36qmgScN5YKpTw4Uol0Et9zPstUcKeknMVx0xu2KUqL4lLMGJGtty1NNwooDwBnREYnPWS--aAOIo-3xd2CTFjFGNuF4ZpMB2LIdWo2DGFPgBSTbskTtNplzP5qNpHcJITfSMGrk0KB4am9aVgr6-31FV211taO3vwpL7DRT1KcAPtgAnHHPCx-4JHGJe-0rz_LNZlVIMkh_qzo0KXjQwWhKcQK1KP6YHhYwM7QbvSr7nJHRQYlJJap09JTJCpMyWhs0p3e3_gp_wRuOF34mvVIxlTyuJEVWMqTVSGVeGFCvN5YkSQrKRWlWzz3SKzUvWIxPopr9N5x80TPfHE31L3RwsKTboJsMz74dszXAx5U8oSyFSjrHY9N1uih8EF1Y3lIEtW-wiIRvBxZWwtXdI6ABJzDOTtM4oemCYr7Yj2B9deu9cO8B_MBfuSZhICzNOJIFM95wHkjwMBKVxUwxwwnV_Ku9D6Fn1LlFn62-ChusZL_bJWSUFNeAbq6YNkUW4jTk-r3Fk6mP3ifmfInUyuX8H6Au0l0mjNzX_I6cxjObFyqTJPjGmYcxSqGh8pwG_22SCY_YsIMCQoTTkER2j64lGWr0fYpjHjxOhpI46Zz_BtEs-gfbpnGsp50rQ0JWT9YfOV6IybvIx0Ihg1Kc8znVW3W0R4n12enq3KXenOKKYX_SYWiq6tFtAeT7u8YuGwTjPCUuxzL6Wz9S8IiEAaG4Gl8r4lCenqTtch85i1Gke8e8LG6uIdOQ0OQOnWN9w6ZM77UvdqVfGHMGLn-z_JOXYOdzS6rmCiPaORtpUwofBX34qMIfi_SO3VvZ45pM8frs-bPJvxYCBl32RlQh_meqyL1rVe0LCMoJy892q53_Pqke1QR-_o_L_r3mtQSmpyYAF4CZ006dTOARZ-39mtxNtKWQrxqYbdFaoUghP9tXSeGsCcCgtKGf66_MA8_1-OX66CvFbXl76FsJz1whgIz8XFu7OG7MFuJFqL5yMnOoxhcFS8HljJ9uRXhAXr5oHPmTosGRhsZvHr3oLzCMR1CY9Z4b6BK_hHUqMPiOJtlhprv469Ws_dHqx7ARaPlP5nIzlzFOMMjaly7KmhPVZLkdW9g4E6hrmqJ1Wqfr9HG5NLDb0hNexpBlo3GLyRF74DphaIV7jLkMvz4Y2WSjtFiO7W5qWghpaTdTxnjH_wHNu0_dFOCYQaUbDdpe38BBh_rSqrmJniCfzjO862uIFDu4zKY";

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


@router.get("/guide/{guide_id}", response_model=List[TourOut])
async def list_tours_by_guide(
    guide_id: int,
    session: AsyncSession = Depends(get_async_session)
):
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
        raise HTTPException(status_code=404, detail="No tours found for this guide.")

    return [TourOut.from_orm(tour) for tour in tours]


# @router.put("/{tour_id}", response_model=TourOut)
# async def update_tour(
#     tour_id: int,
#     tour_data: TourCreate,
#     session: AsyncSession = Depends(get_async_session),
#     guide: User = Depends(validate_guide_resume)
# ):
#     # Fetch the existing tour with relationships loaded
#     result = await session.execute(
#         select(Tour)
#         .options(
#             joinedload(Tour.addresses),
#             joinedload(Tour.languages)
#         )
#         .where(Tour.tour_id == tour_id)
#     )
#     tour = result.unique().scalar_one_or_none()
#
#     if not tour:
#         raise HTTPException(status_code=404, detail="Tour not found.")
#     if tour.guide_id != guide.user_id:
#         raise HTTPException(status_code=403, detail="Not authorized to update this tour.")
#
#     # Validate new relations
#     addresses_result = await session.execute(
#         select(Address).where(Address.address_id.in_(tour_data.destination_ids))
#     )
#     address_list = addresses_result.scalars().all()
#
#     languages_result = await session.execute(
#         select(Language).where(Language.language_id.in_(tour_data.language_ids))
#     )
#     language_list = languages_result.scalars().all()
#
#     if len(address_list) != len(tour_data.destination_ids):
#         raise HTTPException(status_code=400, detail="One or more address IDs are invalid.")
#     if len(language_list) != len(tour_data.language_ids):
#         raise HTTPException(status_code=400, detail="One or more language IDs are invalid.")
#
#     # Update tour fields
#     tour.guest_count = tour_data.guest_count
#     tour.price = tour_data.price
#     tour.price_type = tour_data.price_type
#     tour.payment_type = tour_data.payment_type
#     tour.date = tour_data.date
#     tour.departure_time = tour_data.departure_time
#     tour.return_time = tour_data.return_time
#     tour.duration = tour_data.duration
#     tour.dress_code = tour_data.dress_code
#     tour.not_included = tour_data.not_included
#     tour.included = tour_data.included
#     tour.photo_gallery = tour_data.photo_gallery
#     tour.about = tour_data.about
#     tour.addresses = address_list
#     tour.languages = language_list
#
#     await session.commit()
#     await session.refresh(tour)
#     return TourOut.from_orm(tour)


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