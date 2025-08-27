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
) -> Result[tuple[str, str], str]:
    """Get ASS file ID and content for a given video file ID.

    Returns:
        Result containing tuple of (subtitle_file_id, subtitle_content) or error message
    """
    # Validate and create video file ID
    video_file_id_res = StoredFileId.try_create(video_file_id_value)
    if video_file_id_res.is_err():
        return Err(video_file_id_res.err() or "Invalid video file id")
    video_file_id = video_file_id_res.ok()
    assert video_file_id is not None

    # Find the video-subtitle association
    association_res = video_subtitle_repo.get_by_video_file_id(video_file_id)
    if association_res.is_err():
        return Err(association_res.err() or "No subtitle found for this video")
    association = association_res.ok()
    assert association is not None

    # Get the subtitle file metadata
    subtitle_file_id = association.subtitle_file_id()
    subtitle_file_res = file_repo.get(subtitle_file_id)
    if subtitle_file_res.is_err():
        return Err(subtitle_file_res.err() or "Subtitle file not found")
    subtitle_file = subtitle_file_res.ok()
    assert subtitle_file is not None

    # Load the subtitle file content
    content_res = file_storage.load(subtitle_file)
    if content_res.is_err():
        return Err(content_res.err() or "Failed to load subtitle content")
    content_bytes = content_res.ok()
    assert content_bytes is not None

    # Convert bytes to string (ASS files are text files)
    try:
        content_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return Err("Failed to decode subtitle file as UTF-8")

    return Ok((subtitle_file_id.value(), content_str))
