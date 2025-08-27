from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application import (
    uc_create_video_subtitle,
    uc_get_video_subtitle,
    uc_update_video_subtitle,
    uc_delete_video_subtitle,
)
from codebase_to_llm.domain.user import User

from .dependencies import get_current_user, get_video_subtitle_repo
from .schemas import (
    VideoSubtitleCreateRequest,
    VideoSubtitleUpdateRequest,
    VideoSubtitleResponse,
)

router = APIRouter(prefix="/video_subtitles", tags=["Video Subtitles"])


@router.post("/", summary="Create association")
def create_association(
    request: VideoSubtitleCreateRequest,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_video_subtitle_repo),
) -> VideoSubtitleResponse:
    assoc_id = str(uuid.uuid4())
    result = uc_create_video_subtitle.execute(
        assoc_id, request.video_file_id, request.subtitle_file_id, repo
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    assoc = result.ok()
    assert assoc is not None
    return VideoSubtitleResponse(
        id=assoc.id().value(),
        video_file_id=assoc.video_file_id().value(),
        subtitle_file_id=assoc.subtitle_file_id().value(),
    )


@router.get("/{association_id}", summary="Get association")
def get_association(
    association_id: str,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_video_subtitle_repo),
) -> VideoSubtitleResponse:
    result = uc_get_video_subtitle.execute(association_id, repo)
    if result.is_err():
        raise HTTPException(status_code=404, detail=result.err())
    assoc = result.ok()
    assert assoc is not None
    return VideoSubtitleResponse(
        id=assoc.id().value(),
        video_file_id=assoc.video_file_id().value(),
        subtitle_file_id=assoc.subtitle_file_id().value(),
    )


@router.put("/{association_id}", summary="Update association")
def update_association(
    association_id: str,
    request: VideoSubtitleUpdateRequest,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_video_subtitle_repo),
) -> dict[str, str]:
    result = uc_update_video_subtitle.execute(
        association_id, request.subtitle_file_id, repo
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "updated"}


@router.delete("/{association_id}", summary="Delete association")
def delete_association(
    association_id: str,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_video_subtitle_repo),
) -> dict[str, str]:
    result = uc_delete_video_subtitle.execute(association_id, repo)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "deleted"}
