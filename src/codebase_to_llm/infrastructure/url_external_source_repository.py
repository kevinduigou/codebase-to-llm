from __future__ import annotations

import os
import re
from typing import Final

import httpx
import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    TranscriptsDisabled,
    RequestBlocked,
    IpBlocked,
)

from codebase_to_llm.application.ports import ExternalSourceRepositoryPort
from codebase_to_llm.domain.result import Err, Ok, Result


class UrlExternalSourceRepository(ExternalSourceRepositoryPort):
    """
    Fetches web pages or YouTube transcripts.

    *   Adds a proxy layer for YouTube requests.
    *   Fixes the Trafilatura one-shot fallback.
    """

    __slots__ = ()

    # ── Configuration --------------------------------------------------------

    #: read once at import time; you can also inject this in __init__ instead
    PROXIES: Final[dict[str, str]] = {
        "http": os.getenv(
            "HTTP_PROXY_SMARTPROXY", ""
        ),  # e.g. http://user:pass@host:port
        "https": os.getenv(
            "HTTPS_PROXY_SMARTPROXY", ""
        ),  # e.g. http://user:pass@host:port
    }
    LANGUAGES: Final[list[str]] = ["en", "fr"]

    # ── Public methods -------------------------------------------------------

    def fetch_web_page(self, url: str) -> Result[str, str]:
        """
        Return Markdown extracted from `url`.

        Trafilatura strategy:
        1.  try `fetch_url` + `extract`
        2.  one-shot helper (`extract(url=...)`)
        3.  manual HTTP download + `extract`
        """
        try:
            # 1️⃣  Normal path
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                markdown = trafilatura.extract(
                    downloaded, output_format="markdown", url=url
                )
                if markdown:
                    return Ok(markdown)

            # 2️⃣  One-shot helper (this was the bug: you passed None before)
            markdown = trafilatura.extract(None, url=url, output_format="markdown")
            if markdown:
                return Ok(markdown)

            # 3️⃣  Manual download fallback
            ua = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            )
            resp = httpx.get(
                url,
                headers={"User-Agent": ua},
                follow_redirects=True,
                timeout=10,
            )
            resp.raise_for_status()
            markdown = trafilatura.extract(resp.text, output_format="markdown", url=url)
            if markdown:
                return Ok(markdown)

            return Err("Trafilatura could not extract anything from the page.")

        except Exception as exc:  # noqa: BLE001
            return Err(f"fetch_web_page failed: {exc}")

    def fetch_youtube_transcript(self, url: str) -> Result[str, str]:
        """
        Return plain-text transcript for a YouTube video.

        Adds proxy support and clearer error handling.
        """
        try:
            video_id = _extract_video_id(url)

            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=self.LANGUAGES,
                proxies=self.PROXIES,
            )
            lines = [item["text"] for item in transcript]
            return Ok("\n".join(lines))

        except (RequestBlocked, IpBlocked):
            return Err("YouTube blocked this request/IP. Switch proxy or slow down.")
        except TranscriptsDisabled:
            return Err("The uploader disabled transcripts for this video.")
        except CouldNotRetrieveTranscript as exc:
            return Err(f"Could not retrieve transcript: {exc}")
        except Exception as exc:  # noqa: BLE001
            return Err(f"Unexpected transcript error: {exc}")


def _extract_video_id(url: str) -> str:
    match = re.search(r"(?:v=|/)([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)
    return url
