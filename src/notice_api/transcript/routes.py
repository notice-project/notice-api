from typing import Annotated, AsyncGenerator

import structlog
from deepgram import Deepgram
from deepgram.transcription import LiveTranscription, LiveTranscriptionEvent
from fastapi import APIRouter, Depends, WebSocket
from fastapi.responses import HTMLResponse

from notice_api.core.config import settings
from notice_api.transcript.audio_saver import (
    AudioSaver,
    audio_file_name,
    get_audio_saver,
)
from notice_api.transcript.transcript_saver import (
    TranscriptResultSaver,
    get_transcript_result_saver,
)

router = APIRouter(tags=["transcription"])

MEDIA_RECORDER_INTERVAL = 1000
html = f"""
<!DOCTYPE html>
<html>
    <head>
        <title>Live Transcription</title>
    </head>
    <body>
        <h1>Live Transcription Test</h1>
        <button id="record-btn">Start Recording</button>
        <p id="transcript"></p>
        <script>
            var recordBtn = document.querySelector('#record-btn');
            var isRecording = false;
            var ws = new WebSocket('ws://localhost:8000/transcription/{audio_file_name}.mp3');
            var mediaRecorder;
            navigator.mediaDevices
                .getUserMedia({{ audio: true }})
                .then(stream => {{
                    console.log(stream);
                    mediaRecorder = new MediaRecorder(stream);
                    console.log(mediaRecorder)
                    mediaRecorder.ondataavailable = (e) => {{
                        console.log(e);
                        ws.send(e.data);
                    }}
                }});
            recordBtn.addEventListener('click', () => {{
                console.log('clicked');
                if (isRecording) {{
                    recordBtn.innerHTML = 'Start Recording';
                    mediaRecorder.stop();
                    isRecording = false;
                    ws.send('stop');
                }} else {{
                    recordBtn.innerHTML = 'Recording...';
                    mediaRecorder.start({MEDIA_RECORDER_INTERVAL});
                    isRecording = true;
                }}
            }});
            ws.onmessage = function(event) {{
                console.log(event);
                var transcript = document.getElementById('transcript');
                transcript.innerHTML += event.data;
            }};
        </script>
    </body>
</html>
"""


@router.get("/transcription")
def live_transcription_page():
    return HTMLResponse(html)


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


@router.websocket("/transcription/{filename}")
async def handle_live_transcription(
    ws: WebSocket,
    temp_audio_writer: Annotated[AudioSaver, Depends(get_audio_saver)],
    deepgram_live: Annotated[LiveTranscription, Depends(get_live_transciber)],
):
    logger = structlog.get_logger("ws")
    await ws.accept()
    logger.info("Websocket connection established")

    while True:
        message = await ws.receive()
        logger.info("Received data")

        match message:
            case {"text": "stop"}:
                logger.info("Stopping recording")
                return
            case {"bytes": b}:
                temp_audio_writer.write(b)
                deepgram_live.send(b)
