from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
import asyncio

DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_zmfCU4Eu6Wgt@ep-blue-rain-a5g5bimu.us-east-2.aws.neon.tech/neondb"

Base = declarative_base()


def create_engine_with_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return create_async_engine(
        DATABASE_URL,
        echo=True,
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


engine = create_engine_with_loop()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

