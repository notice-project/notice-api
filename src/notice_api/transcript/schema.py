import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Field, SQLModel


# Define Transcript model for the transcript table
class Transcript(SQLModel, table=True):
    __tablename__ = "transcript"

    id: Optional[UUID] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={"default": func.uuid()},
    )
    user_id: UUID = Field(foreign_key="user.id", index=True)
    note_id: UUID = Field(foreign_key="note.id", index=True)
    line_order: int
    timestamp: datetime.timedelta = Field()
    text: str
