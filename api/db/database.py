import asyncio
from typing import AsyncIterator
from sqlalchemy.orm import (
    DeclarativeBase,
)

from sqlalchemy import MetaData, pool
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncSession,
    async_scoped_session,
    AsyncAttrs
)
from api.utils.settings import settings

# Create an asynchronous engine with future usage enabled
class Base(AsyncAttrs, DeclarativeBase):
    metadata = MetaData(schema='public')

DB_URL: str = settings.DB_URL
engine = create_async_engine(
    url=DB_URL,
    future=True,
    poolclass=pool.AsyncAdaptedQueuePool,
    # The number of permanent connections to keep in the pool.
    # This determines the base number of connections that will be created and maintained.
    pool_size=5,
    # The maximum number of connections that can be created 
    # over and above the pool_size when all connections are in use.
    max_overflow=10,
    # The maximum time to wait for a connection from the pool if all 
    # connections are busy before raising an error.
    pool_timeout=30,
    # Time in seconds to recycle (reconnect) a connection.
    # This is useful to avoid issues with idle connections being closed by the database.
    pool_recycle=18000
)

# Create an asynchronous session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False
)


AsyncScopedSession = async_scoped_session(
    session_factory=async_session_factory,
    scopefunc=asyncio.current_task
)

async def create_tables():
    """
    Creates all tables
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncIterator[AsyncSession]:
    """
    Dependency to provide a database session for each request.
    Handles session lifecycle including commit and rollback.
    """
    async with AsyncScopedSession() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await AsyncScopedSession.remove()
            await session.aclose()
