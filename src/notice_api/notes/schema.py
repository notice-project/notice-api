from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Field, SQLModel


class NoteBase(SQLModel):
    """Base model for a note."""

    title: str


class Note(NoteBase, table=True):
    """A note for the associated user."""

    __tablename__ = "note"  # pyright: ignore[reportGeneralTypeIssues]

    id: Optional[UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={"default": func.uuid()},
    )
    title: str
    created_at: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": func.now()}
    )
    bookshelf_id: UUID = Field(foreign_key="bookshelf.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)


class NoteRead(NoteBase):
    """Model for reading a note."""

    id: UUID
    created_at: datetime


class NoteCreate(NoteBase):
    """Model for creating a note."""

    pass


class NoteUpdate(SQLModel):
    """Model for updating a note."""

    title: Optional[str] = None
