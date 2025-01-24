from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from core.security import decode_access_token
from db.models import User
from db.get_db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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

