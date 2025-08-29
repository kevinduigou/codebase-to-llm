from __future__ import annotations

from codebase_to_llm.application.ports import (
    VideoSubtitleRepositoryPort,
    FileRepositoryPort,
    FileStoragePort,
)
from codebase_to_llm.domain.stored_file import StoredFileId
from codebase_to_llm.domain.result import Result, Ok, Err


def execute(
    video_file_id_value: str,
    new_content: str,
    video_subtitle_repo: VideoSubtitleRepositoryPort,
    file_repo: FileRepositoryPort,
    file_storage: FileStoragePort,
) -> Result[str, str]:
    """Replace the ASS subtitle content for a given video file ID."""
    video_file_id_res = StoredFileId.try_create(video_file_id_value)
    if video_file_id_res.is_err():
        return Err(video_file_id_res.err() or "Invalid video file id")
    video_file_id = video_file_id_res.ok()
    assert video_file_id is not None

    association_res = video_subtitle_repo.get_by_video_file_id(video_file_id)
    if association_res.is_err():
        return Err(association_res.err() or "No subtitle found for this video")
    association = association_res.ok()
    assert association is not None

    subtitle_file_id = association.subtitle_file_id()
    subtitle_file_res = file_repo.get(subtitle_file_id)
    if subtitle_file_res.is_err():
        return Err(subtitle_file_res.err() or "Subtitle file not found")
    subtitle_file = subtitle_file_res.ok()
    assert subtitle_file is not None

    save_res = file_storage.save(subtitle_file, new_content.encode("utf-8"))
    if save_res.is_err():
        return Err(save_res.err() or "Failed to save subtitle content")

    return Ok(subtitle_file_id.value())
