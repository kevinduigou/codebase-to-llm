from __future__ import annotations

from codebase_to_llm.application.ports import VideoKeyInsightsRepositoryPort
from codebase_to_llm.domain.video_key_insights import (
    VideoKeyInsights,
    VideoKeyInsightId,
    KeyInsight,
)
from codebase_to_llm.domain.result import Result, Ok, Err


class UpdateVideoKeyInsightsUseCase:
    """Use case for updating VideoKeyInsights."""

    def __init__(self, repo: VideoKeyInsightsRepositoryPort) -> None:
        self._repo = repo

    def execute(
        self,
        id_value: str,
        title: str | None = None,
        key_insights_data: list[dict[str, object]] | None = None,
    ) -> Result[VideoKeyInsights, str]:
        id_result = VideoKeyInsightId.try_create(id_value)
        if id_result.is_err():
            return Err(id_result.err() or "Invalid VideoKeyInsights ID")

        video_key_insight_id = id_result.ok()
        assert video_key_insight_id is not None

        # Get existing VideoKeyInsights
        existing_result = self._repo.get(video_key_insight_id)
        if existing_result.is_err():
            return Err(existing_result.err() or "VideoKeyInsights not found")

        existing = existing_result.ok()
        assert existing is not None

        # Update title if provided
        updated = existing
        if title is not None:
            title_result = updated.update_title(title)
            if title_result.is_err():
                return Err(title_result.err() or "Invalid title")
            updated_title = title_result.ok()
            assert updated_title is not None
            updated = updated_title

        # Update key insights if provided
        if key_insights_data is not None:
            key_insights: list[KeyInsight] = []
            for insight_data in key_insights_data:
                begin_ts = insight_data.get("begin_timestamp", {})
                end_ts = insight_data.get("end_timestamp", {})

                # Extract timestamp components
                begin_hour = (
                    begin_ts.get("hour", 0) if isinstance(begin_ts, dict) else 0
                )
                begin_minute = (
                    begin_ts.get("minute", 0) if isinstance(begin_ts, dict) else 0
                )
                begin_second = (
                    begin_ts.get("second", 0) if isinstance(begin_ts, dict) else 0
                )

                end_hour = end_ts.get("hour", 0) if isinstance(end_ts, dict) else 0
                end_minute = end_ts.get("minute", 0) if isinstance(end_ts, dict) else 0
                end_second = end_ts.get("second", 0) if isinstance(end_ts, dict) else 0

                insight_result = KeyInsight.try_create(
                    content=str(insight_data.get("content", "")),
                    video_url=str(insight_data.get("video_url", "")),
                    begin_hour=begin_hour,
                    begin_minute=begin_minute,
                    begin_second=begin_second,
                    end_hour=end_hour,
                    end_minute=end_minute,
                    end_second=end_second,
                )
                if insight_result.is_err():
                    return Err(f"Invalid key insight: {insight_result.err()}")

                insight = insight_result.ok()
                assert insight is not None
                key_insights.append(insight)

            updated = updated.replace_key_insights(key_insights)

        # Save updated VideoKeyInsights
        repo_result = self._repo.update(updated)
        if repo_result.is_err():
            return Err(repo_result.err() or "Failed to update VideoKeyInsights")

        return Ok(updated)
