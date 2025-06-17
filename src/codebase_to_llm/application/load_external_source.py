from __future__ import annotations

from typing import Final

from codebase_to_llm.domain.result import Result

from .ports import ExternalSourceRepositoryPort


class LoadExternalSourceUseCase:
    """Orchestrates loading text from external URLs."""

    __slots__ = ("_repo",)

    def __init__(self, repo: ExternalSourceRepositoryPort) -> None:
        self._repo: Final = repo

    def execute(self, url: str) -> Result[str, str]:
        lowered = url.lower()
        if "youtube.com" in lowered or "youtu.be" in lowered:
            return self._repo.fetch_youtube_transcript(url)
        return self._repo.fetch_web_page(url)
