from typing import Annotated

import structlog
from fastapi import APIRouter, Path
from fastapi.responses import FileResponse

from notice_api.transcript import audio_saver

router = APIRouter(tags=["audio"])


@router.get("/audio/{filename:path}")
async def get_audio(
    filename: Annotated[str, Path(description="The filename of the audio file")],
) -> FileResponse:
    logger = structlog.get_logger()
    audio_file_path = audio_saver.get_path_for(filename)

    logger.info(f"Retrieved audio file: {filename}")
    return FileResponse(path=audio_file_path, media_type="audio/mpeg")
