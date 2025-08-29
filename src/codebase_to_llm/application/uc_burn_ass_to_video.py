from __future__ import annotations

from codebase_to_llm.application.ports import BurnAssTaskPort
from codebase_to_llm.domain.result import Result


def enqueue_burn_ass_subtitle(
    video_file_id: str,
    output_filename: str,
    owner_id: str,
    task_port: BurnAssTaskPort,
) -> Result[str, str]:
    return task_port.enqueue_burn_ass(video_file_id, output_filename, owner_id)


def get_burn_ass_status(
    task_id: str, task_port: BurnAssTaskPort
) -> Result[tuple[str, str | None], str]:
    return task_port.get_task_status(task_id)
