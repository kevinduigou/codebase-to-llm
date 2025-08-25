from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.ports import (
    SummaryTaskPort,
    VideoSummaryRepositoryPort,
)
from codebase_to_llm.application.uc_video_summary_task import (
    enqueue_video_summary_generation,
    get_video_summary_status,
)
from codebase_to_llm.application.uc_add_video_summary import AddVideoSummaryUseCase
from codebase_to_llm.application.uc_get_video_summary import GetVideoSummaryUseCase
from codebase_to_llm.application.uc_list_video_summaries import (
    ListVideoSummariesUseCase,
)
from codebase_to_llm.application.uc_update_video_summary import (
    UpdateVideoSummaryUseCase,
)
from codebase_to_llm.application.uc_delete_video_summary import (
    DeleteVideoSummaryUseCase,
)
from codebase_to_llm.domain.model import ModelId
from codebase_to_llm.domain.user import User
from codebase_to_llm.domain.video_summary import (
    VideoSummary,
    VideoSummaryId,
)
from .dependencies import (
    get_summary_task_port,
    get_current_user,
    get_video_summary_repository,
)
from .schemas import (
    ExtractSummaryRequest,
    SummarySegmentResponse,
    SummaryTaskStatusResponse,
    CreateVideoSummaryRequest,
    UpdateVideoSummaryRequest,
    VideoSummaryResponse,
    Timestamp,
)

router = APIRouter(prefix="/summaries", tags=["summaries"])


def _video_summary_to_response(video_summary: VideoSummary) -> VideoSummaryResponse:
    segments_responses = [
        SummarySegmentResponse(
            content=segment.content().value(),
            video_url=segment.video_url().value(),
            begin_timestamp=Timestamp(
                hour=segment.begin_timestamp().hour(),
                minute=segment.begin_timestamp().minute(),
                second=segment.begin_timestamp().second(),
            ),
            end_timestamp=Timestamp(
                hour=segment.end_timestamp().hour(),
                minute=segment.end_timestamp().minute(),
                second=segment.end_timestamp().second(),
            ),
        )
        for segment in video_summary.segments()
    ]
    return VideoSummaryResponse(
        id=video_summary.video_summary_id().value(),
        title=video_summary.title(),
        segments=segments_responses,
        created_at=video_summary.created_at().isoformat(),
        updated_at=video_summary.updated_at().isoformat(),
    )


@router.post("/")
def request_video_summary(
    request: ExtractSummaryRequest,
    current_user: User = Depends(get_current_user),
    task_port: SummaryTaskPort = Depends(get_summary_task_port),
) -> dict[str, str]:
    model_id_result = ModelId.try_create(request.model_id)
    if model_id_result.is_err():
        raise HTTPException(status_code=400, detail=model_id_result.err())
    model_id_obj = model_id_result.ok()
    assert model_id_obj is not None
    user_id = current_user.id().value()
    result = enqueue_video_summary_generation(
        request.video_url, model_id_obj.value(), user_id, task_port
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    task_id = result.ok()
    assert task_id is not None
    return {"task_id": task_id}


@router.get("/{task_id}", response_model=SummaryTaskStatusResponse)
def check_video_summary_task(
    task_id: str, task_port: SummaryTaskPort = Depends(get_summary_task_port)
) -> SummaryTaskStatusResponse:
    result = get_video_summary_status(task_id, task_port)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    data = result.ok()
    assert data is not None
    status, segments = data
    parsed = None
    if segments:
        parsed = []
        for s in segments:
            begin_ts: object = s.get("begin_timestamp", {})
            end_ts: object = s.get("end_timestamp", {})
            if isinstance(begin_ts, dict):
                begin_hour = int(begin_ts.get("hour", 0))
                begin_minute = int(begin_ts.get("minute", 0))
                begin_second = int(begin_ts.get("second", 0))
            else:
                begin_hour = begin_minute = begin_second = 0
            if isinstance(end_ts, dict):
                end_hour = int(end_ts.get("hour", 0))
                end_minute = int(end_ts.get("minute", 0))
                end_second = int(end_ts.get("second", 0))
            else:
                end_hour = end_minute = end_second = 0
            parsed.append(
                SummarySegmentResponse(
                    content=str(s.get("content", "")),
                    video_url=str(s.get("video_url", "")),
                    begin_timestamp=Timestamp(
                        hour=begin_hour,
                        minute=begin_minute,
                        second=begin_second,
                    ),
                    end_timestamp=Timestamp(
                        hour=end_hour,
                        minute=end_minute,
                        second=end_second,
                    ),
                )
            )
    return SummaryTaskStatusResponse(status=status, segments=parsed)


@router.post("/video-summaries", response_model=VideoSummaryResponse)
def create_video_summary(
    request: CreateVideoSummaryRequest,
    current_user: User = Depends(get_current_user),
    repo: VideoSummaryRepositoryPort = Depends(get_video_summary_repository),
) -> VideoSummaryResponse:
    id_value = VideoSummaryId.generate().value()
    owner_id_value = current_user.id().value()
    segments_data: list[dict[str, object]] | None = None
    if request.segments:
        segments_data = []
        for seg in request.segments:
            segments_data.append(
                {
                    "content": seg.content,
                    "video_url": seg.video_url,
                    "begin_timestamp": {
                        "hour": seg.begin_timestamp.hour,
                        "minute": seg.begin_timestamp.minute,
                        "second": seg.begin_timestamp.second,
                    },
                    "end_timestamp": {
                        "hour": seg.end_timestamp.hour,
                        "minute": seg.end_timestamp.minute,
                        "second": seg.end_timestamp.second,
                    },
                }
            )
    use_case = AddVideoSummaryUseCase(repo)
    result = use_case.execute(id_value, owner_id_value, request.title, segments_data)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    video_summary = result.ok()
    assert video_summary is not None
    return _video_summary_to_response(video_summary)


@router.get("/video-summaries/{video_summary_id}", response_model=VideoSummaryResponse)
def get_video_summary(
    video_summary_id: str,
    current_user: User = Depends(get_current_user),
    repo: VideoSummaryRepositoryPort = Depends(get_video_summary_repository),
) -> VideoSummaryResponse:
    use_case = GetVideoSummaryUseCase(repo)
    result = use_case.execute(video_summary_id)
    if result.is_err():
        raise HTTPException(status_code=404, detail=result.err())
    video_summary = result.ok()
    assert video_summary is not None
    if video_summary.owner_id().value() != current_user.id().value():
        raise HTTPException(status_code=403, detail="Access denied")
    return _video_summary_to_response(video_summary)


@router.get("/all-video-summaries", response_model=list[VideoSummaryResponse])
def list_video_summaries(
    current_user: User = Depends(get_current_user),
    repo: VideoSummaryRepositoryPort = Depends(get_video_summary_repository),
) -> list[VideoSummaryResponse]:
    use_case = ListVideoSummariesUseCase(repo)
    result = use_case.execute(current_user.id().value())
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    video_summaries = result.ok()
    assert video_summaries is not None
    return [_video_summary_to_response(vs) for vs in video_summaries]


@router.put("/video-summaries/{video_summary_id}", response_model=VideoSummaryResponse)
def update_video_summary(
    video_summary_id: str,
    request: UpdateVideoSummaryRequest,
    current_user: User = Depends(get_current_user),
    repo: VideoSummaryRepositoryPort = Depends(get_video_summary_repository),
) -> VideoSummaryResponse:
    get_use_case = GetVideoSummaryUseCase(repo)
    get_result = get_use_case.execute(video_summary_id)
    if get_result.is_err():
        raise HTTPException(status_code=404, detail=get_result.err())
    existing = get_result.ok()
    assert existing is not None
    if existing.owner_id().value() != current_user.id().value():
        raise HTTPException(status_code=403, detail="Access denied")
    segments_data: list[dict[str, object]] | None = None
    if request.segments:
        segments_data = []
        for seg in request.segments:
            segments_data.append(
                {
                    "content": seg.content,
                    "video_url": seg.video_url,
                    "begin_timestamp": {
                        "hour": seg.begin_timestamp.hour,
                        "minute": seg.begin_timestamp.minute,
                        "second": seg.begin_timestamp.second,
                    },
                    "end_timestamp": {
                        "hour": seg.end_timestamp.hour,
                        "minute": seg.end_timestamp.minute,
                        "second": seg.end_timestamp.second,
                    },
                }
            )
    use_case = UpdateVideoSummaryUseCase(repo)
    result = use_case.execute(video_summary_id, request.title, segments_data)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    video_summary = result.ok()
    assert video_summary is not None
    return _video_summary_to_response(video_summary)


@router.delete("/video-summaries/{video_summary_id}")
def delete_video_summary(
    video_summary_id: str,
    current_user: User = Depends(get_current_user),
    repo: VideoSummaryRepositoryPort = Depends(get_video_summary_repository),
) -> dict[str, str]:
    get_use_case = GetVideoSummaryUseCase(repo)
    get_result = get_use_case.execute(video_summary_id)
    if get_result.is_err():
        raise HTTPException(status_code=404, detail=get_result.err())
    existing = get_result.ok()
    assert existing is not None
    if existing.owner_id().value() != current_user.id().value():
        raise HTTPException(status_code=403, detail="Access denied")
    use_case = DeleteVideoSummaryUseCase(repo)
    result = use_case.execute(video_summary_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"message": "VideoSummary deleted successfully"}
