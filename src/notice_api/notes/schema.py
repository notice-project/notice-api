from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, types
from sqlmodel import Field, SQLModel
from typing_extensions import TypedDict


class NoteBase(SQLModel):
    """Base model for a note."""

    title: str


class NoteContent(TypedDict):
    id: str
    type: str
    value: str
    children: list["NoteContent"]


DEFAULT_NOTE_CONTENT: NoteContent = {
    "id": "root",
    "type": "RootNode",
    "value": "",
    "children": [],
}


class Note(NoteBase, table=True):
    """A note for the associated user."""

    __tablename__ = "note"  # pyright: ignore[reportGeneralTypeIssues]

    id: Optional[UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={"default": func.uuid()},
    )
    title: str
    content: NoteContent = Field(
        default=DEFAULT_NOTE_CONTENT,
        sa_type=types.JSON(none_as_null=True),
    )
    transcript_audio_filename: Optional[str] = None
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
