from datetime import timedelta
from typing import Annotated, Generator, Protocol
from uuid import UUID

import structlog
from deepgram.transcription import LiveTranscriptionResponse
from fastapi import Depends

from notice_api.db import AsyncSession, get_async_session
from notice_api.notes.routes import get_notes
from notice_api.notes.schema import Note
from notice_api.transcript.schema import Transcript


class TranscriptResultSaver(Protocol):
    async def save_transcript(self, result: LiveTranscriptionResponse):
        ...


class InMemoryTranscriptResultSaver:
    def __init__(self, db: AsyncSession, note_id: UUID):
        self.db: AsyncSession = db
        self.note_id: UUID = note_id

    async def save_transcript(
        self,
        result: LiveTranscriptionResponse,
    ):
        logger = structlog.get_logger("result_saver")
        transcript: str = result["channel"]["alternatives"][0]["transcript"]
        start_time = result["start"]
        timestamp = timedelta(seconds=start_time)

        if len(transcript) <= 0:
            return

        new_transcript = Transcript(
            note_id=self.note_id,
            text=transcript,
            timestamp=timestamp,
        )

        try:
            self.db.add(new_transcript)
            await self.db.commit()
            await self.db.refresh(new_transcript)
            logger.info("Transcript saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save transcript. Error: {e}")


def get_transcript_result_saver(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    note: Annotated[Note, Depends(get_notes)],
) -> Generator[TranscriptResultSaver, None, None]:
    logger = structlog.get_logger("result_saver")
    saver = InMemoryTranscriptResultSaver(db=db, note_id=note.id) # type: ignore
    yield saver
    logger.info(
        "Transcript saved",
    )
