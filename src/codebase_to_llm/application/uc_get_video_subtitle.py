from __future__ import annotations

from codebase_to_llm.application.ports import VideoSubtitleRepositoryPort
from codebase_to_llm.domain.video_subtitle import VideoSubtitle, VideoSubtitleId
from codebase_to_llm.domain.result import Result, Ok, Err


def execute(
    association_id_value: str, repo: VideoSubtitleRepositoryPort
) -> Result[VideoSubtitle, str]:
    id_res = VideoSubtitleId.try_create(association_id_value)
    if id_res.is_err():
        return Err(id_res.err() or "Invalid association id")
    association_id = id_res.ok()
    assert association_id is not None
    assoc_res = repo.get(association_id)
    if assoc_res.is_err():
        return Err(assoc_res.err() or "Association not found")
    assoc = assoc_res.ok()
    assert assoc is not None
    return Ok(assoc)
