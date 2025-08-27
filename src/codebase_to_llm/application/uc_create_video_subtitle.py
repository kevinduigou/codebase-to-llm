from __future__ import annotations

from codebase_to_llm.application.ports import VideoSubtitleRepositoryPort
from codebase_to_llm.domain.video_subtitle import VideoSubtitle
from codebase_to_llm.domain.stored_file import StoredFileId
from codebase_to_llm.domain.result import Result, Ok, Err


def execute(
    association_id: str,
    video_file_id_value: str,
    subtitle_file_id_value: str,
    repo: VideoSubtitleRepositoryPort,
) -> Result[VideoSubtitle, str]:
    vid_res = StoredFileId.try_create(video_file_id_value)
    if vid_res.is_err():
        return Err(vid_res.err() or "Invalid video file id")
    sub_res = StoredFileId.try_create(subtitle_file_id_value)
    if sub_res.is_err():
        return Err(sub_res.err() or "Invalid subtitle file id")
    vid_id = vid_res.ok()
    sub_id = sub_res.ok()
    assert vid_id is not None and sub_id is not None
    assoc_res = VideoSubtitle.try_create(association_id, vid_id, sub_id)
    if assoc_res.is_err():
        return Err(assoc_res.err() or "Invalid association data")
    association = assoc_res.ok()
    assert association is not None
    add_res = repo.add(association)
    if add_res.is_err():
        return Err(add_res.err() or "Unable to save association")
    return Ok(association)
