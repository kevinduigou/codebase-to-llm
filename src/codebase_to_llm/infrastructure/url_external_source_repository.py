from __future__ import annotations

import re
import urllib.request

import trafilatura

import trafilatura

from codebase_to_llm.application.ports import ExternalSourceRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result


class UrlExternalSourceRepository(ExternalSourceRepositoryPort):
    """Fetches content from the internet using urllib."""

    __slots__ = ()

    def fetch_web_page(self, url: str) -> Result[str, str]:
        try:
            downloaded = trafilatura.fetch_url(url)
            markdown_content = trafilatura.extract(downloaded, output_format="markdown")
            if markdown_content is None:
                return Err("Failed to extract content from the web page.")
            return Ok(markdown_content)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def fetch_youtube_transcript(self, url: str) -> Result[str, str]:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore

        try:
            video_id = _extract_video_id(url)
            languages = ["en", "fr"]
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, languages=languages
            )
            lines = [item.get("text", "") for item in transcript]
            return Ok("\n".join(lines))
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))


def _extract_video_id(url: str) -> str:
    match = re.search(r"(?:v=|/)([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)
    return url
