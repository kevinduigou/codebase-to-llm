from __future__ import annotations

import re
import urllib.request

from codebase_to_llm.application.ports import ExternalSourceRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result


class UrlExternalSourceRepository(ExternalSourceRepositoryPort):
    """Fetches content from the internet using urllib."""

    __slots__ = ()

    def fetch_web_page(self, url: str) -> Result[str, str]:
        try:
            with urllib.request.urlopen(url) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                data = response.read().decode(charset, errors="ignore")
            text = re.sub(r"<[^>]+>", " ", data)
            return Ok(text)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def fetch_youtube_transcript(self, url: str) -> Result[str, str]:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore

        try:
            video_id = _extract_video_id(url)
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            lines = [item.get("text", "") for item in transcript]
            return Ok("\n".join(lines))
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))


def _extract_video_id(url: str) -> str:
    match = re.search(r"(?:v=|/)([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)
    return url
