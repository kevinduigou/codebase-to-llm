from __future__ import annotations

import os
import re
import time
import random
from typing import Final
from xml.parsers import expat

import httpx
import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    TranscriptsDisabled,
    RequestBlocked,
    IpBlocked,
    NoTranscriptFound,
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

    def fetch_youtube_transcript(
        self, url: str, include_timestamps: bool = False
    ) -> Result[str, str]:
        """
        Return plain-text transcript for a YouTube video.

        Adds proxy support, clearer error handling, and optional timestamps.
        """
        try:
            video_id = _extract_video_id(url)
            transcript_from_yt_api = []
            language = "en"  # Start with English

            # Retry logic with language fallback
            for attempt in range(3):
                try:
                    # Only pass proxies if they are actually configured
                    if self.PROXIES.get("http") or self.PROXIES.get("https"):
                        transcript_from_yt_api = YouTubeTranscriptApi.get_transcript(
                            video_id=video_id,
                            languages=[language],
                            proxies=self.PROXIES,
                        )
                    else:
                        transcript_from_yt_api = YouTubeTranscriptApi.get_transcript(
                            video_id=video_id,
                            languages=[language],
                        )
                    break
                except (TranscriptsDisabled, NoTranscriptFound):
                    # Nothing to do – captions really don't exist
                    print(
                        f"No transcript available for language {language}, trying alternative language"
                    )
                    if language == "en":
                        language = "fr"
                    elif language == "fr":
                        language = "en"
                    else:
                        # If not en or fr, try en as fallback
                        language = "en"
                except expat.ExpatError as e:
                    # Empty or corrupt XML → wait a bit, then retry
                    print(f"XML parsing error (attempt {attempt + 1}/3): {e}")
                    if attempt < 2:  # Only sleep if we have more attempts
                        time.sleep(2 + random.random())
                    else:
                        print(
                            "Failed to parse transcript XML after 3 attempts, falling back to audio transcription"
                        )
                        break
                except CouldNotRetrieveTranscript as e:
                    # Frequently raised when YouTube returns a consent/rate-limit page
                    print(f"Rate-limited (attempt {attempt + 1}/3): {e}. Retrying …")
                    if attempt < 2:  # Only sleep if we have more attempts
                        time.sleep(5 + random.random())
                    else:
                        print(
                            "Failed to retrieve transcript after 3 attempts, falling back to audio transcription"
                        )
                        break
                except Exception as e:
                    print(
                        f"Error fetching transcript from YouTube API for video {video_id} (attempt {attempt + 1}/3): {e}"
                    )
                    if attempt < 2:  # Only sleep if we have more attempts
                        time.sleep(2 + random.random())
                    else:
                        print(
                            "Failed to fetch transcript after 3 attempts, falling back to audio transcription"
                        )
                        break

            if not transcript_from_yt_api:
                return Err("Could not retrieve transcript after multiple attempts")

            # Format transcript with or without timestamps
            transcriptions = []
            for segment in transcript_from_yt_api:
                if include_timestamps:
                    timestamp = _seconds_to_min_sec(segment["start"])
                    transcriptions.append(f"{timestamp}:{segment['text']}")
                else:
                    transcriptions.append(segment["text"])

            transcript = "\n".join(transcriptions)
            return Ok(transcript)

        except (RequestBlocked, IpBlocked):
            return Err("YouTube blocked this request/IP. Switch proxy or slow down.")
        except TranscriptsDisabled:
            return Err("The uploader disabled transcripts for this video.")
        except Exception as exc:  # noqa: BLE001
            return Err(f"Unexpected transcript error: {exc}")


def _extract_video_id(url: str) -> str:
    match = re.search(r"(?:v=|/)([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)
    return url


def _seconds_to_min_sec(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    minutes = int(seconds // 60)
    seconds_remainder = int(seconds % 60)
    return f"{minutes:02d}:{seconds_remainder:02d}"
