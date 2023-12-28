import os

import structlog
from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse

from notice_api.transcript.routes import AUDIO_DIRECTORY

router = APIRouter()


@router.get("/audio")
async def get_audio(filename: str = Query(..., description="Name of the audio file")):
    logger = structlog.get_logger()
    directory_path = AUDIO_DIRECTORY
    audio_file_path = os.path.join(directory_path, f"{filename}.mp3")

    try:
        with open(audio_file_path, "rb") as audio_file:
            audio_data = audio_file.read()
    except FileNotFoundError:
        logger.error(f"Audio file '{filename}' not found")
        error_message = {"detail": f"Audio file '{filename}' not found"}
        return JSONResponse(status_code=404, content=error_message)

    logger.info(f"Retrieved audio file: {filename}")
    return Response(content=audio_data, media_type="audio/mpeg")
