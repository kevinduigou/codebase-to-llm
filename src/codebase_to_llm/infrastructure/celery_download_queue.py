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


def _try_download_with_config(
    url: str,
    output_file: str,
    section: str,
    proxy: str | None = None,
    use_proxy: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    """Try to download with specific configuration."""
    env = os.environ.copy()

    cmd = [
        "yt-dlp",
        "-f",
        "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[vcodec^=avc1][acodec^=mp4a]",
        "-o",
        output_file,
        "--merge-output-format",
        "mp4",
        "--download-sections",
        section,
        "--force-ipv4",
        "--retries",
        "5",
        "--retry-sleep",
        "3",
        "--user-agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--socket-timeout",
        "30",
        "--fragment-retries",
        "10",
    ]

    # Configure proxy if requested and available
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
        # Clear proxy environment variables for direct connection
        for proxy_var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
            env.pop(proxy_var, None)

    logger.info(
        f"Attempting download with proxy={'enabled' if use_proxy and proxy else 'disabled'}"
    )

    return subprocess.run(
        cmd + [url],
        check=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,  # 30 second timeout
    )


@celery_app.task(name="download_youtube_section")
def download_youtube_section_task(
    url: str, start: str, end: str, name: str, owner_id: str
) -> str:  # pragma: no cover - worker
    proxy = (
        os.getenv("HTTPS_PROXY_SMARTPROXY") or os.getenv("HTTP_PROXY_SMARTPROXY") or ""
    )
    name = sanitize_filename(name)
    section = f"*{start}-{end}"

    # Safer temp file so concurrent tasks don't collide
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, f"{name}.mp4")

        # Try multiple download strategies with exponential backoff
        strategies = [
            ("without_proxy", False),
            ("with_proxy", True),
            ("with_proxy_retry", True),
        ]

        last_error = None

        for attempt, (strategy_name, use_proxy) in enumerate(strategies, 1):
            try:
                logger.info(
                    f"Download attempt {attempt}/{len(strategies)} using strategy: {strategy_name}"
                )

                # Add delay between attempts (exponential backoff)
                if attempt > 1:
                    delay = min(2 ** (attempt - 1), 30)  # Cap at 30 seconds
                    logger.info(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)

                _try_download_with_config(url, output_file, section, proxy, use_proxy)
                logger.info(f"Download successful with strategy: {strategy_name}")
                break

            except subprocess.TimeoutExpired:
                error_msg = (
                    f"Download timeout after 10 minutes with strategy {strategy_name}"
                )
                logger.warning(error_msg)
                last_error = Exception(error_msg)
                continue

            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode("utf-8", errors="ignore") if e.stderr else ""
                stdout = e.stdout.decode("utf-8", errors="ignore") if e.stdout else ""

                # Check if it's a network/proxy related error
                is_network_error = any(
                    error_pattern in stderr.lower()
                    for error_pattern in [
                        "input/output error",
                        "stream ends prematurely",
                        "error in the pull function",
                        "connection reset",
                        "network is unreachable",
                        "timeout",
                    ]
                )

                error_msg = (
                    f"yt-dlp failed with strategy {strategy_name} (code {e.returncode})"
                )
                if is_network_error:
                    logger.warning(
                        f"{error_msg} - Network error detected, will try next strategy"
                    )
                else:
                    logger.error(f"{error_msg} - Non-network error: {stderr[:500]}")

                last_error = Exception(
                    f"{error_msg}. STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                )

                # If it's not a network error, don't retry with other strategies
                if not is_network_error:
                    break

                continue

        else:
            # All strategies failed
            logger.error("All download strategies failed")
            if last_error:
                raise last_error
            raise Exception("Download failed with all strategies")

        # Verify file was created and has content
        if not os.path.exists(output_file):
            raise Exception(
                "Download appeared successful but output file was not created"
            )

        file_size = os.path.getsize(output_file)
        if file_size == 0:
            raise Exception("Download created empty file")

        logger.info(f"Successfully downloaded {file_size} bytes to {output_file}")

        # Read result
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
        raise Exception(result.err())

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
