from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.ports import (
    KeyInsightsTaskPort,
    VideoKeyInsightsRepositoryPort,
)
from codebase_to_llm.application.uc_key_insights_task import (
    enqueue_key_insights_extraction,
    get_key_insights_status,
)
from codebase_to_llm.application.uc_add_video_key_insights import (
    AddVideoKeyInsightsUseCase,
)
from codebase_to_llm.application.uc_get_video_key_insights import (
    GetVideoKeyInsightsUseCase,
)
from codebase_to_llm.application.uc_list_video_key_insights import (
    ListVideoKeyInsightsUseCase,
)
from codebase_to_llm.application.uc_update_video_key_insights import (
    UpdateVideoKeyInsightsUseCase,
)
from codebase_to_llm.application.uc_delete_video_key_insights import (
    DeleteVideoKeyInsightsUseCase,
)
from codebase_to_llm.domain.model import ModelId
from codebase_to_llm.domain.user import User
from codebase_to_llm.domain.video_key_insights import (
    VideoKeyInsights,
    VideoKeyInsightId,
)
from .dependencies import (
    get_key_insights_task_port,
    get_current_user,
    get_video_key_insights_repository,
)
from .schemas import (
    ExtractKeyInsightsRequest,
    KeyInsightResponse,
    KeyInsightsTaskStatusResponse,
    CreateVideoKeyInsightsRequest,
    UpdateVideoKeyInsightsRequest,
    VideoKeyInsightsResponse,
)

router = APIRouter(prefix="/key-insights", tags=["key-insights"])


def _video_key_insights_to_response(
    video_key_insights: VideoKeyInsights,
) -> VideoKeyInsightsResponse:
    """Convert VideoKeyInsights domain object to response schema."""
    key_insights_responses = [
        KeyInsightResponse(
            content=insight.content().value(),
            video_url=insight.video_url().value(),
            begin_timestamp=insight.begin_timestamp().value(),
            end_timestamp=insight.end_timestamp().value(),
        )
        for insight in video_key_insights.key_insights()
    ]

    return VideoKeyInsightsResponse(
        id=video_key_insights.video_key_insight_id().value(),
        title=video_key_insights.title(),
        key_insights=key_insights_responses,
        created_at=video_key_insights.created_at().isoformat(),
        updated_at=video_key_insights.updated_at().isoformat(),
    )


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


# VideoKeyInsights CRUD routes
@router.post("/video-key-insights", response_model=VideoKeyInsightsResponse)
def create_video_key_insights(
    request: CreateVideoKeyInsightsRequest,
    current_user: User = Depends(get_current_user),
    repo: VideoKeyInsightsRepositoryPort = Depends(get_video_key_insights_repository),
) -> VideoKeyInsightsResponse:
    """Create new VideoKeyInsights."""
    # Generate a new ID
    id_value = VideoKeyInsightId.generate().value()
    owner_id_value = current_user.id().value()

    # Convert request key insights to dict format
    key_insights_data = None
    if request.key_insights:
        key_insights_data = [
            {
                "content": insight.content,
                "video_url": insight.video_url,
                "begin_timestamp": insight.begin_timestamp,
                "end_timestamp": insight.end_timestamp,
            }
            for insight in request.key_insights
        ]

    use_case = AddVideoKeyInsightsUseCase(repo)
    result = use_case.execute(
        id_value, owner_id_value, request.title, key_insights_data
    )

    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())

    video_key_insights = result.ok()
    assert video_key_insights is not None
    return _video_key_insights_to_response(video_key_insights)


@router.get("/all-video-key-insights", response_model=list[VideoKeyInsightsResponse])
def list_video_key_insights(
    current_user: User = Depends(get_current_user),
    repo: VideoKeyInsightsRepositoryPort = Depends(get_video_key_insights_repository),
) -> list[VideoKeyInsightsResponse]:
    """List all VideoKeyInsights for the current user."""
    use_case = ListVideoKeyInsightsUseCase(repo)
    result = use_case.execute(current_user.id().value())

    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())

    video_key_insights_list = result.ok()
    assert video_key_insights_list is not None
    return [_video_key_insights_to_response(vki) for vki in video_key_insights_list]
    return []


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


@router.get(
    "/video-key-insights/{video_key_insights_id}",
    response_model=VideoKeyInsightsResponse,
)
def get_video_key_insights(
    video_key_insights_id: str,
    current_user: User = Depends(get_current_user),
    repo: VideoKeyInsightsRepositoryPort = Depends(get_video_key_insights_repository),
) -> VideoKeyInsightsResponse:
    """Get specific VideoKeyInsights by ID."""
    use_case = GetVideoKeyInsightsUseCase(repo)
    result = use_case.execute(video_key_insights_id)

    if result.is_err():
        raise HTTPException(status_code=404, detail=result.err())

    video_key_insights = result.ok()
    assert video_key_insights is not None

    # Check if the user owns this VideoKeyInsights
    if video_key_insights.owner_id().value() != current_user.id().value():
        raise HTTPException(status_code=403, detail="Access denied")

    return _video_key_insights_to_response(video_key_insights)


@router.put(
    "/video-key-insights/{video_key_insights_id}",
    response_model=VideoKeyInsightsResponse,
)
def update_video_key_insights(
    video_key_insights_id: str,
    request: UpdateVideoKeyInsightsRequest,
    current_user: User = Depends(get_current_user),
    repo: VideoKeyInsightsRepositoryPort = Depends(get_video_key_insights_repository),
) -> VideoKeyInsightsResponse:
    """Update VideoKeyInsights."""
    # First check if the user owns this VideoKeyInsights
    get_use_case = GetVideoKeyInsightsUseCase(repo)
    get_result = get_use_case.execute(video_key_insights_id)

    if get_result.is_err():
        raise HTTPException(status_code=404, detail=get_result.err())

    existing = get_result.ok()
    assert existing is not None

    if existing.owner_id().value() != current_user.id().value():
        raise HTTPException(status_code=403, detail="Access denied")

    # Convert request key insights to dict format
    key_insights_data = None
    if request.key_insights:
        key_insights_data = [
            {
                "content": insight.content,
                "video_url": insight.video_url,
                "begin_timestamp": insight.begin_timestamp,
                "end_timestamp": insight.end_timestamp,
            }
            for insight in request.key_insights
        ]

    use_case = UpdateVideoKeyInsightsUseCase(repo)
    result = use_case.execute(video_key_insights_id, request.title, key_insights_data)

    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())

    video_key_insights = result.ok()
    assert video_key_insights is not None
    return _video_key_insights_to_response(video_key_insights)


@router.delete("/video-key-insights/{video_key_insights_id}")
def delete_video_key_insights(
    video_key_insights_id: str,
    current_user: User = Depends(get_current_user),
    repo: VideoKeyInsightsRepositoryPort = Depends(get_video_key_insights_repository),
) -> dict[str, str]:
    """Delete VideoKeyInsights."""
    # First check if the user owns this VideoKeyInsights
    get_use_case = GetVideoKeyInsightsUseCase(repo)
    get_result = get_use_case.execute(video_key_insights_id)

    if get_result.is_err():
        raise HTTPException(status_code=404, detail=get_result.err())

    existing = get_result.ok()
    assert existing is not None

    if existing.owner_id().value() != current_user.id().value():
        raise HTTPException(status_code=403, detail="Access denied")

    use_case = DeleteVideoKeyInsightsUseCase(repo)
    result = use_case.execute(video_key_insights_id)

    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())

    return {"message": "VideoKeyInsights deleted successfully"}
