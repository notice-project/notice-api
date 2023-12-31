from datetime import datetime
from typing import Annotated, Optional

from fastapi import Depends, Header
from sqlmodel import select

from notice_api.auth.schema import Session, User
from notice_api.db import AsyncSession, get_async_session


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    session_token: Annotated[Optional[str], Header(alias="X-Session-Token")] = None,
) -> Optional[User]:
    """Get the current user from the database.

    This function is used as a dependency for FastAPI endpoints. It will return
    the current user if the session token is valid and the session has not
    expired. Otherwise, it will return None.
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
        return None

    return data[1]
