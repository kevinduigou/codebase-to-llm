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

PROMPT = (
    "First find the different section in the vidéos then Make a summury segment by segment\n\n"
    "Format by giving begin and end timestampof each sections"
)


@final
class SummarySegment(BaseModel):
    content: str
    video_url: str
    begin_timestamp: str
    end_timestamp: str

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

        prompt = f"{PROMPT}\n\nVideo URL: {url}\n\nTranscript:\n{transcript}"

        response_result = llm_adapter.structured_output(
            prompt, model_name, api_key, SummarySegments
        )
        if response_result.is_err():
            return Err(response_result.err() or "Error generating summary")
        parsed = response_result.ok()
        if parsed is None:
            return Err("Failed to parse summary")
        segments_model = cast(SummarySegments, parsed)
        return Ok(segments_model.segments)
