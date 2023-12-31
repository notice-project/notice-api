from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import Column, ForeignKey, func, types
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Represents a user of the application which may have one or more accounts."""

    __tablename__ = "user"  # pyright: ignore[reportGeneralTypeIssues]

    id: str = Field(primary_key=True, nullable=False)
    name: Optional[str] = None
    email: EmailStr = Field(sa_type=types.String(255), nullable=False)
    email_verified: datetime = Field(
        sa_column=Column(
            "emailVerified", types.TIMESTAMP, server_default=func.current_timestamp()
        ),
    )
    image: Optional[str] = None


class Account(SQLModel, table=True):
    """Represents an account of a user."""

    __tablename__ = "account"  # pyright: ignore[reportGeneralTypeIssues]

    user_id: str = Field(
        sa_column=Column(
            "userId",
            types.String(255),
            ForeignKey("user.id"),
            index=True,
            nullable=False,
        ),
    )
    type: str
    provider: str = Field(primary_key=True)
    provider_account_id: str = Field(
        sa_column=Column("providerAccountId", types.String(255), primary_key=True),
    )
    refresh_token: Optional[str] = Field(None, sa_type=types.Text())
    access_token: Optional[str] = Field(None, sa_type=types.Text())
    expires_at: Optional[int] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = Field(None, sa_type=types.Text())
    session_state: Optional[str] = None


class Session(SQLModel, table=True):
    """Represents an authenticated session of a user."""

    __tablename__ = "session"  # pyright: ignore[reportGeneralTypeIssues]

    session_token: str = Field(
        sa_column=Column("sessionToken", types.String(255), primary_key=True),
    )
    user_id: str = Field(
        sa_column=Column(
            "userId",
            types.String(255),
            ForeignKey("user.id"),
            index=True,
            nullable=False,
        ),
    )
    expires: datetime = Field(sa_type=types.TIMESTAMP)


class VerificationToken(SQLModel, table=True):
    """Represents a verification token for a user."""

    __tablename__ = "verificationToken"  # pyright: ignore[reportGeneralTypeIssues]

    identifier: str = Field(primary_key=True)
    token: str = Field(primary_key=True)
    expires: datetime = Field(sa_type=types.TIMESTAMP)
