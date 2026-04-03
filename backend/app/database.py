import logging
import ssl as ssl_module

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# Build connect_args for asyncpg SSL
_connect_args = {}
if settings.database_ssl:
    _ssl_ctx = ssl_module.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl_module.CERT_NONE
    _connect_args["ssl"] = _ssl_ctx

try:
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=_connect_args if "asyncpg" in settings.database_url else {},
    )
    async_engine = engine

    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async_session_factory = AsyncSessionLocal

    sync_engine = create_engine(
        settings.database_url_sync,
        echo=False,
    )

    SyncSessionLocal = sessionmaker(
        sync_engine,
        expire_on_commit=False,
    )
except Exception as e:
    logger.error("Failed to create database engines: %s", e)
    engine = None
    async_engine = None
    AsyncSessionLocal = None
    async_session_factory = None
    sync_engine = None
    SyncSessionLocal = None


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not configured")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
