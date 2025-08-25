from __future__ import annotations
import logging
import json

from typing_extensions import final
from sqlalchemy import Column, String, Text, DateTime, Table
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from codebase_to_llm.application.ports import VideoSummaryRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.video_summary import (
    VideoSummary,
    VideoSummaryId,
    SummarySegment,
)
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_video_summaries_table = Table(
    "video_summaries",
    get_metadata(),
    Column("id", String, primary_key=True),
    Column("owner_id", String, nullable=False),
    Column("title", String, nullable=False),
    Column("segments_json", Text, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)


@final
class SqlAlchemyVideoSummaryRepository(VideoSummaryRepositoryPort):
    """VideoSummary repository backed by SQLAlchemy."""

    __slots__ = ()

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def _serialize_segments(self, segments: list[SummarySegment]) -> str:
        """Serialize summary segments to JSON string."""
        segments_data = []
        for segment in segments:
            segments_data.append(
                {
                    "content": segment.content().value(),
                    "video_url": segment.video_url().value(),
                    "begin_timestamp": {
                        "hour": segment.begin_timestamp().hour(),
                        "minute": segment.begin_timestamp().minute(),
                        "second": segment.begin_timestamp().second(),
                    },
                    "end_timestamp": {
                        "hour": segment.end_timestamp().hour(),
                        "minute": segment.end_timestamp().minute(),
                        "second": segment.end_timestamp().second(),
                    },
                }
            )
        return json.dumps(segments_data)

    def _deserialize_segments(self, json_str: str) -> Result[list[SummarySegment], str]:
        """Deserialize summary segments from JSON string."""
        try:
            segments_data = json.loads(json_str)
            segments: list[SummarySegment] = []

            for segment_data in segments_data:
                begin_ts = segment_data.get("begin_timestamp", {})
                end_ts = segment_data.get("end_timestamp", {})

                # Handle both old string format and new dict format for backward compatibility
                if isinstance(begin_ts, str):
                    # Parse old format "HH:MM:SS" or "MM:SS"
                    begin_parts = begin_ts.split(":")
                    if len(begin_parts) == 2:
                        begin_hour, begin_minute, begin_second = (
                            0,
                            int(begin_parts[0]),
                            int(begin_parts[1]),
                        )
                    elif len(begin_parts) == 3:
                        begin_hour, begin_minute, begin_second = (
                            int(begin_parts[0]),
                            int(begin_parts[1]),
                            int(begin_parts[2]),
                        )
                    else:
                        return Err(f"Invalid begin timestamp format: {begin_ts}")
                else:
                    begin_hour = begin_ts.get("hour", 0)
                    begin_minute = begin_ts.get("minute", 0)
                    begin_second = begin_ts.get("second", 0)

                if isinstance(end_ts, str):
                    # Parse old format "HH:MM:SS" or "MM:SS"
                    end_parts = end_ts.split(":")
                    if len(end_parts) == 2:
                        end_hour, end_minute, end_second = (
                            0,
                            int(end_parts[0]),
                            int(end_parts[1]),
                        )
                    elif len(end_parts) == 3:
                        end_hour, end_minute, end_second = (
                            int(end_parts[0]),
                            int(end_parts[1]),
                            int(end_parts[2]),
                        )
                    else:
                        return Err(f"Invalid end timestamp format: {end_ts}")
                else:
                    end_hour = end_ts.get("hour", 0)
                    end_minute = end_ts.get("minute", 0)
                    end_second = end_ts.get("second", 0)

                segment_result = SummarySegment.try_create(
                    content=segment_data.get("content", ""),
                    video_url=segment_data.get("video_url", ""),
                    begin_hour=begin_hour,
                    begin_minute=begin_minute,
                    begin_second=begin_second,
                    end_hour=end_hour,
                    end_minute=end_minute,
                    end_second=end_second,
                )
                if segment_result.is_err():
                    return Err(f"Invalid summary segment data: {segment_result.err()}")

                segment = segment_result.ok()
                assert segment is not None
                segments.append(segment)

            return Ok(segments)
        except json.JSONDecodeError as exc:
            return Err(f"Invalid JSON data: {str(exc)}")
        except Exception as exc:
            return Err(f"Error deserializing summary segments: {str(exc)}")

    def add(self, video_summary: VideoSummary) -> Result[None, str]:
        session = self._session()
        try:
            segments_json = self._serialize_segments(video_summary.segments())

            session.execute(
                _video_summaries_table.insert().values(
                    id=video_summary.video_summary_id().value(),
                    owner_id=video_summary.owner_id().value(),
                    title=video_summary.title(),
                    segments_json=segments_json,
                    created_at=video_summary.created_at(),
                    updated_at=video_summary.updated_at(),
                )
            )
            session.commit()
            return Ok(None)
        except IntegrityError as exc:
            session.rollback()
            logging.warning(str(exc))
            return Err(f"VideoSummary already exists: {str(exc)}")
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def get(self, video_summary_id: VideoSummaryId) -> Result[VideoSummary, str]:
        session = self._session()
        try:
            row = session.execute(
                _video_summaries_table.select().where(
                    _video_summaries_table.c.id == video_summary_id.value()
                )
            ).fetchone()
            if row is None:
                return Err("VideoSummary not found.")

            # Deserialize summary segments
            segments_result = self._deserialize_segments(row.segments_json)
            if segments_result.is_err():
                return Err(segments_result.err() or "Invalid summary segments data")

            segments = segments_result.ok()
            assert segments is not None

            # Create domain objects
            id_result = VideoSummaryId.try_create(row.id)
            owner_result = UserId.try_create(row.owner_id)

            if id_result.is_err() or owner_result.is_err():
                return Err("Invalid VideoSummary data.")

            id_obj = id_result.ok()
            owner_obj = owner_result.ok()

            if id_obj is None or owner_obj is None:
                return Err("Invalid VideoSummary data.")

            return Ok(
                VideoSummary(
                    id_obj,
                    owner_obj,
                    row.title,
                    segments,
                    row.created_at,
                    row.updated_at,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def update(self, video_summary: VideoSummary) -> Result[None, str]:
        session = self._session()
        try:
            segments_json = self._serialize_segments(video_summary.segments())

            result = session.execute(
                _video_summaries_table.update()
                .where(
                    _video_summaries_table.c.id
                    == video_summary.video_summary_id().value()
                )
                .values(
                    title=video_summary.title(),
                    segments_json=segments_json,
                    updated_at=video_summary.updated_at(),
                )
            )

            if result.rowcount == 0:
                session.rollback()
                return Err("VideoSummary not found.")

            session.commit()
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def remove(self, video_summary_id: VideoSummaryId) -> Result[None, str]:
        session = self._session()
        try:
            result = session.execute(
                _video_summaries_table.delete().where(
                    _video_summaries_table.c.id == video_summary_id.value()
                )
            )

            if result.rowcount == 0:
                session.rollback()
                return Err("VideoSummary not found.")

            session.commit()
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def list_for_user(self, owner_id: UserId) -> Result[list[VideoSummary], str]:
        session = self._session()
        try:
            rows = session.execute(
                _video_summaries_table.select()
                .where(_video_summaries_table.c.owner_id == owner_id.value())
                .order_by(_video_summaries_table.c.updated_at.desc())
            ).fetchall()

            video_summary_list: list[VideoSummary] = []

            for row in rows:
                # Deserialize summary segments
                segments_result = self._deserialize_segments(row.segments_json)
                if segments_result.is_err():
                    logging.warning(
                        f"Skipping invalid summary segments data for ID {row.id}: {segments_result.err()}"
                    )
                    continue

                segments = segments_result.ok()
                assert segments is not None

                # Create domain objects
                id_result = VideoSummaryId.try_create(row.id)
                owner_result = UserId.try_create(row.owner_id)

                if id_result.is_err() or owner_result.is_err():
                    logging.warning(
                        f"Skipping invalid VideoSummary data for ID {row.id}"
                    )
                    continue

                id_obj = id_result.ok()
                owner_obj = owner_result.ok()

                if id_obj is None or owner_obj is None:
                    logging.warning(
                        f"Skipping invalid VideoSummary data for ID {row.id}"
                    )
                    continue

                video_summary_list.append(
                    VideoSummary(
                        id_obj,
                        owner_obj,
                        row.title,
                        segments,
                        row.created_at,
                        row.updated_at,
                    )
                )

            return Ok(video_summary_list)
        except Exception as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()
