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
    from .schemas import Timestamp

    key_insights_responses = [
        KeyInsightResponse(
            content=insight.content().value(),
            video_url=insight.video_url().value(),
            begin_timestamp=Timestamp(
                hour=insight.begin_timestamp().hour(),
                minute=insight.begin_timestamp().minute(),
                second=insight.begin_timestamp().second(),
            ),
            end_timestamp=Timestamp(
                hour=insight.end_timestamp().hour(),
                minute=insight.end_timestamp().minute(),
                second=insight.end_timestamp().second(),
            ),
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
        request.video_url,
        model_id_obj.value(),
        user_id,
        request.target_language,
        request.number_of_key_insights,
        task_port,
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
    key_insights_data: list[dict[str, object]] | None = None
    if request.key_insights:
        key_insights_data = [
            {
                "content": insight.content,
                "video_url": insight.video_url,
                "begin_timestamp": {
                    "hour": insight.begin_timestamp.hour,
                    "minute": insight.begin_timestamp.minute,
                    "second": insight.begin_timestamp.second,
                },
                "end_timestamp": {
                    "hour": insight.end_timestamp.hour,
                    "minute": insight.end_timestamp.minute,
                    "second": insight.end_timestamp.second,
                },
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
    from .schemas import Timestamp

    result = get_key_insights_status(task_id, task_port)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    data = result.ok()
    assert data is not None
    status, insights = data

    parsed = None
    if insights:
        parsed = []
        for i in insights:
            # Handle both old string format and new dict format for backward compatibility
            begin_ts = i.get("begin_timestamp", "00:00:00")
            end_ts = i.get("end_timestamp", "00:00:00")

            if isinstance(begin_ts, str):
                # Parse old format "HH:MM:SS" or "MM:SS"
                begin_parts = begin_ts.split(":")
                if len(begin_parts) == 2:
                    begin_hour, begin_minute, begin_second = (
                        0,
                        int(begin_parts[0]),
                        int(begin_parts[1]),
                    )
                elif len(begin_parts) == 3:
                    begin_hour, begin_minute, begin_second = (
                        int(begin_parts[0]),
                        int(begin_parts[1]),
                        int(begin_parts[2]),
                    )
                else:
                    begin_hour, begin_minute, begin_second = 0, 0, 0
            else:
                begin_hour = begin_ts.get("hour", 0)
                begin_minute = begin_ts.get("minute", 0)
                begin_second = begin_ts.get("second", 0)

            if isinstance(end_ts, str):
                # Parse old format "HH:MM:SS" or "MM:SS"
                end_parts = end_ts.split(":")
                if len(end_parts) == 2:
                    end_hour, end_minute, end_second = (
                        0,
                        int(end_parts[0]),
                        int(end_parts[1]),
                    )
                elif len(end_parts) == 3:
                    end_hour, end_minute, end_second = (
                        int(end_parts[0]),
                        int(end_parts[1]),
                        int(end_parts[2]),
                    )
                else:
                    end_hour, end_minute, end_second = 0, 0, 0
            else:
                end_hour = end_ts.get("hour", 0)
                end_minute = end_ts.get("minute", 0)
                end_second = end_ts.get("second", 0)

            parsed.append(
                KeyInsightResponse(
                    content=i.get("content", ""),
                    video_url=i.get("video_url", ""),
                    begin_timestamp=Timestamp(
                        hour=begin_hour, minute=begin_minute, second=begin_second
                    ),
                    end_timestamp=Timestamp(
                        hour=end_hour, minute=end_minute, second=end_second
                    ),
                )
            )

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
    key_insights_data: list[dict[str, object]] | None = None
    if request.key_insights:
        key_insights_data = [
            {
                "content": insight.content,
                "video_url": insight.video_url,
                "begin_timestamp": {
                    "hour": insight.begin_timestamp.hour,
                    "minute": insight.begin_timestamp.minute,
                    "second": insight.begin_timestamp.second,
                },
                "end_timestamp": {
                    "hour": insight.end_timestamp.hour,
                    "minute": insight.end_timestamp.minute,
                    "second": insight.end_timestamp.second,
                },
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
