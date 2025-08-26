from __future__ import annotations

from codebase_to_llm.application.ports import VideoSummaryRepositoryPort
from codebase_to_llm.domain.video_summary import VideoSummary
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.result import Result, Err


class ListVideoSummariesUseCase:
    """Use case for listing VideoSummary for a user."""

    def __init__(self, repo: VideoSummaryRepositoryPort) -> None:
        self._repo = repo

    def execute(self, owner_id_value: str) -> Result[list[VideoSummary], str]:
        owner_result = UserId.try_create(owner_id_value)
        if owner_result.is_err():
            return Err(owner_result.err() or "Invalid owner ID")

        owner_id = owner_result.ok()
        assert owner_id is not None

        return self._repo.list_for_user(owner_id)
