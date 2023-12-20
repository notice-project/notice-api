import structlog
from deepgram import Deepgram
from deepgram.transcription import LiveTranscriptionEvent
from fastapi import APIRouter, WebSocket

from notice_api.core.config import settings

router = APIRouter()


@router.websocket("/transcription")
async def handle_live_transcription(ws: WebSocket):
    logger = structlog.get_logger("ws")
    await ws.accept()
    logger.info("Websocket connection established")

    deepgram = Deepgram(settings.DEEPGRAM_SECRET_KEY)
    try:
        deepgramLive = await deepgram.transcription.live(
            {"smart_format": True, "model": "nova-2", "language": "en-US"}
        )
    except Exception as e:
        logger.debug(f"Could not open socket: {e}")
        return

    saved_transcripts = []
    saved_timestamps = []

    def save_transcript(result):
        transcript = result["channel"]["alternatives"][0]["transcript"]
        timestamp = result["start"]
        logger.info(transcript)
        if len(transcript) > 0:
            saved_transcripts.append(transcript)
            saved_timestamps.append(timestamp)

    deepgramLive.registerHandler(
        LiveTranscriptionEvent.CLOSE, lambda _: print("Connection closed.")
    )
    deepgramLive.registerHandler(
        LiveTranscriptionEvent.TRANSCRIPT_RECEIVED, save_transcript
    )

    while True:
        data = await ws.receive()
        logger.info("Received data")

        if data.get("text") == "stop":
            logger.info("Ready to stop")
            break

        deepgramLive.send(data["bytes"])

    await deepgramLive.finish()
