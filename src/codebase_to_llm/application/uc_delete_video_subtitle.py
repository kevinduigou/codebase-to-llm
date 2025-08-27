from __future__ import annotations

from codebase_to_llm.application.ports import VideoSubtitleRepositoryPort
from codebase_to_llm.domain.video_subtitle import VideoSubtitleId
from codebase_to_llm.domain.result import Result, Ok, Err


def execute(
    association_id_value: str, repo: VideoSubtitleRepositoryPort
) -> Result[None, str]:
    id_res = VideoSubtitleId.try_create(association_id_value)
    if id_res.is_err():
        return Err(id_res.err() or "Invalid association id")
    assoc_id = id_res.ok()
    assert assoc_id is not None
    rem_res = repo.remove(assoc_id)
    if rem_res.is_err():
        return Err(rem_res.err() or "Failed to delete association")
    return Ok(None)
