from __future__ import annotations

from codebase_to_llm.application.ports import VideoSummaryRepositoryPort
from codebase_to_llm.domain.video_summary import (
    VideoSummary,
    VideoSummaryId,
)
from codebase_to_llm.domain.result import Result, Err


class GetVideoSummaryUseCase:
    """Use case for retrieving VideoSummary by ID."""

    def __init__(self, repo: VideoSummaryRepositoryPort) -> None:
        self._repo = repo

    def execute(self, id_value: str) -> Result[VideoSummary, str]:
        id_result = VideoSummaryId.try_create(id_value)
        if id_result.is_err():
            return Err(id_result.err() or "Invalid VideoSummary ID")

        video_summary_id = id_result.ok()
        assert video_summary_id is not None

        return self._repo.get(video_summary_id)
