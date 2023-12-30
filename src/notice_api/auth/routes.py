from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from notice_api.auth.db import get_async_session
from notice_api.auth.schema import Session, User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/users/me")
async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    session_token: Annotated[Optional[str], Header(alias="X-Session-Token")] = None,
) -> Optional[User]:
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
