from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Generator
from uuid import uuid4

import structlog
from pydub import AudioSegment

# Path for all audio file
AUDIO_DIRECTORY = Path(__file__).parent.parent / "audio_temp"
# Path for temporary mime file
TEMP_MIME_AUDIO_PATH = AUDIO_DIRECTORY / "test_audio.bin"
# Name for saving current audio
audio_file_name = "note_name"


def get_path_for(filename: str) -> Path:
    return (AUDIO_DIRECTORY / filename).with_suffix(".mp3")


def mimetype_to_mp3(output_filename: str):
    logger = structlog.get_logger()

    audio_bytes = TEMP_MIME_AUDIO_PATH.read_bytes()
    audio_segment = AudioSegment.from_file(BytesIO(audio_bytes))

    output_path = get_path_for(output_filename)
    audio_segment.export(output_path, format="mp3")
    logger.info("Converted file into mp3")


class AudioSaver(BinaryIO):
    def __init__(self, filename: str):
        self.temp_path = AUDIO_DIRECTORY / uuid4().hex
        self.temp_path.parent.mkdir(parents=True, exist_ok=True)

        self.filename = get_path_for(filename)

        self.writer = self.temp_path.open("wb")

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.close()

    def write(self, data: bytes):
        self.writer.write(data)

    def close(self):
        self.writer.close()

        # Convert the audio to mp3 for playback
        audio_segment = AudioSegment.from_file(self.temp_path)
        audio_segment.export(self.filename, format="mp3")

        self.temp_path.unlink()


def get_audio_saver(filename: str) -> Generator[AudioSaver, None, None]:
    """Get a file-like object to save audio to.

    This function can be used as a FastAPI dependency to get a file-like object
    to save audio to. The file will be deleted when the request is finished.
    """

    with AudioSaver(filename) as saver:
        yield saver
