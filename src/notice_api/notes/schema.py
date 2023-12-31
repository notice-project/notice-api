from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Field, SQLModel


class Bookshelf(SQLModel, table=True):
    """A bookshelf for the associated user."""

    __tablename__ = "bookshelf"  # pyright: ignore[reportGeneralTypeIssues]

    id: Optional[UUID] = Field(None, primary_key=True)
    title: str
    created_at: datetime = Field(sa_column_kwargs={"server_default": func.now()})
    user_id: str = Field(foreign_key="user.id", index=True)


class Note(SQLModel, table=True):
    """A note for the associated user."""

    __tablename__ = "note"  # pyright: ignore[reportGeneralTypeIssues]

    id: Optional[UUID] = Field(None, primary_key=True)
    title: str
    content: str
    created_at: datetime = Field(sa_column_kwargs={"server_default": func.now()})
    bookshelf_id: UUID = Field(foreign_key="bookshelf.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
