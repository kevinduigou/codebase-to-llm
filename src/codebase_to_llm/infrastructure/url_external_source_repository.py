from __future__ import annotations

import re

import httpx
import trafilatura


from codebase_to_llm.application.ports import ExternalSourceRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result


class UrlExternalSourceRepository(ExternalSourceRepositoryPort):
    """Fetches content from the internet using urllib."""

    __slots__ = ()

    def fetch_web_page(self, url: str) -> Result[str, str]:

        try:
            # 1️⃣  First attempt: Trafilatura download helper
            downloaded = trafilatura.fetch_url(url)

            # 2️⃣  Fallback #1: one-shot helper (download + extract in one go)
            if downloaded is None:
                markdown_content = trafilatura.extract(
                    downloaded, output_format="markdown"
                )
                if markdown_content:
                    return Ok(markdown_content)

            # 3️⃣  Fallback #2: manual download → Trafilatura extract
            if downloaded is None:  # still nothing
                try:
                    USER_AGENT = (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/126.0 Safari/537.36"
                    )
                    resp = httpx.get(
                        url,
                        headers={"User-Agent": USER_AGENT},
                        follow_redirects=True,
                        timeout=10,
                    )
                    resp.raise_for_status()
                    downloaded = resp.text
                except Exception as http_err:
                    return Err(f"HTTP fetch failed: {http_err}")

            # 4️⃣  Extract (works with either HTML string or bytes)
            markdown_content = trafilatura.extract(
                downloaded,
                output_format="markdown",
                url=url,  # gives Trafilatura extra context (dates, etc.)
            )
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
