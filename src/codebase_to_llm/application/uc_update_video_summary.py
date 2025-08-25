from __future__ import annotations

from codebase_to_llm.application.ports import VideoSummaryRepositoryPort
from codebase_to_llm.domain.video_summary import (
    VideoSummary,
    VideoSummaryId,
    SummarySegment,
)
from codebase_to_llm.domain.result import Result, Ok, Err


class UpdateVideoSummaryUseCase:
    """Use case for updating VideoSummary."""

    def __init__(self, repo: VideoSummaryRepositoryPort) -> None:
        self._repo = repo

    def execute(
        self,
        id_value: str,
        title: str | None = None,
        segments_data: list[dict[str, object]] | None = None,
    ) -> Result[VideoSummary, str]:
        id_result = VideoSummaryId.try_create(id_value)
        if id_result.is_err():
            return Err(id_result.err() or "Invalid VideoSummary ID")

        video_summary_id = id_result.ok()
        assert video_summary_id is not None

        # Get existing VideoSummary
        existing_result = self._repo.get(video_summary_id)
        if existing_result.is_err():
            return Err(existing_result.err() or "VideoSummary not found")

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

        # Update summary segments if provided
        if segments_data is not None:
            segments: list[SummarySegment] = []
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

            updated = updated.replace_segments(segments)

        # Save updated VideoKeyInsights
        repo_result = self._repo.update(updated)
        if repo_result.is_err():
            return Err(repo_result.err() or "Failed to update VideoSummary")

        return Ok(updated)
