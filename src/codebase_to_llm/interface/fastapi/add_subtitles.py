from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.ports import AddSubtitleTaskPort
from codebase_to_llm.application.uc_add_subtitle_to_video import (
    enqueue_video_add_subtitles,
    get_add_subtitles_status,
)
from codebase_to_llm.domain.user import User
from .dependencies import get_add_subtitles_task_port, get_current_user
from .schemas import TaskStatusResponse, VideoAddSubtitleRequest

router = APIRouter(prefix="/add_subtitles", tags=["add_subtitles"])


@router.post("/")
def request_video_add_subtitles(
    request: VideoAddSubtitleRequest,
    current_user: User = Depends(get_current_user),
    task_port: AddSubtitleTaskPort = Depends(get_add_subtitles_task_port),
) -> dict[str, str]:
    user_id = current_user.id().value()
    result = enqueue_video_add_subtitles(
        request.file_id,
        request.origin_language,
        request.target_language,
        user_id,
        request.output_filename,
        task_port,
        request.subtitle_color,
        request.subtitle_style,
        request.use_soft_subtitles,
        request.font_size_percentage,
        request.margin_percentage,
        request.subtitle_format,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    task_id = result.ok()
    assert task_id is not None
    return {"task_id": task_id}


@router.get("/{task_id}", response_model=TaskStatusResponse)
def check_add_subtitles_task(
    task_id: str, task_port: AddSubtitleTaskPort = Depends(get_add_subtitles_task_port)
) -> TaskStatusResponse:
    result = get_add_subtitles_status(task_id, task_port)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    data = result.ok()
    assert data is not None
    status, file_id = data
    return TaskStatusResponse(status=status, file_id=file_id)
