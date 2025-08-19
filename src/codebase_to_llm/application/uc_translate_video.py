from __future__ import annotations

from codebase_to_llm.application.ports import TranslationTaskPort
from codebase_to_llm.domain.result import Result


def enqueue_video_translation(
    file_id: str | None,
    youtube_url: str | None,
    target_language: str,
    owner_id: str,
    task_port: TranslationTaskPort,
) -> Result[str, str]:
    return task_port.enqueue_translation(
        file_id, youtube_url, target_language, owner_id
    )


def get_translation_status(
    task_id: str, task_port: TranslationTaskPort
) -> Result[tuple[str, str | None], str]:
    return task_port.get_task_status(task_id)
