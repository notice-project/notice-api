import json
from typing import Annotated
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, WebSocket, status

from notice_api.auth.deps import get_current_user
from notice_api.db import AsyncSession, get_async_session
from notice_api.notes.deps import get_current_note
from notice_api.transcript.audio_saver import (
    AudioSaver,
)
from notice_api.transcript.transcript_saver import (
    get_live_transciber,
    get_transcript_result_saver,
)

router = APIRouter(tags=["transcription"])


@router.websocket("/bookshelves/{bookshelf_id}/notes/{note_id}/transcription/ws")
async def handle_live_transcription(
    ws: WebSocket,
    bookshelf_id: UUID,
    note_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
):
    logger = structlog.get_logger("live_transcription.route")
    await ws.accept()

    message = await ws.receive_json()
    match message:
        case {"type": "init", "payload": session_token}:
            logger.info("Received init message", session_token=session_token)
            user = await get_current_user(db, session_token=session_token)
        case _:
            await ws.close(code=status.WS_1003_UNSUPPORTED_DATA)
            return

    note = await get_current_note(
        bookshelf_id=bookshelf_id,
        note_id=note_id,
        user=user,
        db=db,
    )

    transcript_saver = get_transcript_result_saver(db, note)
    async with get_live_transciber(transcript_saver) as deepgram_live:
        audio_saver: AudioSaver | None = None
        while True:
            message = await ws.receive()
            if (b := message.get("bytes")) is not None:
                logger.info("Received audio bytes", length=len(b))
                if audio_saver is not None:
                    audio_saver.write(b)
                deepgram_live.send(b)
                logger.info("Sent audio bytes to deepgram")
                continue

            match json.loads(message["text"]):
                case {"type": "start"}:
                    filename = str(uuid4())
                    logger.info("Received start message", filename=filename)
                    conn = await db.connection()
                    await conn.exec_driver_sql(
                        "UPDATE note SET transcript_audio_filename = %s WHERE id = %s",
                        (filename, note_id),
                    )
                    audio_saver = AudioSaver(filename=filename)
                case {"type": "stop"}:
                    logger.info("Received stop message")
                    return
