from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from core.security import tourist_required
from db.models import Review, User
from db.schemas import ReviewCreate, ReviewOut
from db.get_db import get_async_session
from typing import Optional

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewOut)
async def create_review(
        review: ReviewCreate,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(tourist_required),
):
    new_review = Review(
        guide_id=review.guide_id,
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


@router.get("/", response_model=list[ReviewOut])
async def list_reviews(
        session: AsyncSession = Depends(get_async_session),
        skip: int = 0,
        limit: int = 10,
        min_rating: Optional[float] = None,
        guide_id: Optional[int] = None
):
    query = select(Review)

    filters = []
    if min_rating is not None:
        filters.append(Review.rating >= min_rating)
    if guide_id is not None:
        filters.append(Review.guide_id == guide_id)

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    reviews = result.scalars().all()
    return reviews
