import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Ensure data directory exists
DATA_DIR = "/app/data"
os.makedirs(DATA_DIR, exist_ok=True)

# SQLite database configuration
DATABASE_URL = "sqlite+aiosqlite:////app/data/app.db"

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

# Create async session factory
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create all database tables."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
