from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.uc_download_youtube_section import (
    enqueue_download_youtube_section,
    get_download_status,
)
from codebase_to_llm.application.ports import DownloadTaskPort
from .dependencies import get_download_task_port
from .schemas import TaskStatusResponse, YouTubeDownloadRequest

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.post("/youtube")
def request_youtube_download(
    request: YouTubeDownloadRequest,
    task_port: DownloadTaskPort = Depends(get_download_task_port),
) -> dict[str, str]:
    result = enqueue_download_youtube_section(
        request.url, request.start, request.end, task_port
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    task_id = result.ok()
    assert task_id is not None
    return {"task_id": task_id}


@router.get("/youtube/{task_id}", response_model=TaskStatusResponse)
def check_youtube_download(
    task_id: str, task_port: DownloadTaskPort = Depends(get_download_task_port)
) -> TaskStatusResponse:
    result = get_download_status(task_id, task_port)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    status, file_id = result.ok()
    assert status is not None
    return TaskStatusResponse(status=status, file_id=file_id)
