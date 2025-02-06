from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import AsyncSessionLocal

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    logger.info("Creating new database session")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error: {e}")
            raise
        finally:
            logger.info("Closing database session")
            await session.close()