"""
Database configuration and setup
SQLite for prototype (free!), PostgreSQL for production
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from .settings import get_settings

settings = get_settings()

# Determine database URL based on environment
if settings.DEBUG:
    # SQLite for development/prototype (FREE!)
    DATABASE_URL = "sqlite+aiosqlite:///./sentient_ai.db"
    SYNC_DATABASE_URL = "sqlite:///./sentient_ai.db"
    echo_sql = True
else:
    # PostgreSQL for production
    DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    SYNC_DATABASE_URL = settings.DATABASE_URL
    echo_sql = False

# Create sync engine for migrations
engine = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
    echo=echo_sql
)

# Create async engine for FastAPI
async_engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=echo_sql
)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False
)

# Base class for models
Base = declarative_base()

async def init_db():
    """Initialize database - creates SQLite file automatically"""
    async with async_engine.begin() as conn:
        # Import all models here to ensure they are registered
        from ..models import companion, message, user
        
        # Create tables (SQLite file created automatically)
        await conn.run_sync(Base.metadata.create_all)
        print(f"✅ Database initialized: {DATABASE_URL}")

async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 