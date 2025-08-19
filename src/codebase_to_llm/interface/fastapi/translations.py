from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.ports import TranslationTaskPort
from codebase_to_llm.application.uc_translate_video import (
    enqueue_video_translation,
    get_translation_status,
)
from codebase_to_llm.domain.user import User
from .dependencies import get_translation_task_port, get_current_user
from .schemas import TaskStatusResponse, VideoTranslationRequest

router = APIRouter(prefix="/translations", tags=["translations"])


@router.post("/")
def request_video_translation(
    request: VideoTranslationRequest,
    current_user: User = Depends(get_current_user),
    task_port: TranslationTaskPort = Depends(get_translation_task_port),
) -> dict[str, str]:
    if request.file_id is None and request.youtube_url is None:
        raise HTTPException(
            status_code=400, detail="Either file_id or youtube_url must be provided"
        )
    user_id = current_user.id().value()
    result = enqueue_video_translation(
        request.file_id,
        request.youtube_url,
        request.target_language,
        user_id,
        task_port,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    task_id = result.ok()
    assert task_id is not None
    return {"task_id": task_id}


@router.get("/{task_id}", response_model=TaskStatusResponse)
def check_translation_task(
    task_id: str, task_port: TranslationTaskPort = Depends(get_translation_task_port)
) -> TaskStatusResponse:
    result = get_translation_status(task_id, task_port)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    data = result.ok()
    assert data is not None
    status, file_id = data
    return TaskStatusResponse(status=status, file_id=file_id)
