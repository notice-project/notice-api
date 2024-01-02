import json
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import Depends

from notice_api.db import AsyncSession, get_async_session
from notice_api.notes.note_content import NoteContent


class NoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_note_content(self, note_id: UUID) -> list[NoteContent]:
        conn = await self.db.connection()

        statement = "SELECT `content` ->> '$.children' FROM note WHERE id = %s"
        parameters = (note_id.hex,)

        result = await conn.exec_driver_sql(statement, parameters)
        for (row,) in result:
            return json.loads(row)

        return []

    async def get_note_content_partial(self, note_id: UUID, index: int) -> NoteContent:
        logger = structlog.get_logger("get_note_content_partial")
        conn = await self.db.connection()

        statement = "SELECT `content` ->> '$.children[%s]' FROM note WHERE id = %s"
        parameters = (index, note_id.hex)

        result = await conn.exec_driver_sql(statement, parameters)
        for (row,) in result:
            logger.info("Note content fetched", note_id=note_id, content=row)
            return json.loads(row)

        return {}  # pyright: ignore[reportGeneralTypeIssues]

    async def update_note_content(
        self,
        note_id: UUID,
        content: list[NoteContent],
    ):
        content_json = json.dumps(content)
        conn = await self.db.connection()
        await conn.exec_driver_sql(
            """
            UPDATE
                note
            SET
                `content` = JSON_SET(`content`, '$.children', CAST(%s AS JSON))
            WHERE
                id = %s
            """,
            (content_json, note_id.hex),
        )
        await self.db.commit()

    async def update_note_content_partial(
        self,
        note_id: UUID,
        index: int,
        content: NoteContent,
    ):
        content_json = json.dumps(content)
        conn = await self.db.connection()
        await conn.exec_driver_sql(
            """
            UPDATE
                note
            SET
                `content` = JSON_SET(`content`, '$.children[%s]', CAST(%s AS JSON))
            WHERE
                id = %s
            """,
            (index, content_json, note_id.hex),
        )
        await self.db.commit()

    async def insert_note_content(
        self,
        note_id: UUID,
        index: int,
        content: NoteContent,
    ):
        content_json = json.dumps(content)
        conn = await self.db.connection()
        await conn.exec_driver_sql(
            """
            UPDATE
                note
            SET
                `content` = JSON_SET(
                    `content`,
                    '$.children',
                    JSON_MERGE(
                        COALESCE(`content`->>'$.children[0 to %s]', JSON_ARRAY()),
                        CAST(%s AS JSON),
                        COALESCE(`content`->>'$.children[%s to last]', JSON_ARRAY())
                    )
                )
            WHERE
                id = %s
            """,
            (index - 1, content_json, index, note_id.hex),
        )
        await self.db.commit()

    async def update_note_title(
        self,
        note_id: UUID,
        title: str,
    ) -> None:
        conn = await self.db.connection()
        await conn.exec_driver_sql(
            """
            UPDATE
                note
            SET
                `title` = %s
            WHERE
                id = %s
            """,
            (title, note_id.hex),
        )
        await self.db.commit()

    async def get_note_transcriptions(
        self, note_id: UUID, last_n: int = 140
    ) -> list[str]:
        conn = await self.db.connection()

        result = await conn.exec_driver_sql(
            """
            SELECT
                text
            FROM (
                SELECT * FROM transcript
                WHERE note_id = %s
                ORDER BY id DESC
                LIMIT %s
            ) AS sub
            ORDER BY id ASC
            """,
            (note_id.hex, last_n),
        )
        return [text for (text,) in result]


def get_note_repository(
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> NoteRepository:
    return NoteRepository(db=db)
