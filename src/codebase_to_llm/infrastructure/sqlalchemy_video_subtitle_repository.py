from __future__ import annotations

import logging
from typing_extensions import final
from sqlalchemy import Column, String, Table
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from codebase_to_llm.application.ports import VideoSubtitleRepositoryPort
from codebase_to_llm.domain.video_subtitle import (
    VideoSubtitle,
    VideoSubtitleId,
)
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.domain.stored_file import StoredFileId
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_video_subtitles_table = Table(
    "video_subtitles",
    get_metadata(),
    Column("id", String, primary_key=True),
    Column("video_file_id", String, nullable=False),
    Column("subtitle_file_id", String, nullable=False),
)


@final
class SqlAlchemyVideoSubtitleRepository(VideoSubtitleRepositoryPort):
    """Repository for associating videos with ASS subtitle files."""

    __slots__ = ()

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def add(self, association: VideoSubtitle) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _video_subtitles_table.insert().values(
                    id=association.id().value(),
                    video_file_id=association.video_file_id().value(),
                    subtitle_file_id=association.subtitle_file_id().value(),
                )
            )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))

    def get(self, association_id: VideoSubtitleId) -> Result[VideoSubtitle, str]:
        session = self._session()
        try:
            row = session.execute(
                _video_subtitles_table.select().where(
                    _video_subtitles_table.c.id == association_id.value()
                )
            ).fetchone()
            if row is None:
                return Err("Association not found")
            vid_res = StoredFileId.try_create(row.video_file_id)
            if vid_res.is_err():
                return Err("Invalid video file id in database")
            sub_res = StoredFileId.try_create(row.subtitle_file_id)
            if sub_res.is_err():
                return Err("Invalid subtitle file id in database")
            vid_id = vid_res.ok()
            sub_id = sub_res.ok()
            assert vid_id is not None and sub_id is not None
            assoc_res = VideoSubtitle.try_create(row.id, vid_id, sub_id)
            if assoc_res.is_err():
                return Err(assoc_res.err() or "Invalid association data")
            assoc = assoc_res.ok()
            assert assoc is not None
            return Ok(assoc)
        except SQLAlchemyError as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))

    def update(self, association: VideoSubtitle) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _video_subtitles_table.update()
                .where(_video_subtitles_table.c.id == association.id().value())
                .values(subtitle_file_id=association.subtitle_file_id().value())
            )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))

    def remove(self, association_id: VideoSubtitleId) -> Result[None, str]:
        session = self._session()
        try:
            session.execute(
                _video_subtitles_table.delete().where(
                    _video_subtitles_table.c.id == association_id.value()
                )
            )
            session.commit()
            return Ok(None)
        except SQLAlchemyError as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
