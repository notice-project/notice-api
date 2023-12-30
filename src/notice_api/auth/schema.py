from __future__ import annotations

from datetime import date
from typing import Any, Callable, Optional

from pydantic import EmailStr
from sqlalchemy import Column, ForeignKey, types
from sqlmodel import Field, SQLModel


def RenamedField(
    column_name: str,
    sa_type: types.TypeEngine,
    foreign_key: Optional[str] = None,
    primary_key: bool = False,
    nullable: bool = True,
    default_factory: Optional[Callable[[], Any]] = None,
):
    args = [column_name, sa_type]
    if foreign_key is not None:
        args.append(ForeignKey(foreign_key))

    sa_column = Column(*args, primary_key=primary_key, nullable=nullable)
    return Field(default_factory=default_factory, sa_column=sa_column)


class User(SQLModel, table=True):
    """Represents a user of the application which may have one or more accounts."""

    __tablename__ = "user"  # pyright: ignore[reportGeneralTypeIssues]

    id: str = Field(primary_key=True, nullable=False)
    name: Optional[str] = None
    email: EmailStr = Field(sa_type=types.String(255), nullable=False)
    email_verified: date = RenamedField(
        default_factory=date.today,
        column_name="emailVerified",
        sa_type=types.Date(),
    )
    image: Optional[str] = None


class Account(SQLModel, table=True):
    """Represents an account of a user."""

    __tablename__ = "account"  # pyright: ignore[reportGeneralTypeIssues]

    user_id: str = RenamedField(
        column_name="userId",
        sa_type=types.String(255),
        nullable=False,
        foreign_key="user.id",
    )
    type: str
    provider: str = Field(primary_key=True)
    provider_account_id: str = RenamedField(
        column_name="providerAccountId",
        sa_type=types.String(255),
        primary_key=True,
    )
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    expires_at: Optional[int] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = Field(None, sa_type=types.String(2048))
    session_state: Optional[str] = None


class Session(SQLModel, table=True):
    """Represents an authenticated session of a user."""

    __tablename__ = "session"  # pyright: ignore[reportGeneralTypeIssues]

    session_token: str = RenamedField(
        column_name="sessionToken",
        sa_type=types.String(255),
        primary_key=True,
    )
    user_id: str = RenamedField(
        column_name="userId",
        sa_type=types.String(255),
        foreign_key="user.id",
        nullable=False,
    )
    expires: date


class VerificationToken(SQLModel, table=True):
    """Represents a verification token for a user."""

    __tablename__ = "verificationToken"  # pyright: ignore[reportGeneralTypeIssues]

    identifier: str = Field(primary_key=True)
    token: str = Field(primary_key=True)
    expires: date
