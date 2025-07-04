from __future__ import annotations
from dataclasses import dataclass

from codebase_to_llm.domain.context_buffer import ExternalSource
from codebase_to_llm.domain.result import Ok, Result, Err

from .ports import ContextBufferPort, ExternalSourceRepositoryPort


@dataclass
class AddExternalSourceToContextBufferUseCase:

    def __init__(
        self, context_buffer: ContextBufferPort, repo: ExternalSourceRepositoryPort
    ):
        self._context_buffer = context_buffer
        self._repo = repo

    def execute(self, url: str) -> Result[str, str]:
        lowered = url.lower()
        if "youtube.com" in lowered or "youtu.be" in lowered:
            fetch_result_fn = self._repo.fetch_youtube_transcript
        else:
            fetch_result_fn = self._repo.fetch_web_page

        external_source = ExternalSource.try_from_url(url, fetch_result_fn)
        if external_source.is_err():
            return Err(external_source.err() or "Unknown error")
        self._context_buffer.add_external_source(external_source.ok())
        return Ok(external_source.ok())
