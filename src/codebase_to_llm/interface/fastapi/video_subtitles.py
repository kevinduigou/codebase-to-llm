from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application import (
    uc_get_ass_file_by_video_id,
)
from codebase_to_llm.domain.user import User

from .dependencies import (
    get_current_user,
    get_video_subtitle_repo,
    get_file_repo,
    get_file_storage,
)
from .schemas import (
    VideoSubtitleCreateRequest,
    VideoSubtitleUpdateRequest,
    VideoSubtitleResponse,
    AssFileResponse,
)

router = APIRouter(prefix="/video_subtitles", tags=["Video Subtitles"])


@router.get("/video/{video_file_id}/ass", summary="Get ASS file by video ID")
def get_ass_file_by_video_id(
    video_file_id: str,
    current_user: User = Depends(get_current_user),
    video_subtitle_repo=Depends(get_video_subtitle_repo),
    file_repo=Depends(get_file_repo),
    file_storage=Depends(get_file_storage),
) -> AssFileResponse:
    """Get the ASS subtitle file ID and content for a given video file ID."""
    result = uc_get_ass_file_by_video_id.execute(
        video_file_id, video_subtitle_repo, file_repo, file_storage
    )
    if result.is_err():
        raise HTTPException(status_code=404, detail=result.err())
    result_data = result.ok()
    assert result_data is not None
    subtitle_file_id, content = result_data
    return AssFileResponse(subtitle_file_id=subtitle_file_id, content=content)
