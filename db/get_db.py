from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import AsyncSessionLocal

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()