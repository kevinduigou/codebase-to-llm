from __future__ import annotations


from typing_extensions import final
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.value_object import ValueObject
from codebase_to_llm.domain.entity import Entity
from codebase_to_llm.domain.user import UserId
from datetime import datetime
import uuid


@final
class VideoSummaryId(ValueObject):
    """Unique identifier for a VideoSummary."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["VideoSummaryId", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("VideoSummary ID cannot be empty.")
        return Ok(VideoSummaryId(trimmed_value))

    @staticmethod
    def generate() -> "VideoSummaryId":
        return VideoSummaryId(str(uuid.uuid4()))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class SummaryContent(ValueObject):
    """Content of a summary segment."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["SummaryContent", str]:
        trimmed_value = value.strip()
        if not trimmed_value:
            return Err("summary segment content cannot be empty.")
        if len(trimmed_value) > 5000:
            return Err("summary segment content cannot exceed 5000 characters.")
        return Ok(SummaryContent(trimmed_value))

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

    __slots__ = ("_hour", "_minute", "_second")
    _hour: int
    _minute: int
    _second: int

    @staticmethod
    def try_create(hour: int, minute: int, second: int) -> Result["Timestamp", str]:
        if hour < 0 or hour > 23:
            return Err("Hour must be between 0 and 23.")
        if minute < 0 or minute > 59:
            return Err("Minute must be between 0 and 59.")
        if second < 0 or second > 59:
            return Err("Second must be between 0 and 59.")
        return Ok(Timestamp(hour, minute, second))

    def __init__(self, hour: int, minute: int, second: int) -> None:
        self._hour = hour
        self._minute = minute
        self._second = second

    def hour(self) -> int:
        return self._hour

    def minute(self) -> int:
        return self._minute

    def second(self) -> int:
        return self._second

    def to_string(self) -> str:
        """Convert timestamp to HH:MM:SS format."""
        return f"{self._hour:02d}:{self._minute:02d}:{self._second:02d}"


@final
class SummarySegment(ValueObject):
    """A single summary segment from a video segment."""

    __slots__ = (
        "_content",
        "_video_url",
        "_begin_timestamp",
        "_end_timestamp",
    )
    _content: SummaryContent
    _video_url: VideoUrl
    _begin_timestamp: Timestamp
    _end_timestamp: Timestamp

    @staticmethod
    def try_create(
        content: str,
        video_url: str,
        begin_hour: int,
        begin_minute: int,
        begin_second: int,
        end_hour: int,
        end_minute: int,
        end_second: int,
    ) -> Result["SummarySegment", str]:
        content_result = SummaryContent.try_create(content)
        if content_result.is_err():
            return Err(f"Invalid content: {content_result.err()}")

        url_result = VideoUrl.try_create(video_url)
        if url_result.is_err():
            return Err(f"Invalid video URL: {url_result.err()}")

        begin_result = Timestamp.try_create(begin_hour, begin_minute, begin_second)
        if begin_result.is_err():
            return Err(f"Invalid begin timestamp: {begin_result.err()}")

        end_result = Timestamp.try_create(end_hour, end_minute, end_second)
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

        return Ok(SummarySegment(content_obj, url_obj, begin_obj, end_obj))

    def __init__(
        self,
        content: SummaryContent,
        video_url: VideoUrl,
        begin_timestamp: Timestamp,
        end_timestamp: Timestamp,
    ) -> None:
        self._content = content
        self._video_url = video_url
        self._begin_timestamp = begin_timestamp
        self._end_timestamp = end_timestamp

    def content(self) -> SummaryContent:
        return self._content

    def video_url(self) -> VideoUrl:
        return self._video_url

    def begin_timestamp(self) -> Timestamp:
        return self._begin_timestamp

    def end_timestamp(self) -> Timestamp:
        return self._end_timestamp


@final
class VideoSummary(Entity):
    """Collection of summary segments for a video, owned by a user."""

    __slots__ = (
        "_owner_id",
        "_title",
        "_segments",
        "_created_at",
        "_updated_at",
    )
    _owner_id: UserId
    _title: str
    _segments: list[SummarySegment]
    _created_at: datetime
    _updated_at: datetime

    @staticmethod
    def try_create(
        id_value: str,
        owner_id: str,
        title: str,
        segments: list[SummarySegment] | None = None,
    ) -> Result["VideoSummary", str]:
        id_result = VideoSummaryId.try_create(id_value)
        if id_result.is_err():
            return Err(f"Invalid VideoSummary ID: {id_result.err()}")

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
            VideoSummary(
                id_obj,
                owner_obj,
                title_trimmed,
                segments or [],
                now,
                now,
            )
        )

    def __init__(
        self,
        id: VideoSummaryId,
        owner_id: UserId,
        title: str,
        segments: list[SummarySegment],
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(id)
        self._owner_id = owner_id
        self._title = title
        self._segments = segments
        self._created_at = created_at
        self._updated_at = updated_at

    def video_summary_id(self) -> VideoSummaryId:
        return self._id  # type: ignore[return-value]

    def owner_id(self) -> UserId:
        return self._owner_id

    def title(self) -> str:
        return self._title

    def segments(self) -> list[SummarySegment]:
        return self._segments.copy()

    def created_at(self) -> datetime:
        return self._created_at

    def updated_at(self) -> datetime:
        return self._updated_at

    def add_segment(self, segment: SummarySegment) -> "VideoSummary":
        """Add a summary segment and return a new instance."""
        new_segments = self._segments.copy()
        new_segments.append(segment)
        return VideoSummary(
            self._id,  # type: ignore[arg-type]
            self._owner_id,
            self._title,
            new_segments,
            self._created_at,
            datetime.utcnow(),
        )

    def remove_segment_at_index(self, index: int) -> Result["VideoSummary", str]:
        """Remove a summary segment at the given index and return a new instance."""
        if index < 0 or index >= len(self._segments):
            return Err(f"Index {index} is out of bounds")

        new_segments = self._segments.copy()
        new_segments.pop(index)
        return Ok(
            VideoSummary(
                self._id,  # type: ignore[arg-type]
                self._owner_id,
                self._title,
                new_segments,
                self._created_at,
                datetime.utcnow(),
            )
        )

    def update_title(self, new_title: str) -> Result["VideoSummary", str]:
        """Update the title and return a new instance."""
        title_trimmed = new_title.strip()
        if not title_trimmed:
            return Err("Title cannot be empty.")
        if len(title_trimmed) > 200:
            return Err("Title cannot exceed 200 characters.")

        return Ok(
            VideoSummary(
                self._id,  # type: ignore[arg-type]
                self._owner_id,
                title_trimmed,
                self._segments,
                self._created_at,
                datetime.utcnow(),
            )
        )

    def replace_segments(self, new_segments: list[SummarySegment]) -> "VideoSummary":
        """Replace all summary segments and return a new instance."""
        return VideoSummary(
            self._id,  # type: ignore[arg-type]
            self._owner_id,
            self._title,
            new_segments.copy(),
            self._created_at,
            datetime.utcnow(),
        )
