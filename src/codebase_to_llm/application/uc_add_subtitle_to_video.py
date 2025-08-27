from __future__ import annotations

from codebase_to_llm.application.ports import AddSubtitleTaskPort
from codebase_to_llm.domain.result import Result


def enqueue_video_add_subtitles(
    file_id: str,
    origin_language: str,
    target_language: str,
    owner_id: str,
    output_filename: str,
    task_port: AddSubtitleTaskPort,
    subtitle_color: str = "white",
    subtitle_style: str = "outline",
    use_soft_subtitles: bool = False,
    font_size_percentage: float = 4.0,
    margin_percentage: float = 5.0,
    subtitle_format: str = "mov_text",
) -> Result[str, str]:
    return task_port.enqueue_add_subtitles(
        file_id,
        origin_language,
        target_language,
        owner_id,
        output_filename,
        subtitle_color,
        "black",  # subtitle_background_color - not exposed in API yet
        "cyan",  # subtitle_highlight_color - not exposed in API yet
        use_soft_subtitles,
        subtitle_style,
        font_size_percentage,
        margin_percentage,
        subtitle_format,
    )


def get_add_subtitles_status(
    task_id: str, task_port: AddSubtitleTaskPort
) -> Result[tuple[str, str | None], str]:
    return task_port.get_task_status(task_id)
