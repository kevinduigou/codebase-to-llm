from __future__ import annotations

from codebase_to_llm.application.ports import DownloadTaskPort
from codebase_to_llm.domain.result import Result


def enqueue_download_youtube_section(
    url: str,
    start: str,
    end: str,
    name: str,
    owner_id: str,
    task_port: DownloadTaskPort,
) -> Result[str, str]:
    return task_port.enqueue_youtube_download(url, start, end, name, owner_id)


def get_download_status(
    task_id: str, task_port: DownloadTaskPort
) -> Result[tuple[str, str | None], str]:
    return task_port.get_task_status(task_id)
