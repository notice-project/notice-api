from typing import Generator, Protocol

import structlog
from deepgram.transcription import LiveTranscriptionResponse


class TranscriptResultSaver(Protocol):
    async def save_transcript(self, result: LiveTranscriptionResponse):
        ...


class InMemoryTranscriptResultSaver:
    def __init__(self):
        self.transcripts: list[str] = []
        self.timestamps: list[float] = []

    async def save_transcript(self, result: LiveTranscriptionResponse):
        transcript = result["channel"]["alternatives"][0]["transcript"]
        if len(transcript) <= 0:
            return
        self.transcripts.append(transcript)
        self.timestamps.append(result["start"])


def get_transcript_result_saver() -> Generator[TranscriptResultSaver, None, None]:
    logger = structlog.get_logger("result_saver")
    saver = InMemoryTranscriptResultSaver()
    yield saver
    logger.info(
        "Transcript saved",
        transcripts=saver.transcripts,
        timestamps=saver.timestamps,
    )
