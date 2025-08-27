from __future__ import annotations

from codebase_to_llm.application.ports import BurnAssSubtitlePort
from codebase_to_llm.domain.result import Result


def execute(
    video_bytes: bytes, subtitle_bytes: bytes, port: BurnAssSubtitlePort
) -> Result[bytes, str]:
    return port.burn_ass_subtitle(video_bytes, subtitle_bytes)
