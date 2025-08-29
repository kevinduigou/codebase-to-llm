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
    "Extract {number_of_key_insights} Key Insights from the transcript\n\n"
    "Then Extract the begin and end of timestamp where this Key Insights is expressed\n"
    "Finally provide a concise title summarizing the video in the field 'title'\n"
    'The output language shall be "{target_language}"\n\n'
)


@final
class KeyInsight(BaseModel):
    content: str
    video_url: str
    begin_timestamp: str
    end_timestamp: str

    model_config = ConfigDict(frozen=True)


@final
class KeyInsightsResult(BaseModel):
    title: str
    insights: list[KeyInsight]

    model_config = ConfigDict(frozen=True)


@final
class ExtractKeyInsightsUseCase:
    def execute(
        self,
        url: str,
        model_id: ModelId,
        target_language: str,
        number_of_key_insights: int,
        external_repo: ExternalSourceRepositoryPort,
        llm_adapter: LLMAdapterPort,
        model_repo: ModelRepositoryPort,
        api_key_repo: ApiKeyRepositoryPort,
    ) -> Result[KeyInsightsResult, str]:
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

        prompt_with_language = PROMPT_TEMPLATE.format(
            target_language=target_language,
            number_of_key_insights=number_of_key_insights,
        )
        prompt = (
            f"{prompt_with_language}\n\nVideo URL: {url}\n\nTranscript:\n{transcript}"
        )

        response_result = llm_adapter.structured_output(
            prompt, model_name, api_key, KeyInsightsResult
        )
        if response_result.is_err():
            return Err(response_result.err() or "Error generating key insights")
        parsed = response_result.ok()
        if parsed is None:
            return Err("Failed to parse key insights")
        insights_model = cast(KeyInsightsResult, parsed)
        return Ok(insights_model)
