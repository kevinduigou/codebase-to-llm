from __future__ import annotations

import logging
import os
import re
import subprocess
import tempfile
import time
import uuid
from typing_extensions import final

from codebase_to_llm.application.ports import DownloadTaskPort
from codebase_to_llm.application.uc_add_file import AddFileUseCase
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.infrastructure.gcp_file_storage import GCPFileStorage
from codebase_to_llm.infrastructure.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from codebase_to_llm.infrastructure.celery_app import celery_app

logger = logging.getLogger(__name__)


# Progressive MP4 format selection - prefer itag 18/22 and fall back sanely
FORMAT_SELECTION = (
    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/" "best[ext=mp4]/" "18/22/best"
)


def sanitize_filename(name: str, replacement: str = "_", max_length: int = 255) -> str:
    # Normalize type and strip surrounding whitespace
    name = str(name).strip()

    # Replace path separators and control chars
    # Invalid on Windows: <>:"/\\|?* and control chars 0-31
    # On POSIX, only "/" and null are invalid, but we harmonize for cross-platform safety
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, name)

    # Remove trailing dots and spaces (Windows disallows them)
    name = name.rstrip(" .")

    # Collapse multiple replacements
    if replacement:
        # Escape replacement if it has regex special chars
        rep_escaped = re.escape(replacement)
        name = re.sub(rf"{rep_escaped}+", replacement, name)

    # Default to "untitled" if empty
    if not name:
        name = "untitled"

    return name


def _yt_dlp_base_cmd(
    output_file: str, use_proxy: bool, proxy: str | None
) -> tuple[list[str], dict]:
    """Build base yt-dlp command with improved reliability settings."""
    env = os.environ.copy()
    cmd = [
        "yt-dlp",
        "-f",
        FORMAT_SELECTION,
        "-o",
        output_file,  # include .mp4 in output_file
        "--no-playlist",
        "--merge-output-format",
        "mp4",
        "--force-ipv4",
        "--retries",
        "5",
        "--retry-sleep",
        "3",
        "--socket-timeout",
        "30",
        "--fragment-retries",
        "10",
        # These two often help with YT reliability:
        "--extractor-args",
        "youtube:player_client=android,player_skip=webpage",
        "--concurrent-fragments",
        "4",
        "--no-warnings",
        "--quiet",
    ]
    if use_proxy and proxy:
        cmd += ["--proxy", proxy]
        env.update(
            {
                "http_proxy": proxy,
                "https_proxy": proxy,
                "HTTP_PROXY": proxy,
                "HTTPS_PROXY": proxy,
            }
        )
    else:
        for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
            env.pop(k, None)
    return cmd, env


def _is_transient_youtube_error(stderr: str) -> bool:
    """Check if the error is transient and worth retrying."""
    s = stderr.lower()
    patterns = [
        "fragment 1 not found",
        "http error 403",
        "forbidden",
        "connection reset",
        "network is unreachable",
        "timeout",
        "sign in to confirm you're not a bot",
        "this video is drm protected",  # you may choose to return non-retryable instead
    ]
    return any(p in s for p in patterns)


def _download_full_video(
    url: str, output_file: str, proxy: str | None, use_proxy: bool
) -> None:
    """Download the full video without sections."""
    cmd, env = _yt_dlp_base_cmd(output_file, use_proxy, proxy)
    # Note: we REMOVED --download-sections. We grab the full video reliably.
    subprocess.run(
        cmd + [url],
        check=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=600,  # 10 minutes per attempt
    )
    # Occasionally yt-dlp exits 0 but writes nothing (rare, but guard anyway)
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        raise Exception("yt-dlp reported success but no file was created")


def _ffmpeg_cut(input_file: str, output_file: str, start: str, end: str) -> None:
    """Cut video section using ffmpeg with stream copy fallback to re-encode."""
    # First try stream copy (fast, no re-encode). This requires keyframes near cuts.
    copy_cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-ss",
        start,
        "-to",
        end,
        "-i",
        input_file,
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        "-y",
        output_file,
    ]
    r = subprocess.run(copy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (
        r.returncode == 0
        and os.path.exists(output_file)
        and os.path.getsize(output_file) > 0
    ):
        return

    # Fallback to precise re-encode
    reencode_cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-ss",
        start,
        "-to",
        end,
        "-i",
        input_file,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-movflags",
        "+faststart",
        "-y",
        output_file,
    ]
    r2 = subprocess.run(reencode_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (
        r2.returncode != 0
        or not os.path.exists(output_file)
        or os.path.getsize(output_file) == 0
    ):
        raise Exception(
            f"ffmpeg cutting failed.\ncopy_err:\n{r.stderr.decode(errors='ignore')[:500]}\nreencode_err:\n{r2.stderr.decode(errors='ignore')[:500]}"
        )


@celery_app.task(name="download_youtube_section")
def download_youtube_section_task(
    url: str, start: str, end: str, name: str, owner_id: str
) -> str:  # pragma: no cover - worker
    proxy = (
        os.getenv("HTTPS_PROXY_SMARTPROXY") or os.getenv("HTTP_PROXY_SMARTPROXY") or ""
    )
    name = sanitize_filename(name)
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_file = os.path.join(tmpdir, f"{name}.full.mp4")
        cut_file = os.path.join(tmpdir, f"{name}.mp4")

        strategies = [
            ("without_proxy", False),
            ("with_proxy", True),
            ("with_proxy_retry", True),
        ]
        last_error = None
        output_file = cut_file  # Initialize output_file to avoid UnboundLocalError

        for attempt, (strategy_name, use_proxy) in enumerate(strategies, 1):
            try:
                if attempt > 1:
                    delay = min(2 ** (attempt - 1), 30)
                    logger.info(f"Waiting {delay}s before retry…")
                    time.sleep(delay)
                logger.info(
                    f"Download attempt {attempt}/{len(strategies)} using strategy: {strategy_name}"
                )

                try:
                    _download_full_video(url, raw_file, proxy, use_proxy)
                except subprocess.CalledProcessError as e:
                    stderr = (
                        e.stderr.decode("utf-8", errors="ignore") if e.stderr else ""
                    )
                    stdout = (
                        e.stdout.decode("utf-8", errors="ignore") if e.stdout else ""
                    )
                    if _is_transient_youtube_error(stderr):
                        logger.warning(
                            f"yt-dlp transient error on {strategy_name}: {stderr[:300]}"
                        )
                        last_error = Exception(
                            f"transient: {stderr[:300]}\n{stdout[:300]}"
                        )
                        continue
                    else:
                        logger.error(
                            f"yt-dlp non-network error on {strategy_name}: {stderr[:500]}"
                        )
                        raise

                # Cut after we have a stable file
                _ffmpeg_cut(raw_file, cut_file, start, end)
                logger.info(f"Successfully cut section to {cut_file}")
                output_file = cut_file  # for below
                break

            except subprocess.TimeoutExpired:
                msg = f"Download timeout after 10 minutes with strategy {strategy_name}"
                logger.warning(msg)
                last_error = Exception(msg)
                continue

            except Exception as e:
                # Non-transient or ffmpeg failure: record and break (no point retrying different proxy)
                last_error = e
                logger.error(f"Fatal error on strategy {strategy_name}: {e}")
                break
        else:
            logger.error("All download strategies failed")
            if last_error:
                raise last_error
            raise Exception("Download failed with all strategies")

        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            raise Exception("Processing succeeded but output file missing or empty")

        with open(output_file, "rb") as fh:
            content = fh.read()

    # Persist via your use case
    file_id = str(uuid.uuid4())
    file_repo = SqlAlchemyFileRepository()
    storage = GCPFileStorage()
    add_file_use_case = AddFileUseCase(file_repo, storage)

    result = add_file_use_case.execute(
        id_value=file_id,
        owner_id_value=owner_id,
        name=name + ".mp4" if not name.lower().endswith(".mp4") else name,
        content=content,
        directory_id_value=None,
    )
    if result.is_err():  # pragma: no cover - validation/network
        error_msg = result.err() or "Unknown error occurred during file persistence"
        raise Exception(error_msg)

    logger.info(f"Successfully persisted file with ID: {file_id}")
    return file_id


@final
class CeleryDownloadTaskQueue(DownloadTaskPort):
    __slots__ = ()

    def enqueue_youtube_download(
        self, url: str, start: str, end: str, name: str, owner_id: str
    ) -> Result[str, str]:
        try:
            task = download_youtube_section_task.delay(url, start, end, name, owner_id)
            return Ok(task.id)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def get_task_status(self, task_id: str) -> Result[tuple[str, str | None], str]:
        try:
            async_result = celery_app.AsyncResult(task_id)
            status = async_result.status
            if async_result.successful():
                file_id = str(async_result.get())
                return Ok((status, file_id))
            return Ok((status, None))
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
