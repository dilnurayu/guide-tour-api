from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.testing import future

DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_zmfCU4Eu6Wgt@ep-blue-rain-a5g5bimu.us-east-2.aws.neon.tech/neondb"

Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    future=True,
    poolclass=NullPool,
    connect_args={
        "server_settings": {"application_name": "UzGuide"},
        "command_timeout": 10
    }
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
