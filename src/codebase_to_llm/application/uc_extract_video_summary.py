from __future__ import annotations

from typing import final, cast
from pydantic import BaseModel, ConfigDict

from codebase_to_llm.application.ports import (
    ApiKeyRepositoryPort,
    ExternalSourceRepositoryPort,
    LLMAdapterPort,
    ModelRepositoryPort,
)
from codebase_to_llm.application.uc_get_model_api_key import GetModelApiKeyUseCase
from codebase_to_llm.domain.model import ModelId
from codebase_to_llm.domain.result import Err, Ok, Result

PROMPT_TEMPLATE = (
    "Analyze the video transcript and create a summary divided into distinct segments.\n\n"
    "For each segment:\n"
    "1. Provide a meaningful summary of the content\n"
    "2. Include the video URL\n"
    "3. Specify accurate begin_timestamp and end_timestamp in the format:\n"
    "   - hour: integer (0-23)\n"
    "   - minute: integer (0-59)\n"
    "   - second: integer (0-59)\n\n"
    "IMPORTANT: \n"
    'In most transcript hour is absent, if timestamp as only 2 element mm:ss, it means hour shall be set to 0'
    'The output language shall be "{target_language}"\n\n'
    "Example format:\n"
    'begin_timestamp: {{"hour": 0, "minute": 1, "second": 30}}\n'
    'end_timestamp: {{"hour": 0, "minute": 3, "second": 45}}'
)


class Timestamp(BaseModel):
    hour: int
    minute: int
    second: int


@final
class SummarySegment(BaseModel):
    content: str
    video_url: str
    begin_timestamp: Timestamp
    end_timestamp: Timestamp

    model_config = ConfigDict(frozen=True)


@final
class SummarySegments(BaseModel):
    segments: list[SummarySegment]

    model_config = ConfigDict(frozen=True)


@final
class ExtractVideoSummaryUseCase:
    def execute(
        self,
        url: str,
        model_id: ModelId,
        target_language: str,
        external_repo: ExternalSourceRepositoryPort,
        llm_adapter: LLMAdapterPort,
        model_repo: ModelRepositoryPort,
        api_key_repo: ApiKeyRepositoryPort,
    ) -> Result[list[SummarySegment], str]:
        transcript_result = external_repo.fetch_youtube_transcript(
            url, include_timestamps=True
        )
        if transcript_result.is_err():
            return Err(transcript_result.err() or "Error fetching transcript")
        transcript = transcript_result.ok()
        if transcript is None:
            return Err("Transcript not found")

        details_result = GetModelApiKeyUseCase().execute(
            model_id, model_repo, api_key_repo
        )
        if details_result.is_err():
            return Err(details_result.err() or "Error retrieving model/API key")
        details = details_result.ok()
        if details is None:
            return Err("Model or API key not found")
        model_name, api_key = details

        prompt_with_language = PROMPT_TEMPLATE.format(target_language=target_language)
        prompt = (
            f"{prompt_with_language}\n\nVideo URL: {url}\n\nTranscript:\n{transcript}"
        )

        response_result = llm_adapter.structured_output(
            prompt, model_name, api_key, SummarySegments
        )
        if response_result.is_err():
            return Err(response_result.err() or "Error generating summary")
        parsed = response_result.ok()
        if parsed is None:
            return Err("Failed to parse summary")
        segments_model = cast(SummarySegments, parsed)

        # Validate and fix invalid timestamps
        validated_segments = []
        for i, segment in enumerate(segments_model.segments):
            begin_seconds = (
                segment.begin_timestamp.hour * 3600
                + segment.begin_timestamp.minute * 60
                + segment.begin_timestamp.second
            )
            end_seconds = (
                segment.end_timestamp.hour * 3600
                + segment.end_timestamp.minute * 60
                + segment.end_timestamp.second
            )

            # If timestamps are invalid (both zero or begin >= end), create fallback timestamps
            if begin_seconds >= end_seconds:
                # Create fallback timestamps based on segment index
                fallback_begin_minutes = i * 2  # Each segment starts 2 minutes apart
                fallback_end_minutes = (
                    fallback_begin_minutes + 1
                )  # Each segment is 1 minute long

                # Create new segment with corrected timestamps
                corrected_segment = SummarySegment(
                    content=segment.content,
                    video_url=segment.video_url,
                    begin_timestamp=Timestamp(
                        hour=fallback_begin_minutes // 60,
                        minute=fallback_begin_minutes % 60,
                        second=0,
                    ),
                    end_timestamp=Timestamp(
                        hour=fallback_end_minutes // 60,
                        minute=fallback_end_minutes % 60,
                        second=0,
                    ),
                )
                validated_segments.append(corrected_segment)
            else:
                validated_segments.append(segment)

        return Ok(validated_segments)
