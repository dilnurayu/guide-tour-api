from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.security import create_access_token, get_password_hash
from db.models import User
from db.schemas import UserCreate, Token
from db.get_db import get_async_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Token)
async def signup(
        user: UserCreate,
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(User).where(User.email == user.email)
    )
    user_in_db = result.scalar_one_or_none()

    if user_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    hashed_password = get_password_hash(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        address=user.address,
        user_type=user.user_type,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    access_token = create_access_token({"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}