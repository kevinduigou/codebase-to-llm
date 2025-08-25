from __future__ import annotations

from typing_extensions import final
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.value_object import ValueObject
from codebase_to_llm.domain.entity import Entity
from codebase_to_llm.domain.user import UserId
from datetime import datetime
import uuid


@final
class VideoKeyInsightId(ValueObject):
    """Unique identifier for a VideoKeyInsight."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["VideoKeyInsightId", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("VideoKeyInsight ID cannot be empty.")
        return Ok(VideoKeyInsightId(trimmed_value))

    @staticmethod
    def generate() -> "VideoKeyInsightId":
        return VideoKeyInsightId(str(uuid.uuid4()))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class KeyInsightContent(ValueObject):
    """Content of a key insight."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["KeyInsightContent", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("Key insight content cannot be empty.")
        if len(trimmed_value) > 5000:
            return Err("Key insight content cannot exceed 5000 characters.")
        return Ok(KeyInsightContent(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class VideoUrl(ValueObject):
    """URL of the video."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["VideoUrl", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("Video URL cannot be empty.")
        if len(trimmed_value) > 2000:
            return Err("Video URL cannot exceed 2000 characters.")
        # Basic URL validation
        if not (
            trimmed_value.startswith("http://") or trimmed_value.startswith("https://")
        ):
            return Err("Video URL must start with http:// or https://")
        return Ok(VideoUrl(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class Timestamp(ValueObject):
    """Timestamp for video segments."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["Timestamp", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("Timestamp cannot be empty.")
        # Basic timestamp format validation (HH:MM:SS or MM:SS)
        import re

        if not re.match(r"^(\d{1,2}:)?\d{1,2}:\d{2}$", trimmed_value):
            return Err("Timestamp must be in format MM:SS or HH:MM:SS")
        return Ok(Timestamp(trimmed_value))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class KeyInsight(ValueObject):
    """A single key insight from a video segment."""

    __slots__ = (
        "_content",
        "_video_url",
        "_begin_timestamp",
        "_end_timestamp",
    )
    _content: KeyInsightContent
    _video_url: VideoUrl
    _begin_timestamp: Timestamp
    _end_timestamp: Timestamp

    @staticmethod
    def try_create(
        content: str,
        video_url: str,
        begin_timestamp: str,
        end_timestamp: str,
    ) -> Result["KeyInsight", str]:
        content_result = KeyInsightContent.try_create(content)
        if content_result.is_err():
            return Err(f"Invalid content: {content_result.err()}")

        url_result = VideoUrl.try_create(video_url)
        if url_result.is_err():
            return Err(f"Invalid video URL: {url_result.err()}")

        begin_result = Timestamp.try_create(begin_timestamp)
        if begin_result.is_err():
            return Err(f"Invalid begin timestamp: {begin_result.err()}")

        end_result = Timestamp.try_create(end_timestamp)
        if end_result.is_err():
            return Err(f"Invalid end timestamp: {end_result.err()}")

        content_obj = content_result.ok()
        url_obj = url_result.ok()
        begin_obj = begin_result.ok()
        end_obj = end_result.ok()

        if (
            content_obj is None
            or url_obj is None
            or begin_obj is None
            or end_obj is None
        ):
            return Err("Unexpected error: one of the value objects is None")

        return Ok(KeyInsight(content_obj, url_obj, begin_obj, end_obj))

    def __init__(
        self,
        content: KeyInsightContent,
        video_url: VideoUrl,
        begin_timestamp: Timestamp,
        end_timestamp: Timestamp,
    ) -> None:
        self._content = content
        self._video_url = video_url
        self._begin_timestamp = begin_timestamp
        self._end_timestamp = end_timestamp

    def content(self) -> KeyInsightContent:
        return self._content

    def video_url(self) -> VideoUrl:
        return self._video_url

    def begin_timestamp(self) -> Timestamp:
        return self._begin_timestamp

    def end_timestamp(self) -> Timestamp:
        return self._end_timestamp


@final
class VideoKeyInsights(Entity):
    """Collection of key insights for a video, owned by a user."""

    __slots__ = (
        "_owner_id",
        "_title",
        "_key_insights",
        "_created_at",
        "_updated_at",
    )
    _owner_id: UserId
    _title: str
    _key_insights: list[KeyInsight]
    _created_at: datetime
    _updated_at: datetime

    @staticmethod
    def try_create(
        id_value: str,
        owner_id: str,
        title: str,
        key_insights: list[KeyInsight] | None = None,
    ) -> Result["VideoKeyInsights", str]:
        id_result = VideoKeyInsightId.try_create(id_value)
        if id_result.is_err():
            return Err(f"Invalid VideoKeyInsight ID: {id_result.err()}")

        owner_result = UserId.try_create(owner_id)
        if owner_result.is_err():
            return Err(f"Invalid owner ID: {owner_result.err()}")

        title_trimmed = title.strip()
        if not title_trimmed:
            return Err("Title cannot be empty.")
        if len(title_trimmed) > 200:
            return Err("Title cannot exceed 200 characters.")

        id_obj = id_result.ok()
        owner_obj = owner_result.ok()

        if id_obj is None or owner_obj is None:
            return Err("Unexpected error: one of the value objects is None")

        now = datetime.utcnow()
        return Ok(
            VideoKeyInsights(
                id_obj,
                owner_obj,
                title_trimmed,
                key_insights or [],
                now,
                now,
            )
        )

    def __init__(
        self,
        id: VideoKeyInsightId,
        owner_id: UserId,
        title: str,
        key_insights: list[KeyInsight],
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(id)
        self._owner_id = owner_id
        self._title = title
        self._key_insights = key_insights
        self._created_at = created_at
        self._updated_at = updated_at

    def video_key_insight_id(self) -> VideoKeyInsightId:
        return self._id  # type: ignore[return-value]

    def owner_id(self) -> UserId:
        return self._owner_id

    def title(self) -> str:
        return self._title

    def key_insights(self) -> list[KeyInsight]:
        return self._key_insights.copy()

    def created_at(self) -> datetime:
        return self._created_at

    def updated_at(self) -> datetime:
        return self._updated_at

    def add_key_insight(self, key_insight: KeyInsight) -> "VideoKeyInsights":
        """Add a key insight and return a new instance."""
        new_insights = self._key_insights.copy()
        new_insights.append(key_insight)
        return VideoKeyInsights(
            self._id,  # type: ignore[arg-type]
            self._owner_id,
            self._title,
            new_insights,
            self._created_at,
            datetime.utcnow(),
        )

    def remove_key_insight_at_index(
        self, index: int
    ) -> Result["VideoKeyInsights", str]:
        """Remove a key insight at the given index and return a new instance."""
        if index < 0 or index >= len(self._key_insights):
            return Err(f"Index {index} is out of bounds")

        new_insights = self._key_insights.copy()
        new_insights.pop(index)
        return Ok(
            VideoKeyInsights(
                self._id,  # type: ignore[arg-type]
                self._owner_id,
                self._title,
                new_insights,
                self._created_at,
                datetime.utcnow(),
            )
        )

    def update_title(self, new_title: str) -> Result["VideoKeyInsights", str]:
        """Update the title and return a new instance."""
        title_trimmed = new_title.strip()
        if not title_trimmed:
            return Err("Title cannot be empty.")
        if len(title_trimmed) > 200:
            return Err("Title cannot exceed 200 characters.")

        return Ok(
            VideoKeyInsights(
                self._id,  # type: ignore[arg-type]
                self._owner_id,
                title_trimmed,
                self._key_insights,
                self._created_at,
                datetime.utcnow(),
            )
        )

    def replace_key_insights(
        self, new_insights: list[KeyInsight]
    ) -> "VideoKeyInsights":
        """Replace all key insights and return a new instance."""
        return VideoKeyInsights(
            self._id,  # type: ignore[arg-type]
            self._owner_id,
            self._title,
            new_insights.copy(),
            self._created_at,
            datetime.utcnow(),
        )
