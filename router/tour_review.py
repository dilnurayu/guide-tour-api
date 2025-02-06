from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from core.security import tourist_required
from db.models import User, TourReview
from db.schemas import TourReviewCreate, TourReviewOut
from db.get_db import get_async_session
from typing import Optional

router = APIRouter(prefix="/tour-reviews", tags=["tour reviews"])


@router.post("/", response_model=TourReviewOut)
async def create_review(
        tour_review: TourReviewCreate,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(tourist_required),
):
    new_review = TourReview(
        tour_id=tour_review.tour_id,
        tourist_id=current_user.user_id,
        title=tour_review.title,
        description=tour_review.description,
        rating=tour_review.rating,
    )

    session.add(new_review)
    await session.commit()
    await session.refresh(new_review)
    return new_review


@router.get("/{review_id}", response_model=TourReviewOut)
async def get_review(
        review_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(TourReview).where(TourReview.review_id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")
    return review


@router.get("/", response_model=list[TourReviewOut])
async def list_reviews(
        session: AsyncSession = Depends(get_async_session),
        skip: int = 0,
        limit: int = 10,
        min_rating: Optional[float] = None,
        tour_id: Optional[int] = None
):
    query = select(TourReview)

    filters = []
    if min_rating is not None:
        filters.append(TourReview.rating >= min_rating)
    if tour_id is not None:
        filters.append(TourReview.tour_id == tour_id)

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    reviews = result.scalars().all()
    return reviews
