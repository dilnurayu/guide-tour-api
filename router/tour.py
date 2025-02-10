import dropbox
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
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

DROPBOX_ACCESS_TOKEN = "sl.u.AFgSeZb16eVH7auTKVajOUYpb6NdfSc23RCFBTu3J3Mh7yYe6ifGMrdhqGjwFwXZtBNQqSbZoKMjOS5EZWI72htqT4BjfFh4lFrpaCNgE1fMzZt6767mgFJInI0LcW184iz8BpgU3TmugOuESeNr1ZTynGIIlnBpvbOgBkA4dBVCazMkViAmck7VQXkUfO2vCNLVyfRaHIrZa18EAf5GlVuaTP3wJJ81brBoRKLkTSyvL6V0yHkbBG9nGfd4ZSEJqssxgmHBwiJL5OO2sexWBqUX0PoRgGmoVh7NpkI07lWXUbGIfjxe-ySqnfKwfenN3D3la9XFOzr8Pt2ZGEmaM3Uq9ybPO4CmjBgJbcFDkFipjINQzHNX60NIpzBAvVbTXfKfxpD0DUkZ8gP4ZIagSBqvQ81r4qBIodrKIL9NlzM5QdncIcMPbo6QS28-f7FW-AjhkqeEnKZIYF8QNfx-AwK_5jpuPvylGISTdUiy51EgttnosOrKHLBDgKrSKhy_sfa8FRyM95YpseJ0hHptY7RWmPBDIX_NPNYUGVhmpZU_54g-JZqAZB-cYk0xoaawpEyu7Iz70f7NajQTSqDnYyg0rqRbQiehCShUuEjOqRPEQbZta5XJDPC0JVOSTyV3DzB4XJuXt5GEBH2WzeutR-5VWQqijf8HsymWrMqwaRWhRdJM7oapNv2rh3lCy0yPyzMvOXrB3BD0HC89zix1cFp2gSZ2C9LKRaFyXQcVNI9NtGn8InTklUZ3fcs9SD17Qxrg44fB_GSBASg9XgE3dY75aUn_n-ALlOmsxW6OEsCDjXHzu4_yrJPyABDWdOtwEYV5YgTPvGgy4MB7MJXOIwvOJpPHmMS-pZydhW7LUOQMDw5fYkmtb6SsMw2cWEuvkDlErllG-5ocbLCHX1anQNWuPxNDPYW9aKCRNFWAV7w2ZPSoK0BkTgvRNLvFSbrHnCs2BNTLODo2D9iIRegdmd1n2C8tAjyArwEvGAYmcbbAXQSpxFv-MWr93Pv9XggT-JH9hKULxbhq6rj_Pa04m243X3TdMDOeTebJxNTuVmf8QZTqsGNeWZmhSGxmnh9dPDsthfHPKWwRoAn22Ks6_6QNJdWdqv7UFS8L87n4owrtozPQUiAONgDZotzAfsaQvsaXCqDa0pxvKoIPi5psqBk9GcmbW3DaQ7588We83LEPIk7ege1GZ0c902L5OITzj0doQIuIIoEm4Y95dmoEAJfWvgy4l50otiALLnApPGYMkm12LX7ioZ-HZt8fv1fP7JAA_4gfA9fTn39bSe9z4vVw";

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
