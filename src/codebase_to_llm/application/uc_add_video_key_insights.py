from __future__ import annotations

from codebase_to_llm.application.ports import VideoKeyInsightsRepositoryPort
from codebase_to_llm.domain.video_key_insights import VideoKeyInsights, KeyInsight
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class AddVideoKeyInsightsUseCase:
    """Use case for creating and persisting VideoKeyInsights."""

    def __init__(self, repo: VideoKeyInsightsRepositoryPort) -> None:
        self._repo = repo

    def execute(
        self,
        id_value: str,
        owner_id_value: str,
        title: str,
        key_insights_data: list[dict[str, object]] | None = None,
    ) -> Result[VideoKeyInsights, str]:
        owner_result = UserId.try_create(owner_id_value)
        if owner_result.is_err():
            return Err(owner_result.err() or "Invalid owner id")
        owner_id = owner_result.ok()
        assert owner_id is not None

        # Parse key insights if provided
        key_insights: list[KeyInsight] = []
        if key_insights_data:
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

        video_key_insights_result = VideoKeyInsights.try_create(
            id_value, owner_id_value, title, key_insights
        )
        if video_key_insights_result.is_err():
            return Err(
                video_key_insights_result.err() or "Invalid VideoKeyInsights data"
            )

        video_key_insights = video_key_insights_result.ok()
        assert video_key_insights is not None

        repo_result = self._repo.add(video_key_insights)
        if repo_result.is_err():
            return Err(repo_result.err() or "Failed to save VideoKeyInsights")

        return Ok(video_key_insights)
