import logging
from datetime import datetime, timedelta
from typing import Union
from fastapi import HTTPException, status, Depends
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import selectinload

from db.models import User
from db.get_db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

async def guide_required(
    current_user: User = Depends(get_current_user),
):
    if current_user.user_type != "guide":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access restricted to guides only"
        )
    return current_user

async def tourist_required(
    current_user: User = Depends(get_current_user),
):
    if current_user.user_type != "tourist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access restricted to tourists only"
        )
    return current_user


async def validate_guide_resume(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(guide_required),
) -> User:
    result = await session.execute(
        select(User)
        .where(User.user_id == current_user.user_id)
        .options(selectinload(User.resumes))
    )
    guide = result.scalar_one_or_none()

    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    if not guide.resumes:
        raise HTTPException(
            status_code=400,
            detail="You must upload a resume before creating a tour",
        )

    return guide