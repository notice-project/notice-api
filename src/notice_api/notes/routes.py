from base64 import b64decode, b64encode
from datetime import datetime
from typing import Annotated, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import col, select

from notice_api.auth.deps import get_current_user
from notice_api.auth.schema import User
from notice_api.db import AsyncSession, get_async_session
from notice_api.notes.schema import Note, NoteCreate, NoteRead

router = APIRouter(prefix="/bookshelves/{bookshelf_id}/notes", tags=["notes"])


async def get_current_note(
    bookshelf_id: UUID,
    note_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Get the current note from the database.

    This function is used as a dependency for endpoints that require a note.

    If the note is not found, or the note does not belong to the current user,
    a 404 error is raised.
    """

    statement = select(Note.id, Note.title, Note.created_at).where(
        col(Note.id) == note_id,
        col(Note.user_id) == user.id,
        col(Note.bookshelf_id) == bookshelf_id,
    )
    result = await db.exec(statement)
    note = result.first()
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )

    id, title, created_at = note
    return Note(
        id=id,
        title=title,
        created_at=created_at,
        user_id=user.id,
        bookshelf_id=bookshelf_id,
    )


class NoteCursor(BaseModel):
    id: UUID
    title: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def decode(cls, cursor: str) -> "NoteCursor":
        return cls.model_validate_json(b64decode(cursor.encode()).decode())

    def encode(self) -> str:
        return b64encode(self.model_dump_json().encode()).decode()


class GetNotesResponse(BaseModel):
    data: list[NoteRead]
    next_cursor: Optional[str] = None


@router.get("/")
async def get_notes(
    bookshelf_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    cursor: Optional[str] = None,
    limit: int = 10,
    order: Literal["asc", "desc"] = "desc",
    sort: Literal["title", "created_at"] = "created_at",
) -> GetNotesResponse:
    statement = (
        select(col(Note.id), col(Note.title), col(Note.created_at))
        .where(col(Note.user_id) == user.id, col(Note.bookshelf_id) == bookshelf_id)
        .limit(limit)
    )

    # First sort by the `sort` parameter, then by the `id` column
    # (`id`: to achieve deterministic ordering).
    sort_order = (
        col(getattr(Note, sort)).desc()
        if order == "desc"
        else col(getattr(Note, sort)).asc()
    )
    id_order = col(Note.id).asc()
    statement = statement.order_by(sort_order, id_order)

    if cursor:
        cursor_obj = NoteCursor.decode(cursor)
        sort_value = getattr(cursor_obj, sort)
        if sort_value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cursor: {cursor}",
            )

        sort_eq = col(getattr(Note, sort)) == sort_value
        id_gt = col(Note.id) > cursor_obj.id
        sort_filter = (
            col(getattr(Note, sort)) < sort_value
            if order == "desc"
            else col(getattr(Note, sort)) > sort_value
        )
        statement = statement.where((sort_eq & id_gt) | sort_filter)

    notes = await db.exec(statement)
    notes = [NoteRead.model_validate(note) for note in notes]

    next_cursor = None
    if len(notes) == limit:
        next_cursor = NoteCursor(
            id=notes[-1].id,
            title=notes[-1].title,
            created_at=notes[-1].created_at,
        ).encode()

    return GetNotesResponse(data=notes, next_cursor=next_cursor)


class CreateNoteResponse(BaseModel):
    data: NoteRead


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_note(
    bookshelf_id: UUID,
    note_create: NoteCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> CreateNoteResponse:
    note = Note(
        title=note_create.title,
        bookshelf_id=bookshelf_id,
        user_id=user.id,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return CreateNoteResponse(data=NoteRead.model_validate(note))


class UpdateNoteResponse(BaseModel):
    data: NoteRead


@router.patch("/{note_id}")
async def update_note(
    note: Annotated[Note, Depends(get_current_note)],
    note_update: NoteCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> UpdateNoteResponse:
    note.title = note_update.title
    await db.commit()
    await db.refresh(note)
    return UpdateNoteResponse(data=NoteRead.model_validate(note))


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note: Annotated[Note, Depends(get_current_note)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
):
    await db.delete(note)
    await db.commit()
