import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class TranscriptBase(SQLModel):
    """Base model for a transcript."""

    title: str


# Define Transcript model for the transcript table
class Transcript(TranscriptBase, table=True):
    __tablename__ = "transcript"

    id: Optional[int] = Field(default=None, primary_key=True)
    note_id: UUID = Field(primary_key=True, foreign_key="note.id", index=True)
    timestamp: datetime.timedelta = Field()
    text: str
