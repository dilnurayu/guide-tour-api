from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import guide_required, tourist_required
from db.get_db import get_async_session
from db.models import User, Address
from db.schemas import ProfileOut

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/guide", response_model=ProfileOut)
async def guide_profile(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(guide_required),
):
    result = await session.execute(
        select(User.name, User.email, Address)
        .join(Address, User.address_id == Address.address_id, isouter=True)
        .where(User.user_id == current_user.user_id)
    )
    user_data = result.one_or_none()

    if not user_data:
        raise HTTPException(status_code=404, detail="User profile not found.")

    user_name, email, address = user_data
    return ProfileOut(user_name=user_name, email=email, address=address)



@router.get("/tourist", response_model=ProfileOut)
async def guide_profile(
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(tourist_required),
):
    result = await session.execute(
        select(User.name, User.email, Address.address_id)
        .join(Address, User.address_id == Address.address_id, isouter=True)
        .where(User.user_id == current_user.user_id)
    )
    user_data = result.one_or_none()

    if not user_data:
        raise HTTPException(status_code=404, detail="User profile not found.")

    user_name, email, address_id = user_data
    return ProfileOut(user_name=user_name, email=email, address_id=address_id)