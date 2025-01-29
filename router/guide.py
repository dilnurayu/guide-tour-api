from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import GuideLanguages, GuideAddress
from db.schemas import GuideLanguageCreate, GuideLanguageOut, GuideAddressCreate, GuideAddressOut
from db.get_db import get_async_session

router = APIRouter(prefix="/guides", tags=["guides"])


@router.post("/languages", response_model=GuideLanguageOut)
async def add_guide_language(
        data: GuideLanguageCreate,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(GuideLanguages).where(
            (GuideLanguages.guide_id == data.guide_id) &
            (GuideLanguages.language_id == data.language_id)
        )
    )
    existing_entry = result.scalar_one_or_none()

    if existing_entry:
        raise HTTPException(
            status_code=400,
            detail="This language is already assigned to this guide."
        )

    new_entry = GuideLanguages(
        guide_id=data.guide_id,
        language_id=data.language_id
    )
    session.add(new_entry)
    await session.commit()
    await session.refresh(new_entry)
    return new_entry


@router.post("/addresses", response_model=GuideAddressOut)
async def add_guide_address(
        data: GuideAddressCreate,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(GuideAddress).where(
            (GuideAddress.guide_id == data.guide_id) &
            (GuideAddress.address_id == data.address_id)
        )
    )
    existing_entry = result.scalar_one_or_none()

    if existing_entry:
        raise HTTPException(
            status_code=400,
            detail="This address is already assigned to this guide."
        )

    new_entry = GuideAddress(
        guide_id=data.guide_id,
        address_id=data.address_id
    )
    session.add(new_entry)
    await session.commit()
    await session.refresh(new_entry)
    return new_entry