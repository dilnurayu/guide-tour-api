from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.security import create_access_token, verify_password, get_password_hash
from db.models import User
from db.schemas import UserCreate, Token, SignIn
from db.get_db import get_async_session
from router.tour import save_upload_file

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=Token)
async def signup(
    name: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    address_id: Optional[int] = Form(None),
    user_type: str = Form(...),
    profile_photo: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(User).where(User.email == email))
    user_in_db = result.scalar_one_or_none()
    if user_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    profile_photo_url = None
    if profile_photo:
        profile_photo_url = await save_upload_file(profile_photo)

    hashed_password = get_password_hash(password)
    new_user = User(
        name=name,
        email=email,
        hashed_password=hashed_password,
        address_id=address_id,
        user_type=user_type,
        profile_photo=profile_photo_url,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    access_token = create_access_token({"sub": new_user.email, "role": new_user.user_type})
    return {"access_token": access_token, "token_type": "bearer"}

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
