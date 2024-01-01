import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Field, SQLModel


# Define Transcript model for the transcript table
class Transcript(SQLModel, table=True):
    __tablename__ = "transcript"

    id: Optional[int] = Field(default=None, primary_key=True)
    note_id: UUID = Field(primary_key=True, foreign_key="note.id", index=True)
    timestamp: datetime.timedelta = Field()
    text: str
