from typing import AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker
)
from sqlalchemy import MetaData
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from decouple import config

class Base(DeclarativeBase):
    metadata = MetaData(schema='public')

DB_URL = config("DB_URL")
engine = create_async_engine(url=DB_URL)

async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False
)

async def create_tables():
    """
    
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_db() -> AsyncIterator[AsyncSession]:
    """
    
    """
    async with async_session_factory() as session:
        try:
            yield session
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()
