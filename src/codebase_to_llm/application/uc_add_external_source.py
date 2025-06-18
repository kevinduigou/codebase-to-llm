from __future__ import annotations
from dataclasses import dataclass


from codebase_to_llm.domain.result import Ok, Result, Err

from .ports import ContextBufferPort


@dataclass
class AddExternalSourceToContextBufferUseCase:

    def __init__(self, context_buffer: ContextBufferPort):
        self._context_buffer = context_buffer

    def execute(self, url: str) -> Result[str, str]:
        lowered = url.lower()
        if "youtube.com" in lowered or "youtu.be" in lowered:
            return self._repo.fetch_youtube_transcript(url)
        fetch_result = self._repo.fetch_web_page(url)
        if fetch_result.is_err():
            return Err(fetch_result.err())  # type: ignore[arg-type]
        self._context_buffer.add_external_source(url, fetch_result.ok())
        return Ok(url)
