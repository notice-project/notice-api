import importlib.metadata

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

import notice_api.utils.logging.core as logging_core
import notice_api.utils.logging.middlewares as logging_middlewares
from notice_api.auth.routes import router as auth_router
from notice_api.core.config import settings
from notice_api.transcript.routes import router as transcribe_router

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


app.include_router(auth_router)

app.include_router(transcribe_router)
