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
    video_subtitle_repo: VideoSubtitleRepositoryPort,
    file_repo: FileRepositoryPort,
    file_storage: FileStoragePort,
) -> Result[str, str]:
    """Delete the ASS subtitle file and its association for a given video file."""
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

    delete_storage_res = file_storage.delete(subtitle_file)
    if delete_storage_res.is_err():
        return Err(delete_storage_res.err() or "Failed to delete subtitle content")

    remove_file_res = file_repo.remove(subtitle_file_id)
    if remove_file_res.is_err():
        return Err(remove_file_res.err() or "Failed to remove subtitle file")

    remove_assoc_res = video_subtitle_repo.remove(association.id())
    if remove_assoc_res.is_err():
        return Err(remove_assoc_res.err() or "Failed to remove subtitle association")

    return Ok(subtitle_file_id.value())
