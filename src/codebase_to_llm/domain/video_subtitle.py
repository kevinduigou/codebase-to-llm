from __future__ import annotations

from typing_extensions import final

from .entity import Entity
from .result import Err, Ok, Result
from .stored_file import StoredFileId
from .value_object import ValueObject


@final
class VideoSubtitleId(ValueObject):
    """Unique identifier for a video to subtitle association."""

    __slots__ = ("_value",)
    _value: str

    @staticmethod
    def try_create(value: str) -> Result["VideoSubtitleId", str]:
        trimmed = value.strip()
        if not trimmed:
            return Err("Association id cannot be empty.")
        return Ok(VideoSubtitleId(trimmed))

    def __init__(self, value: str) -> None:
        self._value = value

    def value(self) -> str:
        return self._value


@final
class VideoSubtitle(Entity):
    """Association between a video file and an ASS subtitle file."""

    __slots__ = ("_video_file_id", "_subtitle_file_id")
    _video_file_id: StoredFileId
    _subtitle_file_id: StoredFileId

    @staticmethod
    def try_create(
        id_value: str,
        video_file_id: StoredFileId,
        subtitle_file_id: StoredFileId,
    ) -> Result["VideoSubtitle", str]:
        id_res = VideoSubtitleId.try_create(id_value)
        if id_res.is_err():
            return Err(id_res.err() or "Invalid association id.")
        id_obj = id_res.ok()
        assert id_obj is not None
        return Ok(VideoSubtitle(id_obj, video_file_id, subtitle_file_id))

    def __init__(
        self,
        id: VideoSubtitleId,
        video_file_id: StoredFileId,
        subtitle_file_id: StoredFileId,
    ) -> None:
        super().__init__(id)
        self._video_file_id = video_file_id
        self._subtitle_file_id = subtitle_file_id

    def video_file_id(self) -> StoredFileId:
        return self._video_file_id

    def subtitle_file_id(self) -> StoredFileId:
        return self._subtitle_file_id

    def update(self, subtitle_file_id: StoredFileId) -> "VideoSubtitle":
        return VideoSubtitle(self.id(), self._video_file_id, subtitle_file_id)
