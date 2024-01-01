from base64 import b64decode, b64encode
from datetime import datetime
from typing import Annotated, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import col, select

from notice_api.auth.deps import get_current_user
from notice_api.auth.schema import User
from notice_api.bookshelves.schema import (
    Bookshelf,
    BookshelfCreate,
    BookshelfRead,
    BookshelfUpdate,
)
from notice_api.db import AsyncSession, get_async_session
from notice_api.notes.schema import Note

router = APIRouter(prefix="/bookshelves", tags=["bookshelves"])


class BookshelfCursor(BaseModel):
    id: UUID
    title: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def decode(cls, cursor: str) -> "BookshelfCursor":
        return cls.model_validate_json(b64decode(cursor.encode()).decode())

    def encode(self) -> str:
        return b64encode(self.model_dump_json().encode()).decode()


class GetBookshelvesResponse(BaseModel):
    data: list[BookshelfRead]
    next_cursor: Optional[str] = None


@router.get("/")
async def get_bookshelves(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    cursor: Optional[str] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    order: Literal["asc", "desc"] = "desc",
    sort: Literal["title", "created_at"] = "created_at",
) -> GetBookshelvesResponse:
    note_count_subquery = (
        select(func.count())
        .select_from(Note)
        .where(Note.bookshelf_id == Bookshelf.id)
        .scalar_subquery()
        .label("note_count")
    )
    # Intentionally select one more than the limit to determine if there are
    # more results.
    statement = (
        select(Bookshelf, note_count_subquery)
        .where(Bookshelf.user_id == user.id)
        .limit(limit + 1)
    )

    # First sort by the `sort` parameter, then by the `id` column
    # (`id`: to achieve deterministic ordering).
    sort_order = (
        col(getattr(Bookshelf, sort)).desc()
        if order == "desc"
        else col(getattr(Bookshelf, sort)).asc()
    )
    id_order = col(Bookshelf.id).asc()
    statement = statement.order_by(sort_order, id_order)

    if cursor:
        # Decode the cursor and use it to skip the rows that have already been
        # returned.
        cursor_obj = BookshelfCursor.decode(cursor)
        sort_value = getattr(cursor_obj, sort)
        if sort_value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cursor: {cursor}",
            )

        # Example: sort = "title", order = "desc", sort_value = "B"
        #   - sort_eq = Bookshelf.title = "B"
        #   - id_gt = Bookshelf.id > bookshelf_cursor.id
        #   - sort_filter = Bookshelf.title < "B"
        #
        # The final statement will be:
        #   (Bookshelf.title = "B" AND Bookshelf.id > bookshelf_cursor.id)
        #   OR Bookshelf.title < "B"
        sort_eq = col(getattr(Bookshelf, sort)) == sort_value
        id_gt = col(Bookshelf.id) > cursor_obj.id
        sort_filter = (
            col(getattr(Bookshelf, sort)) < sort_value
            if order == "desc"
            else col(getattr(Bookshelf, sort)) > sort_value
        )
        statement = statement.where((sort_eq & id_gt) | sort_filter)

    result = await db.exec(statement)
    bookshelves = [
        BookshelfRead.model_validate(
            {
                **bookshelf.model_dump(),
                "count": count,
            }
        )
        for bookshelf, count in result
    ]

    next_cursor = None
    if len(bookshelves) > limit:
        last_bookshelf = bookshelves[-2]
        next_cursor = BookshelfCursor(
            id=last_bookshelf.id,
            title=last_bookshelf.title,
            created_at=last_bookshelf.created_at,
        ).encode()

    return GetBookshelvesResponse(
        data=bookshelves[:limit],
        next_cursor=next_cursor,
    )


class CreateBookshelfResponse(BaseModel):
    data: BookshelfRead


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_bookshelf(
    bookshelf_create: BookshelfCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> CreateBookshelfResponse:
    bookshelf = Bookshelf(title=bookshelf_create.title, user_id=user.id)
    db.add(bookshelf)
    await db.commit()
    await db.refresh(bookshelf)
    return CreateBookshelfResponse(data=BookshelfRead.model_validate(bookshelf))


class UpdateBookshelfResponse(BaseModel):
    data: BookshelfRead


@router.patch("/{bookshelf_id}")
async def update_bookshelf(
    bookshelf_id: UUID,
    bookshelf_update: BookshelfUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> UpdateBookshelfResponse:
    bookshelf = await db.get(Bookshelf, bookshelf_id)
    if bookshelf is None or bookshelf.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bookshelf {bookshelf_id} not found",
        )

    if bookshelf_update.title is not None:
        bookshelf.title = bookshelf_update.title

    await db.commit()
    await db.refresh(bookshelf)
    return UpdateBookshelfResponse(data=BookshelfRead.model_validate(bookshelf))


@router.delete("/{bookshelf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookshelf(
    bookshelf_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    bookshelf = await db.get(Bookshelf, bookshelf_id)
    if bookshelf is None or bookshelf.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bookshelf {bookshelf_id} not found",
        )

    await db.delete(bookshelf)
    await db.commit()
