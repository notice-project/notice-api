from io import BytesIO

import structlog
from deepgram import Deepgram
from deepgram.transcription import LiveTranscriptionEvent
from fastapi import APIRouter, WebSocket
from fastapi.responses import HTMLResponse
from pydub import AudioSegment

from notice_api.core.config import settings

router = APIRouter()

AUDIO_DIRECTORY = "../audio_temp"  # Path for all audio file
TEMP_MIME_AUDIO_PATH = "../audio_temp/test_audio.bin"  # Path for temporary mime file
audio_file_name = "note_name"  # Name for saving current audio

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


@router.websocket("/transcription/{output_filename}")
async def handle_live_transcription(ws: WebSocket, output_filename: str):
    logger = structlog.get_logger("ws")
    await ws.accept()
    logger.info("Websocket connection established")

    with open(TEMP_MIME_AUDIO_PATH, "wb") as audio_file:
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

        def save_transcript(result: dict):
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
                logger.info("Stopping recording")
                # Convert mimetype to mp3 for playback
                mimetype_to_mp3(output_filename)
                break

            # Write temporary mime audio file to local
            audio_file.write(data["bytes"])

            deepgramLive.send(data["bytes"])

        await deepgramLive.finish()


def mimetype_to_mp3(output_filename: str):
    logger = structlog.get_logger()
    file_path = TEMP_MIME_AUDIO_PATH

    with open(file_path, "rb") as file:
        audio_bytes = file.read()

    audio_segment = AudioSegment.from_file(BytesIO(audio_bytes))

    output_path = f"{AUDIO_DIRECTORY}/{output_filename}"
    audio_segment.export(output_path, format="mp3")
    logger.info("Converted file into mp3")
