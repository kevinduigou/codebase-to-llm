from __future__ import annotations

import os
import subprocess
import tempfile
from typing_extensions import final

from codebase_to_llm.application.ports import BurnAssSubtitlePort
from codebase_to_llm.domain.result import Result, Ok, Err


@final
class FFMPEGBurnAssSubtitle(BurnAssSubtitlePort):
    """Burn ASS subtitles into an MKV video and output MP4."""

    __slots__ = ()

    def burn_ass_subtitle(self, video: bytes, subtitle: bytes) -> Result[bytes, str]:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = os.path.join(tmpdir, "input.mkv")
                ass_path = os.path.join(tmpdir, "subtitle.ass")
                output_path = os.path.join(tmpdir, "output.mp4")
                with open(video_path, "wb") as vf:
                    vf.write(video)
                with open(ass_path, "wb") as sf:
                    sf.write(subtitle)
                subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        video_path,
                        "-vf",
                        f"ass={ass_path}",
                        "-c:a",
                        "copy",
                        output_path,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                with open(output_path, "rb") as out:
                    return Ok(out.read())
        except subprocess.CalledProcessError as exc:  # noqa: BLE001
            return Err(str(exc))
