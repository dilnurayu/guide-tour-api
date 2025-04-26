from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Language
from db.schemas import LanguageCreate, LanguageOut
from db.get_db import get_async_session

router = APIRouter(prefix="/languages", tags=["languages"])


@router.post("/", response_model=LanguageOut)
async def create_language(
    data: LanguageCreate,
    session: AsyncSession = Depends(get_async_session),
):
    new_language = Language(
        name=data.name,
    )
    session.add(new_language)
    await session.commit()
    await session.refresh(new_language)
    return new_language


@router.get("/{language_id}", response_model=LanguageOut)
async def get_language(
    language_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Language).where(Language.id == language_id)
    )
    language = result.scalar_one_or_none()

    if not language:
        raise HTTPException(status_code=404, detail="Language not found.")
    return language


@router.get("/", response_model=list[LanguageOut])
async def list_languages(
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Language))
    languages = result.scalars().all()
    return languages


@router.delete("/{language_id}", response_model=LanguageOut)
async def delete_language(
    language_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Language).where(Language.id == language_id)
    )
    language = result.scalar_one_or_none()

    if not language:
        raise HTTPException(status_code=404, detail="Language not found.")

    await session.delete(language)
    await session.commit()
    return language
