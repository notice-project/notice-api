from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Field, SQLModel


class Bookshelf(BookshelfBase, table=True):
    """A bookshelf for the associated user."""

    __tablename__ = "bookshelf"  # pyright: ignore[reportGeneralTypeIssues]

    id: Optional[UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={"default": func.uuid()},
    )
    created_at: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": func.now()}
    )
    user_id: str = Field(foreign_key="user.id", index=True)
