from __future__ import annotations

from codebase_to_llm.application.ports import KeyInsightsTaskPort
from codebase_to_llm.domain.result import Result


def enqueue_key_insights_extraction(
    url: str,
    model_id: str,
    owner_id: str,
    task_port: KeyInsightsTaskPort,
) -> Result[str, str]:
    return task_port.enqueue_key_insights(url, model_id, owner_id)


def get_key_insights_status(
    task_id: str, task_port: KeyInsightsTaskPort
) -> Result[tuple[str, list[dict[str, str]] | None], str]:
    return task_port.get_task_status(task_id)
