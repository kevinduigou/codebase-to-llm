from __future__ import annotations

from codebase_to_llm.application.ports import VideoSummaryRepositoryPort
from codebase_to_llm.domain.video_summary import VideoSummary, SummarySegment
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Ok, Err


class AddVideoSummaryUseCase:
    """Use case for creating and persisting VideoSummary."""

    def __init__(self, repo: VideoSummaryRepositoryPort) -> None:
        self._repo = repo

    def execute(
        self,
        id_value: str,
        owner_id_value: str,
        title: str,
        segments_data: list[dict[str, object]] | None = None,
    ) -> Result[VideoSummary, str]:
        owner_result = UserId.try_create(owner_id_value)
        if owner_result.is_err():
            return Err(owner_result.err() or "Invalid owner id")
        owner_id = owner_result.ok()
        assert owner_id is not None

        # Parse summary segments if provided
        segments: list[SummarySegment] = []
        if segments_data:
            for segment_data in segments_data:
                begin_ts = segment_data.get("begin_timestamp", {})
                end_ts = segment_data.get("end_timestamp", {})

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

                segment_result = SummarySegment.try_create(
                    content=str(segment_data.get("content", "")),
                    video_url=str(segment_data.get("video_url", "")),
                    begin_hour=begin_hour,
                    begin_minute=begin_minute,
                    begin_second=begin_second,
                    end_hour=end_hour,
                    end_minute=end_minute,
                    end_second=end_second,
                )
                if segment_result.is_err():
                    return Err(f"Invalid summary segment: {segment_result.err()}")

                segment = segment_result.ok()
                assert segment is not None
                segments.append(segment)

        video_summary_result = VideoSummary.try_create(
            id_value, owner_id_value, title, segments
        )
        if video_summary_result.is_err():
            return Err(video_summary_result.err() or "Invalid VideoSummary data")

        video_summary = video_summary_result.ok()
        assert video_summary is not None

        repo_result = self._repo.add(video_summary)
        if repo_result.is_err():
            return Err(repo_result.err() or "Failed to save VideoSummary")

        return Ok(video_summary)
