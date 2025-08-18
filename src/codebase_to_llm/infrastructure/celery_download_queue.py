from __future__ import annotations

import os
import subprocess
import uuid
from typing_extensions import final
from celery import Celery

from codebase_to_llm.application.ports import DownloadTaskPort
from codebase_to_llm.application.uc_add_file import AddFileUseCase
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.infrastructure.gcp_file_storage import GCPFileStorage
from codebase_to_llm.infrastructure.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from codebase_to_llm.config import CONFIG

celery_app = Celery(
    "downloader",
    broker=CONFIG.redis_url,
    backend=CONFIG.redis_url,
)


@celery_app.task(name="download_youtube_section")
def download_youtube_section_task(
    url: str, start: str, end: str, name: str, owner_id: str
) -> str:  # pragma: no cover - worker
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

    # Use AddFileUseCase to properly create and persist the file
    file_id = str(uuid.uuid4())
    file_repo = SqlAlchemyFileRepository()
    storage = GCPFileStorage()
    add_file_use_case = AddFileUseCase(file_repo, storage)

    result = add_file_use_case.execute(
        id_value=file_id,
        owner_id_value=owner_id,
        name=name,
        content=content,
        directory_id_value=None,
    )

    if result.is_err():  # pragma: no cover - validation/network
        raise Exception(result.err())

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
