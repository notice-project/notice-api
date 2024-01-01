from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated, AsyncGenerator, Protocol, cast
from uuid import UUID

import structlog
from deepgram import Deepgram
from deepgram.transcription import (
    LiveTranscription,
    LiveTranscriptionEvent,
    LiveTranscriptionResponse,
)
from fastapi import Depends

from notice_api.core.config import settings
from notice_api.db import AsyncSession, get_async_session
from notice_api.notes.routes import get_notes
from notice_api.notes.schema import Note
from notice_api.transcript.schema import Transcript


class TranscriptResultSaver(Protocol):
    async def save_transcript(self, result: LiveTranscriptionResponse):
        ...


class DatabaseTranscriptResultSaver:
    def __init__(self, db: AsyncSession, note_id: UUID):
        self.db = db
        self.note_id = note_id

    async def save_transcript(self, result: LiveTranscriptionResponse):
        logger = structlog.get_logger("result_saver")
        transcript = result["channel"]["alternatives"][0]["transcript"]
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
) -> TranscriptResultSaver:
    return DatabaseTranscriptResultSaver(db=db, note_id=cast(UUID, note.id))


@asynccontextmanager
async def get_live_transciber(
    result_saver: Annotated[
        TranscriptResultSaver, Depends(get_transcript_result_saver)
    ],
) -> AsyncGenerator[LiveTranscription, None]:
    """Get a live transcription connection to Deepgram.

    This function can be used as a FastAPI dependency to get a live transcription
    connection to Deepgram. The connection will be closed when the request is
    finished.

    Args:
        result_saver: The result saver to use to save transcripts.
    """

    logger = structlog.get_logger("live_transcription")

    deepgram = Deepgram(settings.DEEPGRAM_SECRET_KEY)
    deepgram_live = await deepgram.transcription.live(
        {"smart_format": True, "model": "nova-2", "language": "en-US"}
    )

    deepgram_live.registerHandler(
        LiveTranscriptionEvent.CLOSE,
        lambda _: logger.info("Connection closed."),
    )
    deepgram_live.registerHandler(
        LiveTranscriptionEvent.TRANSCRIPT_RECEIVED,
        result_saver.save_transcript,
    )

    yield deepgram_live

    logger.info("Closing connection")
    await deepgram_live.finish()
