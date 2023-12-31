from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import notice_api.auth.schema as auth_schema  # noqa: F401
import notice_api.notes.schema as notes_schema  # noqa: F401
from notice_api.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, future=True)
AsyncSessionFactory = sessionmaker[AsyncSession](  # pyright: ignore[reportGeneralTypeIssues]
    engine,  # pyright: ignore[reportGeneralTypeIssues]
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session
