from __future__ import annotations

import os
import subprocess
import uuid
from typing_extensions import final
from celery import Celery

from codebase_to_llm.application.ports import DownloadTaskPort
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.stored_file import StoredFile
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.infrastructure.gcp_file_storage import GCPFileStorage
from codebase_to_llm.config import CONFIG

celery_app = Celery(
    "downloader",
    broker=CONFIG.redis_url,
    backend=CONFIG.redis_url,
)


@celery_app.task(name="download_youtube_section")
def download_youtube_section_task(url: str, start: str, end: str) -> str:  # pragma: no cover - worker
    proxies = {
        "HTTP_PROXY": os.getenv("HTTP_PROXY_SMARTPROXY", ""),
        "HTTPS_PROXY": os.getenv("HTTPS_PROXY_SMARTPROXY", ""),
    }
    output_file = "output.mp4"
    section = f"*{start}-{end}"
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
        url,
    ]
    env = {**os.environ, **proxies}
    subprocess.run(cmd, check=True, env=env)
    with open(output_file, "rb") as fh:
        content = fh.read()
    user_id_result = UserId.try_create("downloader")
    if user_id_result.is_err():  # pragma: no cover - validation
        raise Exception(user_id_result.err())
    user_id = user_id_result.ok()
    assert user_id is not None
    file_id = str(uuid.uuid4())
    stored_file_result = StoredFile.try_create(file_id, user_id, output_file)
    if stored_file_result.is_err():  # pragma: no cover - validation
        raise Exception(stored_file_result.err())
    stored_file = stored_file_result.ok()
    assert stored_file is not None
    storage = GCPFileStorage()
    save_result = storage.save(stored_file, content)
    if save_result.is_err():  # pragma: no cover - network
        raise Exception(save_result.err())
    return file_id


@final
class CeleryDownloadTaskQueue(DownloadTaskPort):
    __slots__ = ()

    def enqueue_youtube_download(
        self, url: str, start: str, end: str
    ) -> Result[str, str]:
        try:
            task = download_youtube_section_task.delay(url, start, end)
            return Ok(task.id)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def get_task_status(
        self, task_id: str
    ) -> Result[tuple[str, str | None], str]:
        try:
            async_result = celery_app.AsyncResult(task_id)
            status = async_result.status
            if async_result.successful():
                file_id = str(async_result.get())
                return Ok((status, file_id))
            return Ok((status, None))
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
