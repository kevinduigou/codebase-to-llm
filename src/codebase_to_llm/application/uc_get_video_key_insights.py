from __future__ import annotations

from codebase_to_llm.application.ports import VideoKeyInsightsRepositoryPort
from codebase_to_llm.domain.video_key_insights import (
    VideoKeyInsights,
    VideoKeyInsightId,
)
from codebase_to_llm.domain.result import Result, Err


class GetVideoKeyInsightsUseCase:
    """Use case for retrieving VideoKeyInsights by ID."""

    def __init__(self, repo: VideoKeyInsightsRepositoryPort) -> None:
        self._repo = repo

    def execute(self, id_value: str) -> Result[VideoKeyInsights, str]:
        id_result = VideoKeyInsightId.try_create(id_value)
        if id_result.is_err():
            return Err(id_result.err() or "Invalid VideoKeyInsights ID")

        video_key_insight_id = id_result.ok()
        assert video_key_insight_id is not None

        return self._repo.get(video_key_insight_id)
