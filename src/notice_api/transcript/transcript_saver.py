from datetime import timedelta
from typing import Annotated, Generator, Protocol

import structlog
from deepgram.transcription import LiveTranscriptionResponse
from fastapi import Depends

from notice_api.auth.deps import get_current_user
from notice_api.auth.schema import User
from notice_api.db import AsyncSession, get_async_session
from notice_api.notes.routes import get_notes
from notice_api.notes.schema import Note
from notice_api.transcript.schema import Transcript


class TranscriptResultSaver(Protocol):
    async def save_transcript(self, result: LiveTranscriptionResponse):
        ...


class InMemoryTranscriptResultSaver:
    def __init__(self, db: AsyncSession, user: User, note: Note):
        self.db: AsyncSession = db
        self.user: User = user
        self.note: Note = note
        self.transcripts: list[str] = []
        self.timestamps: list[float] = []
        self.index: int = 0

    async def save_transcript(
        self,
        result: LiveTranscriptionResponse,
    ):
        logger = structlog.get_logger("result_saver")
        transcript = result["channel"]["alternatives"][0]["transcript"]
        start_time = result["start"]
        timestamp = timedelta(seconds=start_time)

        if len(transcript) <= 0:
            return

        self.transcripts.append(transcript)
        self.timestamps.append(start_time)

        new_transcript = Transcript(
            user_id=self.user.id,
            note_id=self.note.id,
            line_order=self.index,
            text=transcript,
            timestamp=timestamp,
        )

        try:
            self.db.add(new_transcript)
            await self.db.commit()
            await self.db.refresh(new_transcript)
            self.index += 1
            logger.info("Transcript saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save transcript. Error: {e}")


def get_transcript_result_saver(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user: Annotated[User, Depends(get_current_user)],
    note: Annotated[Note, Depends(get_notes)],
) -> Generator[TranscriptResultSaver, None, None]:
    logger = structlog.get_logger("result_saver")
    saver = InMemoryTranscriptResultSaver(db=db, user=user, note=note)
    yield saver
    logger.info(
        "Transcript saved",
        transcripts=saver.transcripts,
        timestamps=saver.timestamps,
    )
