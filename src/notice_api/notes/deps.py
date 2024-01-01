from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlmodel import col, select

from notice_api.auth.deps import get_current_user
from notice_api.auth.schema import User
from notice_api.db import AsyncSession, get_async_session
from notice_api.notes.schema import Note


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
