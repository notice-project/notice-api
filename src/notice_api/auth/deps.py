from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import select

from notice_api.auth.schema import Session, User
from notice_api.db import AsyncSession, get_async_session


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    session_token: Annotated[str, Header(alias="X-Session-Token")],
) -> User:
    """Get the current user from the database.

    This function is used as a dependency for FastAPI endpoints. It will return
    the current user if the session token is valid and the session has not
    expired. Otherwise, it will raise an HTTPException with status code 401.
    """

    statement = (
        select(Session, User)
        .join(User)
        .where(Session.session_token == session_token)
        .where(Session.expires > datetime.utcnow())
    )
    result = await db.exec(statement)
    data = result.first()
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not logged in.",
        )

    return data[1]
