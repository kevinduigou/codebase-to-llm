from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.ports import KeyInsightsTaskPort
from codebase_to_llm.application.uc_key_insights_task import (
    enqueue_key_insights_extraction,
    get_key_insights_status,
)
from codebase_to_llm.domain.model import ModelId
from codebase_to_llm.domain.user import User
from .dependencies import get_key_insights_task_port, get_current_user
from .schemas import (
    ExtractKeyInsightsRequest,
    KeyInsightResponse,
    KeyInsightsTaskStatusResponse,
)

router = APIRouter(prefix="/key-insights", tags=["key-insights"])


@router.post("/")
def request_key_insights(
    request: ExtractKeyInsightsRequest,
    current_user: User = Depends(get_current_user),
    task_port: KeyInsightsTaskPort = Depends(get_key_insights_task_port),
) -> dict[str, str]:
    model_id_result = ModelId.try_create(request.model_id)
    if model_id_result.is_err():
        raise HTTPException(status_code=400, detail=model_id_result.err())
    model_id_obj = model_id_result.ok()
    assert model_id_obj is not None
    user_id = current_user.id().value()
    result = enqueue_key_insights_extraction(
        request.video_url, model_id_obj.value(), user_id, task_port
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    task_id = result.ok()
    assert task_id is not None
    return {"task_id": task_id}


@router.get("/{task_id}", response_model=KeyInsightsTaskStatusResponse)
def check_key_insights_task(
    task_id: str, task_port: KeyInsightsTaskPort = Depends(get_key_insights_task_port)
) -> KeyInsightsTaskStatusResponse:
    result = get_key_insights_status(task_id, task_port)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    data = result.ok()
    assert data is not None
    status, insights = data
    parsed = [KeyInsightResponse(**i) for i in insights] if insights else None
    return KeyInsightsTaskStatusResponse(status=status, insights=parsed)
