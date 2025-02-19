from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload
from db.models import Resume, User, Review, Language, Address
from db.schemas import ResumeCreate, ResumeOut
from db.get_db import get_async_session
from typing import Optional, List
from core.security import guide_required, oauth2_scheme

router = APIRouter(prefix="/resumes", tags=["resumes"])


async def get_average_rating(guide_id: int, session: AsyncSession) -> float:
    """Calculate the average rating for a guide's resumes."""
    result = await session.execute(
        select(func.avg(Review.rating))
        .join(Resume, Resume.resume_id == Review.resume_id)
        .where(Resume.guide_id == guide_id)
    )
    return result.scalar() or 0.0


async def get_resume_with_relations(resume_id: int, session: AsyncSession):
    """Get a resume with all its related data."""
    result = await session.execute(
        select(Resume)
        .options(joinedload(Resume.languages), joinedload(Resume.addresses))
        .where(Resume.resume_id == resume_id)
    )
    return result.unique().scalar_one_or_none()


async def validate_and_get_relations(resume_data: ResumeCreate, session: AsyncSession):
    """Validate and get language and address relations."""
    languages = await session.execute(
        select(Language).where(Language.language_id.in_(resume_data.languages))
    )
    addresses = await session.execute(
        select(Address).where(Address.address_id.in_(resume_data.addresses))
    )
    return languages.scalars().all(), addresses.scalars().all()


@router.post("/", dependencies=[Depends(oauth2_scheme)])
async def create_resume(
        resume: ResumeCreate,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(guide_required),
):
    existing = await session.execute(
        select(Resume).where(Resume.guide_id == current_user.user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="A resume already exists for this guide user."
        )

    languages, addresses = await validate_and_get_relations(resume, session)

    new_resume = Resume(
        guide_id=current_user.user_id,
        bio=resume.bio,
        experience_start_date=resume.experience_start_date,
        price=resume.price,
        price_type=resume.price_type,
        languages=languages,
        addresses=addresses,
    )

    session.add(new_resume)
    await session.commit()
    return {"msg": "Resume created successfully"}


@router.get("/me", response_model=ResumeOut, dependencies=[Depends(oauth2_scheme)])
async def get_my_resume(
    current_user: User = Depends(guide_required),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Resume)
        .options(joinedload(Resume.languages), joinedload(Resume.addresses))
        .where(Resume.guide_id == current_user.user_id)
    )
    resume = result.unique().scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found for the current guide.")

    resume.rating = await get_average_rating(resume.guide_id, session)
    return ResumeOut.from_orm(resume)


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(
    resume_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Resume, User.name.label("user_name"))
        .options(joinedload(Resume.languages), joinedload(Resume.addresses))
        .join(User, Resume.guide_id == User.user_id)
        .where(Resume.resume_id == resume_id)
    )
    resume_row = result.unique().one_or_none()

    if not resume_row:
        raise HTTPException(status_code=404, detail="Resume not found.")

    resume, user_name = resume_row
    resume.rating = await get_average_rating(resume.guide_id, session)
    return ResumeOut.from_orm(resume, guide_name=user_name)


@router.get("/", response_model=List[ResumeOut])
async def list_resumes(
        session: AsyncSession = Depends(get_async_session),
        skip: int = 0,
        limit: int = 10,
        user_id: Optional[int] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        language_ids: Optional[List[int]] = Query(None, description="Filter by language IDs"),
        address_ids: Optional[List[int]] = Query(None, description="Filter by address IDs"),
        price_type: Optional[str] = None,
        experience_start_date: Optional[date] = None,
):
    query = (
        select(Resume, User.name.label("user_name"))
        .options(joinedload(Resume.languages), joinedload(Resume.addresses))
        .join(User, Resume.guide_id == User.user_id)
    )

    filters = []
    if user_id is not None:
        filters.append(Resume.guide_id == user_id)
    if price_type is not None:
        filters.append(Resume.price_type == price_type)
    if experience_start_date is not None:
        filters.append(Resume.experience_start_date == experience_start_date)
    if min_price is not None:
        filters.append(Resume.price >= min_price)
    if max_price is not None:
        filters.append(Resume.price <= max_price)
    if language_ids is not None:
        query = query.join(Resume.languages).where(Language.language_id.in_(language_ids))
    if address_ids is not None:
        query = query.join(Resume.addresses).where(Address.address_id.in_(address_ids))

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    resumes = result.unique().all()

    response_resumes = []
    for resume, user_name in resumes:
        rating = await get_average_rating(resume.guide_id, session)
        if min_rating is not None and rating < min_rating:
            continue
        if max_rating is not None and rating > max_rating:
            continue
        resume.rating = rating
        response_resumes.append(ResumeOut.from_orm(resume, guide_name=user_name))
    return response_resumes


@router.put("/me", response_model=ResumeOut, dependencies=[Depends(oauth2_scheme)])
async def update_my_resume(
        resume_data: ResumeCreate,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(guide_required),
):
    result = await session.execute(
        select(Resume)
        .options(joinedload(Resume.languages), joinedload(Resume.addresses))
        .where(Resume.guide_id == current_user.user_id)
    )
    resume = result.unique().scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found for current guide.")

    languages, addresses = await validate_and_get_relations(resume_data, session)

    resume.languages = languages
    resume.addresses = addresses
    resume.bio = resume_data.bio
    resume.experience_start_date = resume_data.experience_start_date
    resume.price = resume_data.price
    resume.price_type = resume_data.price_type

    await session.commit()
    await session.refresh(resume)

    return ResumeOut.from_orm(resume)


@router.delete("/{resume_id}", dependencies=[Depends(oauth2_scheme)])
async def delete_resume(
    resume_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(guide_required),
):
    result = await session.execute(select(Resume).where(Resume.resume_id == resume_id))
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if resume.guide_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this resume.")

    await session.delete(resume)
    await session.commit()
    return {"message": "Resume deleted successfully"}
