import os

import structlog
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from notice_api.transcript.routes import AUDIO_DIRECTORY

router = APIRouter()


@router.get("/audio")
async def get_audio(filename: str = Query(..., description="Name of the audio file")):
    logger = structlog.get_logger()
    directory_path = AUDIO_DIRECTORY
    audio_file_path = os.path.join(directory_path, f"{filename}.mp3")

    logger.info(f"Retrieved audio file: {filename}")
    return FileResponse(path=audio_file_path, media_type="audio/mpeg")
