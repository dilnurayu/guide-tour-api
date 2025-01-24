from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_zmfCU4Eu6Wgt@ep-blue-rain-a5g5bimu.us-east-2.aws.neon.tech/neondb"

Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

