from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Resume
from db.schemas import ResumeCreate, ResumeOut
from db.get_db import get_async_session
from typing import Optional

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/", response_model=ResumeOut)
async def create_resume(
        resume: ResumeCreate,
        session: AsyncSession = Depends(get_async_session)
):
    # Create new resume
    new_resume = Resume(
        user_id=resume.user_id,
        languages=",".join(map(str, resume.languages)) if resume.languages else None,
        addresses=",".join(map(str, resume.addresses)) if resume.addresses else None,
        bio=resume.bio,
        experience_start_date=resume.experience_start_date,
        rating=resume.rating,
    )

    session.add(new_resume)
    await session.commit()
    await session.refresh(new_resume)
    return new_resume


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(
        resume_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Resume).where(Resume.resume_id == resume_id)
    )
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return resume


@router.get("/", response_model=list[ResumeOut])
async def list_resumes(
        session: AsyncSession = Depends(get_async_session),
        skip: int = 0,
        limit: int = 10
):
    result = await session.execute(
        select(Resume)
        .offset(skip)
        .limit(limit)
    )
    resumes = result.scalars().all()
    return resumes


# Additional useful endpoints

@router.put("/{resume_id}", response_model=ResumeOut)
async def update_resume(
        resume_id: int,
        resume_data: ResumeCreate,
        session: AsyncSession = Depends(get_async_session)
):
    # Get existing resume
    result = await session.execute(
        select(Resume).where(Resume.resume_id == resume_id)
    )
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    # Update resume fields
    resume.user_id = resume_data.user_id
    resume.languages = ",".join(map(str, resume_data.languages)) if resume_data.languages else None
    resume.addresses = ",".join(map(str, resume_data.addresses)) if resume_data.addresses else None
    resume.bio = resume_data.bio
    resume.experience_start_date = resume_data.experience_start_date
    resume.rating = resume_data.rating

    await session.commit()
    await session.refresh(resume)
    return resume


@router.delete("/{resume_id}")
async def delete_resume(
        resume_id: int,
        session: AsyncSession = Depends(get_async_session)
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
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Resume).where(Resume.user_id == user_id)
    )
    resumes = result.scalars().all()
    return resumes


@router.get("/search/", response_model=list[ResumeOut])
async def search_resumes(
        user_id: Optional[int] = None,
        min_rating: Optional[float] = None,
        session: AsyncSession = Depends(get_async_session)
):
    query = select(Resume)

    if user_id is not None:
        query = query.where(Resume.user_id == user_id)
    if min_rating is not None:
        query = query.where(Resume.rating >= min_rating)

    result = await session.execute(query)
    resumes = result.scalars().all()
    return resumes