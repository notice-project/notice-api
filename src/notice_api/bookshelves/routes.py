from base64 import b64decode, b64encode
from datetime import datetime
from typing import Annotated, Literal, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import and_, col, or_, select

from notice_api.auth.deps import get_current_user
from notice_api.auth.schema import User
from notice_api.bookshelves.schema import (
    Bookshelf,
    BookshelfCreate,
    BookshelfRead,
    BookshelfUpdate,
)
from notice_api.db import AsyncSession, get_async_session

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
    data: Sequence[BookshelfRead]
    next_cursor: Optional[str] = None


@router.get("/")
async def get_bookshelves(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    cursor: Optional[str] = None,
    limit: int = 10,
    order: Literal["asc", "desc"] = "desc",
    sort: Literal["title", "created_at"] = "created_at",
) -> GetBookshelvesResponse:
    statement = select(Bookshelf).where(Bookshelf.user_id == user.id).limit(limit)

    # First sort by the `sort` parameter, then by the `id` column
    # (`id`: to achieve deterministic ordering).
    primary_order = (
        col(getattr(Bookshelf, sort)).desc()
        if order == "desc"
        else col(getattr(Bookshelf, sort)).asc()
    )
    secondary_order = col(Bookshelf.id).asc()
    statement = statement.order_by(primary_order, secondary_order)

    if cursor:
        # Decode the cursor and use it to skip the rows that have already been
        # returned.
        bookshelf_cursor = BookshelfCursor.decode(cursor)
        if sort == "title" and bookshelf_cursor.title is not None:
            sort_value = bookshelf_cursor.title
        elif sort == "created_at" and bookshelf_cursor.created_at is not None:
            sort_value = bookshelf_cursor.created_at
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor",
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
        id_gt = col(Bookshelf.id) > bookshelf_cursor.id
        sort_filter = (
            col(getattr(Bookshelf, sort)) < sort_value
            if order == "desc"
            else col(getattr(Bookshelf, sort)) > sort_value
        )
        statement = statement.where(or_(and_(sort_eq, id_gt), sort_filter))

    result = await db.exec(statement)
    bookshelves = [BookshelfRead.model_validate(bookshelf) for bookshelf in result]

    next_cursor = None
    if len(bookshelves) == limit:
        last_bookshelf = bookshelves[-1]
        next_cursor = BookshelfCursor(
            id=last_bookshelf.id,
            title=last_bookshelf.title,
            created_at=last_bookshelf.created_at,
        ).encode()

    return GetBookshelvesResponse(
        data=bookshelves,
        next_cursor=next_cursor,
    )


class CreateBookshelfResponse(BaseModel):
    data: BookshelfRead


@router.post(
    "/",
    response_model=CreateBookshelfResponse,
    status_code=status.HTTP_201_CREATED,
)
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
    if not bookshelf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookshelf not found",
        )
    if bookshelf.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
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
    if not bookshelf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookshelf not found",
        )
    if bookshelf.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    await db.delete(bookshelf)
    await db.commit()
