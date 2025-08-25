from __future__ import annotations
import logging
import json

from typing_extensions import final
from sqlalchemy import Column, String, Text, DateTime, Table
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from codebase_to_llm.application.ports import VideoKeyInsightsRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.video_key_insights import (
    VideoKeyInsights,
    VideoKeyInsightId,
    KeyInsight,
)
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.infrastructure.db import DatabaseSessionManager, get_metadata

_video_key_insights_table = Table(
    "video_key_insights",
    get_metadata(),
    Column("id", String, primary_key=True),
    Column("owner_id", String, nullable=False),
    Column("title", String, nullable=False),
    Column("key_insights_json", Text, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)


@final
class SqlAlchemyVideoKeyInsightsRepository(VideoKeyInsightsRepositoryPort):
    """VideoKeyInsights repository backed by SQLAlchemy."""

    __slots__ = ()

    def _session(self) -> Session:
        return DatabaseSessionManager.get_session()

    def _serialize_key_insights(self, key_insights: list[KeyInsight]) -> str:
        """Serialize key insights to JSON string."""
        insights_data = []
        for insight in key_insights:
            insights_data.append(
                {
                    "content": insight.content().value(),
                    "video_url": insight.video_url().value(),
                    "begin_timestamp": {
                        "hour": insight.begin_timestamp().hour(),
                        "minute": insight.begin_timestamp().minute(),
                        "second": insight.begin_timestamp().second(),
                    },
                    "end_timestamp": {
                        "hour": insight.end_timestamp().hour(),
                        "minute": insight.end_timestamp().minute(),
                        "second": insight.end_timestamp().second(),
                    },
                }
            )
        return json.dumps(insights_data)

    def _deserialize_key_insights(self, json_str: str) -> Result[list[KeyInsight], str]:
        """Deserialize key insights from JSON string."""
        try:
            insights_data = json.loads(json_str)
            key_insights: list[KeyInsight] = []

            for insight_data in insights_data:
                begin_ts = insight_data.get("begin_timestamp", {})
                end_ts = insight_data.get("end_timestamp", {})

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

                insight_result = KeyInsight.try_create(
                    content=insight_data.get("content", ""),
                    video_url=insight_data.get("video_url", ""),
                    begin_hour=begin_hour,
                    begin_minute=begin_minute,
                    begin_second=begin_second,
                    end_hour=end_hour,
                    end_minute=end_minute,
                    end_second=end_second,
                )
                if insight_result.is_err():
                    return Err(f"Invalid key insight data: {insight_result.err()}")

                insight = insight_result.ok()
                assert insight is not None
                key_insights.append(insight)

            return Ok(key_insights)
        except json.JSONDecodeError as exc:
            return Err(f"Invalid JSON data: {str(exc)}")
        except Exception as exc:
            return Err(f"Error deserializing key insights: {str(exc)}")

    def add(self, video_key_insights: VideoKeyInsights) -> Result[None, str]:
        session = self._session()
        try:
            key_insights_json = self._serialize_key_insights(
                video_key_insights.key_insights()
            )

            session.execute(
                _video_key_insights_table.insert().values(
                    id=video_key_insights.video_key_insight_id().value(),
                    owner_id=video_key_insights.owner_id().value(),
                    title=video_key_insights.title(),
                    key_insights_json=key_insights_json,
                    created_at=video_key_insights.created_at(),
                    updated_at=video_key_insights.updated_at(),
                )
            )
            session.commit()
            return Ok(None)
        except IntegrityError as exc:
            session.rollback()
            logging.warning(str(exc))
            return Err(f"VideoKeyInsights already exists: {str(exc)}")
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def get(
        self, video_key_insight_id: VideoKeyInsightId
    ) -> Result[VideoKeyInsights, str]:
        session = self._session()
        try:
            row = session.execute(
                _video_key_insights_table.select().where(
                    _video_key_insights_table.c.id == video_key_insight_id.value()
                )
            ).fetchone()
            if row is None:
                return Err("VideoKeyInsights not found.")

            # Deserialize key insights
            key_insights_result = self._deserialize_key_insights(row.key_insights_json)
            if key_insights_result.is_err():
                return Err(key_insights_result.err() or "Invalid key insights data")

            key_insights = key_insights_result.ok()
            assert key_insights is not None

            # Create domain objects
            id_result = VideoKeyInsightId.try_create(row.id)
            owner_result = UserId.try_create(row.owner_id)

            if id_result.is_err() or owner_result.is_err():
                return Err("Invalid VideoKeyInsights data.")

            id_obj = id_result.ok()
            owner_obj = owner_result.ok()

            if id_obj is None or owner_obj is None:
                return Err("Invalid VideoKeyInsights data.")

            return Ok(
                VideoKeyInsights(
                    id_obj,
                    owner_obj,
                    row.title,
                    key_insights,
                    row.created_at,
                    row.updated_at,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def update(self, video_key_insights: VideoKeyInsights) -> Result[None, str]:
        session = self._session()
        try:
            key_insights_json = self._serialize_key_insights(
                video_key_insights.key_insights()
            )

            result = session.execute(
                _video_key_insights_table.update()
                .where(
                    _video_key_insights_table.c.id
                    == video_key_insights.video_key_insight_id().value()
                )
                .values(
                    title=video_key_insights.title(),
                    key_insights_json=key_insights_json,
                    updated_at=video_key_insights.updated_at(),
                )
            )

            if result.rowcount == 0:
                session.rollback()
                return Err("VideoKeyInsights not found.")

            session.commit()
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def remove(self, video_key_insight_id: VideoKeyInsightId) -> Result[None, str]:
        session = self._session()
        try:
            result = session.execute(
                _video_key_insights_table.delete().where(
                    _video_key_insights_table.c.id == video_key_insight_id.value()
                )
            )

            if result.rowcount == 0:
                session.rollback()
                return Err("VideoKeyInsights not found.")

            session.commit()
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()

    def list_for_user(self, owner_id: UserId) -> Result[list[VideoKeyInsights], str]:
        session = self._session()
        try:
            rows = session.execute(
                _video_key_insights_table.select()
                .where(_video_key_insights_table.c.owner_id == owner_id.value())
                .order_by(_video_key_insights_table.c.updated_at.desc())
            ).fetchall()

            video_key_insights_list: list[VideoKeyInsights] = []

            for row in rows:
                # Deserialize key insights
                key_insights_result = self._deserialize_key_insights(
                    row.key_insights_json
                )
                if key_insights_result.is_err():
                    logging.warning(
                        f"Skipping invalid key insights data for ID {row.id}: {key_insights_result.err()}"
                    )
                    continue

                key_insights = key_insights_result.ok()
                assert key_insights is not None

                # Create domain objects
                id_result = VideoKeyInsightId.try_create(row.id)
                owner_result = UserId.try_create(row.owner_id)

                if id_result.is_err() or owner_result.is_err():
                    logging.warning(
                        f"Skipping invalid VideoKeyInsights data for ID {row.id}"
                    )
                    continue

                id_obj = id_result.ok()
                owner_obj = owner_result.ok()

                if id_obj is None or owner_obj is None:
                    logging.warning(
                        f"Skipping invalid VideoKeyInsights data for ID {row.id}"
                    )
                    continue

                video_key_insights_list.append(
                    VideoKeyInsights(
                        id_obj,
                        owner_obj,
                        row.title,
                        key_insights,
                        row.created_at,
                        row.updated_at,
                    )
                )

            return Ok(video_key_insights_list)
        except Exception as exc:  # noqa: BLE001
            logging.warning(str(exc))
            return Err(str(exc))
        finally:
            session.close()
