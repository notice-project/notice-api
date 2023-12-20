import structlog
from deepgram import Deepgram
from deepgram.transcription import LiveTranscriptionEvent
from fastapi import APIRouter, WebSocket
from fastapi.responses import HTMLResponse

from notice_api.core.config import settings

router = APIRouter()


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


@router.get("/transcription")
def live_transcription_page():
    return HTMLResponse(html)


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
        logger.debug("Could not open socket", error=e)
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
