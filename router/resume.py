from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from db.models import Resume, User, Review, Language, Address
from db.schemas import ResumeCreate, ResumeOut
from db.get_db import get_async_session
from typing import Optional, List
from core.security import guide_required, oauth2_scheme

router = APIRouter(prefix="/resumes")

async def get_average_rating(guide_id: int, session: AsyncSession) -> float:
    result = await session.execute(
        select(func.avg(Review.rating))
        .where(Review.guide_id == guide_id)
    )
    average_rating = result.scalar()
    return average_rating or 0.0

@router.post("/", dependencies=[Depends(oauth2_scheme)])
async def create_resume(
    resume: ResumeCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(guide_required),
):
    result = await session.execute(
        select(Resume).where(Resume.user_id == current_user.user_id)
    )
    existing_resume = result.scalar_one_or_none()

    if existing_resume:
        raise HTTPException(
            status_code=400, detail="A resume already exists for this guide user."
        )

    languages = await session.execute(
        select(Language).where(Language.language_id.in_(resume.languages))  # Changed from language_ids
    )
    addresses = await session.execute(
        select(Address).where(Address.address_id.in_(resume.addresses))  # Changed from address_ids
    )

    new_resume = Resume(
        user_id=current_user.user_id,
        bio=resume.bio,
        experience_start_date=resume.experience_start_date,
        languages=languages.scalars().all(),
        addresses=addresses.scalars().all(),
        rating=0,
    )

    session.add(new_resume)
    await session.commit()
    await session.refresh(new_resume)
    return {"msg": "created"}

@router.get("/me", response_model=ResumeOut, dependencies=[Depends(oauth2_scheme)])
async def get_my_resume(
    current_user: User = Depends(guide_required),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Resume, User.name.label("user_name"))
        .options(joinedload(Resume.languages), joinedload(Resume.addresses))
        .join(User, Resume.user_id == User.user_id)
        .where(Resume.user_id == current_user.user_id)
    )
    resume_row = result.unique().one_or_none()

    if not resume_row:
        raise HTTPException(status_code=404, detail="Resume not found for the current guide.")

    resume, user_name = resume_row

    resume.rating = await get_average_rating(resume.user_id, session)
    return ResumeOut.from_orm(resume, user_name=user_name)

@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(
    resume_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Resume, User.name.label("user_name"))
        .options(joinedload(Resume.languages), joinedload(Resume.addresses))
        .join(User, Resume.user_id == User.user_id)
        .where(Resume.resume_id == resume_id)
    )
    resume_row = result.unique().one_or_none()

    if not resume_row:
        raise HTTPException(status_code=404, detail="Resume not found.")

    resume, user_name = resume_row

    resume.rating = await get_average_rating(resume.user_id, session)
    return ResumeOut.from_orm(resume, user_name=user_name)

@router.get("/", response_model=List[ResumeOut])
async def list_resumes(
    session: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 10,
    user_id: Optional[int] = None,
    min_rating: Optional[float] = None,
    language_id: Optional[int] = None,
    address_id: Optional[int] = None,
):
    query = select(Resume, User.name.label("user_name")).options(
        joinedload(Resume.languages),
        joinedload(Resume.addresses)
    ).join(User, Resume.user_id == User.user_id)

    if user_id is not None:
        query = query.where(Resume.user_id == user_id)
    if language_id is not None:
        query = query.join(Resume.languages).where(Language.language_id == language_id)
    if address_id is not None:
        query = query.join(Resume.addresses).where(Address.address_id == address_id)

    query = query.offset(skip).limit(limit)

    result = await session.execute(query)
    resume_rows = result.unique().all()
    resumes_with_username = []

    for resume_row in resume_rows:
        resume, user_name = resume_row
        if min_rating is not None:
            rating = await get_average_rating(resume.user_id, session)
            if rating >= min_rating:
                resume.rating = rating
                resumes_with_username.append(ResumeOut.from_orm(resume, user_name=user_name))
        else:
            resume.rating = await get_average_rating(resume.user_id, session)
            resumes_with_username.append(ResumeOut.from_orm(resume, user_name=user_name))

    return resumes_with_username

@router.put("/{resume_id}", response_model=ResumeOut, dependencies=[Depends(oauth2_scheme)])
async def update_resume(
    resume_id: int,
    resume_data: ResumeCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(guide_required),
):
    result = await session.execute(
        select(Resume)
        .options(joinedload(Resume.languages), joinedload(Resume.addresses))
        .where(Resume.resume_id == resume_id)
    )
    resume = result.unique().scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if resume.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this resume.")

    languages = await session.execute(
        select(Language).where(Language.language_id.in_(resume_data.languages)) # Changed from language_ids
    )
    addresses = await session.execute(
        select(Address).where(Address.address_id.in_(resume_data.addresses)) # Changed from address_ids
    )

    resume.languages = languages.scalars().all()
    resume.addresses = addresses.scalars().all()
    resume.bio = resume_data.bio
    resume.experience_start_date = resume_data.experience_start_date

    await session.commit()
    await session.refresh(resume)
    resume.rating = await get_average_rating(resume.user_id, session)

    user_result = await session.execute(select(User.name).where(User.user_id == resume.user_id))
    user_name = user_result.scalar_one()

    return ResumeOut.from_orm(resume, user_name=user_name)


@router.delete("/{resume_id}", dependencies=[Depends(oauth2_scheme)])
async def delete_resume(
    resume_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(guide_required),
):
    result = await session.execute(
        select(Resume).where(Resume.resume_id == resume_id)
    )
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if resume.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this resume.")

    await session.delete(resume)
    await session.commit()
    return {"message": "Resume deleted successfully"}