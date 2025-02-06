from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
import asyncio

DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_zmfCU4Eu6Wgt@ep-blue-rain-a5g5bimu.us-east-2.aws.neon.tech/neondb"

Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Keep echo for debugging if you like
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_recycle=300,  # 5 minutes
    pool_timeout=30,  # 30 seconds
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
