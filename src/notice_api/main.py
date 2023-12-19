import importlib.metadata

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from deepgram import Deepgram
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

import notice_api.utils.logging.core as logging_core
import notice_api.utils.logging.middlewares as logging_middlewares
from notice_api.auth.routes import router as auth_router
from notice_api.core.config import settings


logging_core.setup_logging(
    json_logs=settings.LOG_JSON_FORMAT,
    log_level=settings.LOG_LEVEL,
)

app = FastAPI(
    title="Not!ce API",
    description=importlib.metadata.metadata(__package__)["Summary"],
    version=importlib.metadata.version(__package__),
)

logging_middlewares.install_logging_middleware(app)
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    message: str = "Server is running 🎉"


@app.get("/")
def health_check() -> HealthCheckResponse:
    """Check if the server is running."""

    return HealthCheckResponse()


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
            var ws = new WebSocket("ws://localhost:8000/transcription");
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


@app.get("/transcription")
def live_transcription_page():
    return HTMLResponse(html)


@app.websocket("/transcription")
async def live_transcription(ws: WebSocket):
    """WebSocket endpoint for live audio transcription.

    - saved_transcripts: a list of str, 逐字稿, 每個約4秒片段
    - saved_timestamps: 對應的timestamp
    - _data: websocket data from frontend
    """
    logger = structlog.get_logger("ws")
    await ws.accept()
    logger.info("Websocket connection established")

    # Initializes the Deepgram SDK
    deepgram = Deepgram(settings.DEEPGRAM_SECRET_KEY)
    try:
        deepgramLive = await deepgram.transcription.live({
            "smart_format": True,
            "model": "nova-2",
            "language": "en-US"
        })
    except Exception as e:
        logger.debug(f'Could not open socket: {e}')
        return

    saved_transcripts = []
    saved_timestamps = []

    def save_transcript(result):
        transcript = result['channel']['alternatives'][0]['transcript']
        timestamp = result['start']
        if len(transcript) > 0:
            saved_transcripts.append(transcript)
            saved_timestamps.append(timestamp)

    # Listen for the connection to close
    deepgramLive.registerHandler(deepgramLive.event.CLOSE, lambda _: print('Connection closed.'))
    # Listen for any transcripts received from Deepgram and write them to the console
    deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, save_transcript)

    while True:
        _data = await ws.receive()
        logger.info("Received data")

        if _data.get('text') == 'stop':
            logger.info("Ready to stop")
            break

        # Send audio data to Deepgram
        deepgramLive.send(_data['bytes'])

    # Finished sending data to Deepgram
    await deepgramLive.finish()


app.include_router(auth_router)
