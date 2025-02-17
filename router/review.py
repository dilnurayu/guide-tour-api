from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Review, Resume, User
from db.schemas import ReviewCreate, ReviewOut
from db.get_db import get_async_session
from typing import List
from core.security import tourist_required, guide_required

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("/", response_model=ReviewOut)
async def create_review(
    review: ReviewCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(tourist_required),
):
    new_review = Review(
        resume_id=review.resume_id,
        tourist_id=current_user.user_id,
        title=review.title,
        description=review.description,
        rating=review.rating,
    )

    session.add(new_review)
    await session.commit()
    await session.refresh(new_review)
    return new_review

@router.get("/{review_id}", response_model=ReviewOut)
async def get_review(
    review_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Review).where(Review.review_id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")
    return review


@router.get("/guide/me", response_model=List[ReviewOut])
async def list_my_reviews(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(guide_required)
):
    query = (
        select(Review)
        .join(Resume, Resume.resume_id == Review.resume_id)
        .where(Resume.guide_id == current_user.user_id)
    )
    result = await session.execute(query)
    reviews = result.scalars().all()
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for your profile.")
    return reviews


@router.get("/resume/{resume_id}", response_model=List[ReviewOut])
async def list_reviews_by_resume(
        resume_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    query = select(Review).where(Review.resume_id == resume_id)
    result = await session.execute(query)
    reviews = result.scalars().all()

    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this resume.")

    return reviews
