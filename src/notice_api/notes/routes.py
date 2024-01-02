import json
from base64 import b64decode, b64encode
from datetime import datetime
from typing import Annotated, Literal, Optional, cast, overload
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, status
from pydantic import BaseModel
from sqlmodel import col, select

from notice_api.auth.deps import get_current_user
from notice_api.auth.schema import User
from notice_api.db import AsyncSession, get_async_session
from notice_api.notes.deps import get_current_note
from notice_api.notes.schema import Note, NoteContent, NoteCreate, NoteRead

router = APIRouter(prefix="/bookshelves/{bookshelf_id}/notes", tags=["notes"])


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
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    order: Literal["asc", "desc"] = "desc",
    sort: Literal["title", "created_at"] = "created_at",
) -> GetNotesResponse:
    statement = (
        select(col(Note.id), col(Note.title), col(Note.created_at))
        .where(col(Note.user_id) == user.id, col(Note.bookshelf_id) == bookshelf_id)
        .limit(limit + 1)
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
    if len(notes) > limit:
        last_note = notes[-2]
        next_cursor = NoteCursor(
            id=last_note.id,
            title=last_note.title,
            created_at=last_note.created_at,
        ).encode()

    return GetNotesResponse(
        data=notes[:limit],
        next_cursor=next_cursor,
    )


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


@router.websocket("/{note_id}/ws")
async def take_note(
    websocket: WebSocket,
    bookshelf_id: UUID,
    note_id: UUID,
    repo: Annotated[NoteRepository, Depends(get_note_repository)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
):
    logger = structlog.get_logger("take_note")
    await websocket.accept()

    message = await websocket.receive_json()
    match message:
        case {"type": "init", "payload": session_token}:
            user = await get_current_user(db, session_token=session_token)
        case _:
            await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
            return

    note = await get_current_note(
        bookshelf_id=bookshelf_id,
        note_id=note_id,
        user=user,
        db=db,
    )
    content = await repo.get_note_content(note_id=note_id)

    note_content = NoteContent(
        id="root",
        type="RootNode",
        value=note.title,
        children=content,
    )
    await websocket.send_json({"type": "note", "payload": note_content})

    while True:
        message = await websocket.receive_json()
        match message:
            case {
                "type": "update",
                "payload": {"index": index, "content": content},
            }:
                logger.info("Received update", note_id=note.id, index=index)
                await repo.update_note_content_partial(
                    note_id=note_id,
                    index=index,
                    content=content,
                )
                logger.info("Note updated", note_id=note.id, index=index)
                await websocket.send_json(
                    {"type": "update", "payload": updated_content}
                )
            case {"type": "update all", "payload": new_children}:
                logger.info(
                    "Received full update",
                    note_id=note.id,
                    children_count=len(new_children),
                )
                await repo.update_note_content(
                    note_id=note_id,
                    content=new_children,
                )
                updated_content = await repo.get_note_content(note_id)
                logger.info(
                    "Full update complete",
                    note_id=note.id,
                    children_count=len(updated_content),
                )
                await websocket.send_json(
                    {"type": "update", "payload": updated_content}
                )
            case {"type": "update title", "payload": new_title}:
                logger.info("Received title update", note_id=note.id, title=new_title)
                await repo.update_note_title(note_id=note_id, title=new_title)
                logger.info("Title updated", note_id=note.id, title=new_title)
            case _:
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
