from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.ports import BurnAssTaskPort
from codebase_to_llm.application.uc_burn_ass_to_video import (
    enqueue_burn_ass_subtitle,
    get_burn_ass_status,
)
from codebase_to_llm.domain.user import User
from .dependencies import get_burn_ass_task_port, get_current_user
from .schemas import BurnAssRequest, TaskStatusResponse

router = APIRouter(prefix="/burn_ass", tags=["burn_ass"])


@router.post("/video/{video_file_id}")
def request_burn_ass(
    video_file_id: str,
    request: BurnAssRequest,
    current_user: User = Depends(get_current_user),
    task_port: BurnAssTaskPort = Depends(get_burn_ass_task_port),
) -> dict[str, str]:
    owner_id = current_user.id().value()
    result = enqueue_burn_ass_subtitle(
        video_file_id, request.output_filename, owner_id, task_port
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    task_id = result.ok()
    assert task_id is not None
    return {"task_id": task_id}


@router.get("/{task_id}", response_model=TaskStatusResponse)
def check_burn_ass_task(
    task_id: str, task_port: BurnAssTaskPort = Depends(get_burn_ass_task_port)
) -> TaskStatusResponse:
    result = get_burn_ass_status(task_id, task_port)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    data = result.ok()
    assert data is not None
    status, file_id = data
    return TaskStatusResponse(status=status, file_id=file_id)
