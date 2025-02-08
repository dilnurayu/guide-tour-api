from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.security import create_access_token, verify_password, get_password_hash
from db.models import User
from db.schemas import UserCreate, Token, SignIn
from db.get_db import get_async_session

router = APIRouter(prefix="/auth", tags=["auth"])

#Sign Up
@router.post("/signup", response_model=Token)
async def signup(
    user: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(User).where(User.email == user.email))
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
        address_id=user.address_id,
        user_type=user.user_type,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    access_token = create_access_token({"sub": new_user.email, "role": new_user.user_type})
    return {"access_token": access_token, "token_type": "bearer"}

#Sing In
@router.post("/signin", response_model=Token)
async def signin(
    credentials: SignIn,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token({"sub": user.email, "role": user.user_type})
    return {"access_token": access_token, "token_type": "bearer"}
