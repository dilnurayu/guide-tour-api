from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.models import Resume, User, Review
from db.schemas import ResumeCreate, ResumeOut
from db.get_db import get_async_session
from typing import Optional
from core.security import guide_required, oauth2_scheme

router = APIRouter(prefix="/resumes", tags=["resumes"])


def parse_resume_fields(resume: Resume, average_rating: Optional[float] = 0.0):
    resume.languages = (
        list(map(int, resume.languages.split(","))) if resume.languages else []
    )
    resume.addresses = (
        list(map(int, resume.addresses.split(","))) if resume.addresses else []
    )
    return {
        "resume_id": resume.resume_id,
        "user_id": resume.user_id,
        "languages": resume.languages,
        "addresses": resume.addresses,
        "bio": resume.bio,
        "experience_start_date": resume.experience_start_date,
        "rating": average_rating,
    }


async def get_average_rating(guide_id: int, session: AsyncSession) -> float:
    result = await session.execute(
        select(func.avg(Review.rating))
        .where(Review.guide_id == guide_id)
    )
    average_rating = result.scalar()
    return average_rating or 0.0


@router.post("/", response_model=ResumeOut, dependencies=[Depends(oauth2_scheme)])
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

    new_resume = Resume(
        user_id=current_user.user_id,
        languages=",".join(map(str, resume.languages)) if resume.languages else None,
        addresses=",".join(map(str, resume.addresses)) if resume.addresses else None,
        bio=resume.bio,
        experience_start_date=resume.experience_start_date,
        rating=0,
    )

    session.add(new_resume)
    await session.commit()
    await session.refresh(new_resume)

    return parse_resume_fields(new_resume)


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(
    resume_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Resume).where(Resume.resume_id == resume_id)
    )
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    average_rating = await get_average_rating(resume.user_id, session)
    return parse_resume_fields(resume, average_rating)


@router.get("/", response_model=list[ResumeOut])
async def list_resumes(
    session: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 10,
):
    result = await session.execute(
        select(Resume).offset(skip).limit(limit)
    )
    resumes = result.scalars().all()

    resumes_with_ratings = []
    for resume in resumes:
        average_rating = await get_average_rating(resume.user_id, session)
        resumes_with_ratings.append(parse_resume_fields(resume, average_rating))

    return resumes_with_ratings



@router.put("/{resume_id}", response_model=ResumeOut)
async def update_resume(
    resume_id: int,
    resume_data: ResumeCreate,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Resume).where(Resume.resume_id == resume_id)
    )
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    resume.languages = (
        ",".join(map(str, resume_data.languages)) if resume_data.languages else None
    )
    resume.addresses = (
        ",".join(map(str, resume_data.addresses)) if resume_data.addresses else None
    )
    resume.bio = resume_data.bio
    resume.experience_start_date = resume_data.experience_start_date
    resume.rating = resume_data.rating

    await session.commit()
    await session.refresh(resume)
    return parse_resume_fields(resume)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Resume).where(Resume.resume_id == resume_id)
    )
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    await session.delete(resume)
    await session.commit()
    return {"message": "Resume deleted successfully"}


@router.get("/user/{user_id}", response_model=list[ResumeOut])
async def get_user_resumes(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    # Fetch all resumes for the user
    result = await session.execute(
        select(Resume).where(Resume.user_id == user_id)
    )
    resumes = result.scalars().all()

    # Calculate the average rating for the user
    resumes_with_ratings = []
    for resume in resumes:
        average_rating = await get_average_rating(resume.user_id, session)
        resumes_with_ratings.append(parse_resume_fields(resume, average_rating))

    return resumes_with_ratings


@router.get("/search/", response_model=list[ResumeOut])
async def search_resumes(
    user_id: Optional[int] = None,
    min_rating: Optional[float] = None,
    session: AsyncSession = Depends(get_async_session),
):
    query = select(Resume)

    if user_id is not None:
        query = query.where(Resume.user_id == user_id)
    if min_rating is not None:
        query = query.where(Resume.rating >= min_rating)

    result = await session.execute(query)
    resumes = result.scalars().all()

    return [parse_resume_fields(resume) for resume in resumes]
