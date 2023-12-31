import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


# Define Transcript model for the transcript table
class Transcript(SQLModel, table=True):
    __tablename__ = "transcript"  # pyright: ignore[reportGeneralTypeIssues]

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={"autoincrement": True},
    )
    note_id: Optional[UUID] = Field(primary_key=True, foreign_key="note.id", index=True)
    timestamp: datetime.timedelta = Field()
    text: str
