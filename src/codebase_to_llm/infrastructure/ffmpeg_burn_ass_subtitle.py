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

                # Write input files
                with open(video_path, "wb") as vf:
                    vf.write(video)
                with open(ass_path, "wb") as sf:
                    sf.write(subtitle)

                # First attempt: Try to copy audio stream (preserves original quality)
                result = self._try_ffmpeg_with_audio_copy(
                    video_path, ass_path, output_path
                )

                if result.is_ok():
                    with open(output_path, "rb") as out:
                        return Ok(out.read())

                # Fallback: Re-encode audio with higher quality settings
                result = self._try_ffmpeg_with_audio_reencode(
                    video_path, ass_path, output_path
                )

                if result.is_ok():
                    with open(output_path, "rb") as out:
                        return Ok(out.read())

                # Convert Result[None, str] to Result[bytes, str] for error case
                return Err(result.err() or "Unknown error occurred")

        except Exception as exc:  # noqa: BLE001
            return Err(f"Unexpected error: {str(exc)}")

    def _try_ffmpeg_with_audio_copy(
        self, video_path: str, ass_path: str, output_path: str
    ) -> Result[None, str]:
        """Try FFmpeg with audio stream copying (preserves original audio quality)."""
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",  # Overwrite output files without asking
                    "-i",
                    video_path,
                    "-vf",
                    f"ass={ass_path}",
                    "-c:v",
                    "libx264",  # Video codec
                    "-c:a",
                    "copy",  # Copy audio stream without re-encoding
                    "-map",
                    "0:v:0",  # Map first video stream
                    "-map",
                    "0:a",  # Map all audio streams
                    "-preset",
                    "medium",  # Balance between speed and quality
                    "-crf",
                    "23",  # Constant rate factor for good quality
                    output_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Verify output file
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                return Err("Output file was not created or is empty")

            return Ok(None)

        except subprocess.CalledProcessError as exc:  # noqa: BLE001
            error_msg = f"FFmpeg with audio copy failed: {exc.returncode}"
            if exc.stderr:
                error_msg += f"\nStderr: {exc.stderr}"
            return Err(error_msg)

    def _try_ffmpeg_with_audio_reencode(
        self, video_path: str, ass_path: str, output_path: str
    ) -> Result[None, str]:
        """Fallback: Re-encode audio with high quality settings."""
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",  # Overwrite output files without asking
                    "-i",
                    video_path,
                    "-vf",
                    f"ass={ass_path}",
                    "-c:v",
                    "libx264",  # Video codec
                    "-c:a",
                    "aac",  # Re-encode to AAC
                    "-b:a",
                    "192k",  # Higher audio bitrate for better quality
                    "-map",
                    "0:v:0",  # Map first video stream
                    "-map",
                    "0:a",  # Map all audio streams
                    "-preset",
                    "medium",  # Balance between speed and quality
                    "-crf",
                    "23",  # Constant rate factor for good quality
                    output_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Verify output file
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                return Err("Output file was not created or is empty")

            return Ok(None)

        except subprocess.CalledProcessError as exc:  # noqa: BLE001
            error_msg = f"FFmpeg with audio re-encode failed: {exc.returncode}"
            if exc.stderr:
                error_msg += f"\nStderr: {exc.stderr}"
            if exc.stdout:
                error_msg += f"\nStdout: {exc.stdout}"
            return Err(error_msg)
