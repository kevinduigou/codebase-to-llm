from __future__ import annotations

from codebase_to_llm.application.ports import VideoSubtitleRepositoryPort
from codebase_to_llm.domain.video_subtitle import VideoSubtitleId
from codebase_to_llm.domain.stored_file import StoredFileId
from codebase_to_llm.domain.result import Result, Ok, Err


def execute(
    association_id_value: str,
    subtitle_file_id_value: str,
    repo: VideoSubtitleRepositoryPort,
) -> Result[None, str]:
    assoc_id_res = VideoSubtitleId.try_create(association_id_value)
    if assoc_id_res.is_err():
        return Err(assoc_id_res.err() or "Invalid association id")
    sub_id_res = StoredFileId.try_create(subtitle_file_id_value)
    if sub_id_res.is_err():
        return Err(sub_id_res.err() or "Invalid subtitle file id")
    assoc_id = assoc_id_res.ok()
    sub_id = sub_id_res.ok()
    assert assoc_id is not None and sub_id is not None
    get_res = repo.get(assoc_id)
    if get_res.is_err():
        return Err(get_res.err() or "Association not found")
    assoc = get_res.ok()
    assert assoc is not None
    updated = assoc.update(sub_id)
    upd_res = repo.update(updated)
    if upd_res.is_err():
        return Err(upd_res.err() or "Failed to update association")
    return Ok(None)
