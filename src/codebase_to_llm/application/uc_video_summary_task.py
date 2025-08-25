from __future__ import annotations

from codebase_to_llm.application.ports import SummaryTaskPort
from codebase_to_llm.domain.result import Result


def enqueue_video_summary_generation(
    url: str,
    model_id: str,
    owner_id: str,
    task_port: SummaryTaskPort,
) -> Result[str, str]:
    return task_port.enqueue_summary(url, model_id, owner_id)


def get_video_summary_status(
    task_id: str, task_port: SummaryTaskPort
) -> Result[tuple[str, list[dict[str, object]] | None], str]:
    return task_port.get_task_status(task_id)
