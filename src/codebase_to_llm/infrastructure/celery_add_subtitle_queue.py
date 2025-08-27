from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
import time
import uuid
from typing import Iterable, Tuple
from typing_extensions import final
from pydantic import BaseModel
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from codebase_to_llm.application.ports import AddSubtitleTaskPort
from codebase_to_llm.application.uc_add_file import AddFileUseCase
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.stored_file import StoredFileId
from codebase_to_llm.infrastructure.gcp_file_storage import GCPFileStorage
from codebase_to_llm.infrastructure.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from codebase_to_llm.infrastructure.celery_app import celery_app

logger = logging.getLogger(__name__)


class TranslationResponse(BaseModel):
    """Pydantic model for single text translation response."""

    translated_text: str


class SubtitleTranslation(BaseModel):
    """Pydantic model for a single subtitle translation."""

    index: int
    text: str


class BatchTranslationResponse(BaseModel):
    """Pydantic model for batch subtitle translation response."""

    translations: list[SubtitleTranslation]


def _ass_color_from_hex(rgb_hex: str, alpha_hex: str = "00") -> str:
    """
    Convert '#RRGGBB' or 'RRGGBB' to ASS &HAABBGGRR format.
    alpha_hex: '00' = opaque, 'FF' = fully transparent (ASS uses inverted alpha).
    """
    h = rgb_hex.lstrip("#")
    if len(h) != 6:
        raise ValueError("Color must be RRGGBB")
    rr, gg, bb = h[0:2], h[2:4], h[4:6]
    # ASS wants AABBGGRR
    return f"&H{alpha_hex}{bb}{gg}{rr}"


def build_subtitle_style(
    preset: str = "outline",  # 'outline' or 'boxed'
    font_name: str = "Inter",  # any font installed/available to libass
    font_size: int = 36,
    text_hex: str = "FFFFFF",
    box_alpha_hex: str = "60",  # 0x60 ~ 38% transparency (00=opaque, FF=invisible)
    margins: tuple[int, int, int] = (60, 60, 50),  # L, R, V in px
) -> str:
    ml, mr, mv = margins
    text_color = _ass_color_from_hex(text_hex, "00")
    outline_color = _ass_color_from_hex("202020", "00")
    back_color = _ass_color_from_hex("000000", box_alpha_hex)

    if preset == "boxed":
        # Semi-transparent rounded-ish feel (approx via blurless box)
        # BorderStyle=3 draws an opaque box behind text using BackColour.
        return (
            f"FontName={font_name},FontSize={font_size},"
            f"PrimaryColour={text_color},BackColour={back_color},"
            f"BorderStyle=3,Outline=0,Shadow=0,"
            f"Alignment=2,WrapStyle=2,ScaleBorderAndShadow=1,"
            f"MarginL={ml},MarginR={mr},MarginV={mv}"
        )

    # Default: modern outline + subtle shadow, no karaoke box
    return (
        f"FontName={font_name},FontSize={font_size},"
        f"PrimaryColour={text_color},OutlineColour={outline_color},"
        f"BorderStyle=1,Outline=2,Shadow=1,"
        f"Alignment=2,WrapStyle=2,ScaleBorderAndShadow=1,"
        f"MarginL={ml},MarginR={mr},MarginV={mv}"
    )


def _soft_wrap(text: str, max_len: int = 42) -> str:
    """
    Greedy wrap at spaces to max_len per line; returns 1–2 lines joined with '\\N'.
    If text is longer than ~2*max_len, it will still be split at ~2 lines (best-effort).
    """
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_len:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
        if len(lines) == 2:  # keep it to max 2 lines
            break
    if cur and len(lines) < 2:
        lines.append(cur)
    # If we stopped early, append the rest to the second line (best effort)
    rest_idx = len(" ".join(lines).split())
    if rest_idx < len(words) and len(lines) > 0:
        tail = " ".join(words[rest_idx:])
        if tail:
            if len(lines) == 1 and len(lines[0]) + 1 + len(tail) <= max_len:
                lines[0] += " " + tail
            else:
                lines[-1] += " " + tail
    return "\\N".join(lines[:2])


def _mux_soft_subs(
    input_video: str, srt_path: str, output_path: str, subtitle_format: str = "mov_text",target_language = "eng"
) -> None:
    """Add soft subtitles (muxed as subtitle track) instead of burning them in"""
    try:
        if subtitle_format == "ass":
            # ASS format is not supported in MP4 containers, so we need to use MKV
            # Change output extension to .mkv for ASS support
            base_name = os.path.splitext(output_path)[0]
            mkv_output = f"{base_name}.mkv"

            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    input_video,
                    "-i",
                    srt_path,
                    "-c:v",
                    "copy",
                    "-c:a",
                    "copy",
                    "-c:s",
                    "ass",  # embed ASS subtitles
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a?",
                    "-map",
                    "1:0",
                    "-metadata:s:s:0",
                    f"language={target_language}",
                    "-y",  # overwrite output file if it exists
                    mkv_output,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Convert back to MP4 if needed (this will convert ASS to mov_text)
            if output_path.endswith(".mp4"):
                subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        mkv_output,
                        "-c:v",
                        "copy",
                        "-c:a",
                        "copy",
                        "-c:s",
                        "mov_text",  # convert ASS to mov_text for MP4
                        "-y",
                        output_path,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                # Clean up temporary MKV file
                os.remove(mkv_output)
            else:
                # If output is not MP4, rename MKV to the desired output
                os.rename(mkv_output, output_path)
        else:
            # Default: mov_text = widely supported in MP4 players (iOS, browsers)
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    input_video,
                    "-i",
                    srt_path,
                    "-c:v",
                    "copy",
                    "-c:a",
                    "copy",
                    "-c:s",
                    "mov_text",  # convert SRT to MP4 text subtitles
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a?",
                    "-map",
                    "1:0",
                    "-metadata:s:s:0",
                    "language=eng",  # set your target language code here
                    "-y",  # overwrite output file if it exists
                    output_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg command failed with return code {e.returncode}")
        logger.error(f"Command: {' '.join(e.cmd)}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise


def parse_srt(srt_content: str) -> list[dict[str, str | int]]:
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\n*$)"
    matches = re.findall(pattern, srt_content, re.DOTALL)
    subtitles: list[dict[str, str | int]] = []
    for match in matches:
        subtitles.append(
            {
                "index": int(match[0]),
                "start": match[1],
                "end": match[2],
                "text": match[3].strip(),
            }
        )
    return subtitles


def format_srt(subtitles: list[dict[str, str | int]]) -> str:
    srt_content = ""
    for sub in subtitles:
        idx = sub["index"]
        start = sub["start"]
        end = sub["end"]
        text = sub["text"]
        srt_content += f"{idx}\n{start} --> {end}\n{text}\n\n"
    return srt_content


def translate_text(client: OpenAI, text: str, target_language: str) -> str:
    language_names = {
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
    }
    target_lang_name = language_names.get(target_language, target_language)
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional translator. Translate the following text to "
                    f"{target_lang_name}. Maintain the original meaning and tone."
                ),
            },
            {"role": "user", "content": text},
        ],
        response_format=TranslationResponse,
        temperature=0.3,
    )
    parsed_response = response.choices[0].message.parsed
    assert parsed_response is not None
    return parsed_response.translated_text.strip()


def _batched(iterable: Iterable, n: int):
    """Yield lists of size n."""
    lst = list(iterable)
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def translate_subtitles_in_batches(
    client: OpenAI,
    subtitles: list[dict[str, str | int]],
    origin_language: str,
    target_language: str,
    batch_size: int = 160,
    max_retries: int = 5,
    retry_backoff_seconds: float = 1.0,
) -> list[dict[str, str | int]]:
    """
    Translate many subtitle lines with far fewer API calls by batching.
    Returns a new list with the same order and indices, but translated text.
    """
    # Map language codes to names (optional, matches your existing style)
    language_names = {
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
        "en": "English",
    }
    src_name = language_names.get(origin_language, origin_language or "source language")
    tgt_name = language_names.get(target_language, target_language)

    translated: list[dict[str, str | int]] = []

    for chunk in _batched(subtitles, batch_size):
        # Prepare a compact payload for the model
        payload = {
            "segments": [
                {
                    "index": int(s["index"]),  # ensure int
                    "text": str(s["text"]),  # keep original line breaks
                }
                for s in chunk
            ]
        }

        # Build messages with strict JSON response format
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": (
                    "You are a professional subtitle translator specializing in conversational and educational content. "
                    f"Translate from {src_name} to {tgt_name}. "
                    "Translate idiomatically and naturally for native speakers, prioritizing meaning and natural flow over literal accuracy. "
                    "Use vocabulary and expressions that sound natural when spoken aloud. "
                    "Preserve the tone, intent, and cultural context of each segment. "
                    "Keep punctuation and preserve line breaks **within** each segment's text. "
                    "Do not merge or split segments — each segment must be translated individually, "
                    "but you must consider the **complete context** across all segments before translating to ensure coherence and natural flow. "
                    "Use conversational register appropriate for spoken subtitles. "
                    "When encountering technical or specialized terminology, use the standard terms in the target language. "
                    "Do not add explanations or comments."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Translate the following subtitle segments. "
                    "First review the complete context to understand the topic and flow, then translate each segment naturally. "
                    "Return ONLY a valid JSON object in this exact format:\n"
                    "{\n"
                    '  "translations": [\n'
                    '    {"index": <number>, "text": "<translated string>"}\n'
                    "  ]\n"
                    "}\n\n"
                    f"Segments JSON:\n{json.dumps(payload, ensure_ascii=False)}"
                ),
            },
        ]

        # Simple retry with exponential backoff for transient errors
        last_err: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                # First translation pass using structured outputs
                resp = client.beta.chat.completions.parse(
                    messages=messages,
                    model="gpt-4o",
                    temperature=0.2,
                    response_format=BatchTranslationResponse,
                )
                parsed_response = resp.choices[0].message.parsed
                assert parsed_response is not None, "Empty parsed response"

                # Second pass for natural language refinement
                refinement_messages: list[ChatCompletionMessageParam] = [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional subtitle translator specializing in conversational and educational content. "
                            f"Check if text sounds like a native speaker in {tgt_name} would say it. "
                            "If not, reformulate sentences but keep the global structure."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"First review the complete context to understand the topic and flow, then adjust translation in {tgt_name} to sound natural. "
                            f"Segments to refine:\n{json.dumps([{'index': t.index, 'text': t.text} for t in parsed_response.translations], ensure_ascii=False)}"
                        ),
                    },
                ]

                refined_resp = client.beta.chat.completions.parse(
                    messages=refinement_messages,
                    model="gpt-4o",
                    temperature=0.2,
                    response_format=BatchTranslationResponse,
                )
                refined_parsed = refined_resp.choices[0].message.parsed
                assert refined_parsed is not None, "Empty refined response"

                # Build a lookup by index to reattach safely
                by_index = {t.index: t.text for t in refined_parsed.translations}

                out_chunk: list[dict[str, str | int]] = []
                for s in chunk:
                    idx = int(s["index"])
                    txt = by_index.get(idx)
                    if txt is None:
                        # Hard fail if alignment is broken
                        raise ValueError(f"Missing translation for index {idx}")
                    out_chunk.append(
                        {
                            "index": idx,
                            "start": s["start"],
                            "end": s["end"],
                            "text": txt,
                        }
                    )
                translated.extend(out_chunk)
                last_err = None
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
                # exponential backoff
                time.sleep(retry_backoff_seconds * (2 ** (attempt - 1)))

        if last_err:
            raise last_err  # surface the problem to the caller

    # Keep original ordering (already preserved by chunking)
    return translated


def sanitize_filename(name: str, replacement: str = "_", max_length: int = 255) -> str:
    name = str(name).strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, name)
    name = name.rstrip(" .")
    if replacement:
        rep_escaped = re.escape(replacement)
        name = re.sub(rf"{rep_escaped}+", replacement, name)
    if not name:
        name = "untitled"
    return name[:max_length]


def _load_video_from_file_id(file_id: str) -> Result[bytes, str]:
    file_repo = SqlAlchemyFileRepository()
    storage = GCPFileStorage()
    id_res = StoredFileId.try_create(file_id)
    if id_res.is_err():
        return Err(id_res.err() or "Invalid file id")
    stored_file = id_res.ok()
    assert stored_file is not None
    file_res = file_repo.get(stored_file)
    if file_res.is_err():
        return Err(file_res.err() or "File not found")
    file = file_res.ok()
    assert file is not None
    content_res = storage.load(file)
    if content_res.is_err():
        return Err(content_res.err() or "Unable to load file content")
    data = content_res.ok()
    assert data is not None
    return Ok(data)


def _load_video_from_file_path(file_path: str) -> Result[bytes, str]:
    """Load video content directly from a file path on the filesystem."""
    try:
        if not os.path.exists(file_path):
            return Err(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            return Err(f"Path is not a file: {file_path}")

        with open(file_path, "rb") as f:
            content = f.read()

        return Ok(content)
    except PermissionError:
        return Err(f"Permission denied accessing file: {file_path}")
    except OSError as e:
        return Err(f"Error reading file {file_path}: {str(e)}")
    except Exception as e:
        return Err(f"Unexpected error loading file {file_path}: {str(e)}")


def _get_video_dimensions(video_path: str) -> Tuple[int, int]:
    """
    Get video width and height using ffprobe.
    Returns (width, height) tuple.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                "-select_streams",
                "v:0",
                video_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)
        video_stream = data["streams"][0]
        width = int(video_stream["width"])
        height = int(video_stream["height"])

        return (width, height)
    except (
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
        ValueError,
    ) as e:
        logger.warning(f"Failed to get video dimensions: {e}. Using default 1920x1080")
        return (1920, 1080)  # Default to 1080p if detection fails


def _calculate_dynamic_subtitle_params(
    video_width: int,
    video_height: int,
    font_size_percentage: float = 4.0,
    margin_percentage: float = 5.0,
) -> Tuple[int, Tuple[int, int, int]]:
    """
    Calculate dynamic font size and margins based on video dimensions.

    Args:
        video_width: Video width in pixels
        video_height: Video height in pixels
        font_size_percentage: Font size as percentage of video height (default: 4%)
        margin_percentage: Margin as percentage of video width/height (default: 5%)

    Returns:
        Tuple of (font_size, (left_margin, right_margin, vertical_margin))
    """
    # Calculate font size as percentage of video height
    font_size = max(12, int(video_height * (font_size_percentage / 100)))

    # Calculate margins as percentage of video dimensions
    horizontal_margin = max(20, int(video_width * (margin_percentage / 100)))
    vertical_margin = max(15, int(video_height * (margin_percentage / 100)))

    return font_size, (horizontal_margin, horizontal_margin, vertical_margin)


def _download_video(url: str, path: str) -> None:
    subprocess.run(
        ["yt-dlp", "-f", "mp4", "-o", path, url],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def add_subtitle_to_video(
    content: bytes,
    origin_language: str,
    target_language: str,
    subtitle_color: str = "yellow",
    subtitle_background_color: str = "black",
    subtitle_highlight_color: str = "cyan",
    use_soft_subtitles: bool = False,
    subtitle_style: str = "outline",
    font_size_percentage: float = 4.0,
    margin_percentage: float = 5.0,
    subtitle_format: str = "mov_text",
) -> bytes:
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "input.mp4")
        with open(video_path, "wb") as fh:
            fh.write(content)

        # Get video dimensions for dynamic subtitle sizing
        video_width, video_height = _get_video_dimensions(video_path)
        logger.info(f"Video dimensions: {video_width}x{video_height}")

        audio_path = os.path.join(tmpdir, "audio.wav")
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                video_path,
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                audio_path,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # 1) Transcribe with segment-level timestamps (no word-level for clean subtitles)
        with open(audio_path, "rb") as audio_file:
            transcript_json = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        # 2) Convert to SRT format and handle translation
        subtitles: list[dict[str, str | int]] = []
        if transcript_json.segments:
            # First, collect all segments without translation
            for i, seg in enumerate(transcript_json.segments, 1):
                text = seg.text.strip()

                # Convert timestamps to SRT format
                start_time = f"{int(seg.start // 3600):02d}:{int((seg.start % 3600) // 60):02d}:{seg.start % 60:06.3f}".replace(
                    ".", ","
                )
                end_time = f"{int(seg.end // 3600):02d}:{int((seg.end % 3600) // 60):02d}:{seg.end % 60:06.3f}".replace(
                    ".", ","
                )

                subtitles.append(
                    {
                        "index": i,
                        "start": start_time,
                        "end": end_time,
                        "text": text,
                    }
                )

            # Batch translate all subtitles if needed
            if origin_language != target_language:
                logger.info(
                    f"Batch translating {len(subtitles)} subtitle segments from {origin_language} to {target_language}"
                )
                subtitles = translate_subtitles_in_batches(
                    client=client,
                    subtitles=subtitles,
                    origin_language=origin_language,
                    target_language=target_language,
                    batch_size=160,  # Process up to 160 segments per API call
                    max_retries=5,
                    retry_backoff_seconds=1.0,
                )

            # Apply soft wrapping for better readability to all subtitles
            for subtitle in subtitles:
                subtitle["text"] = _soft_wrap(str(subtitle["text"]), max_len=42)

        # 3) Write SRT file
        srt_path = os.path.join(tmpdir, "subtitles.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(format_srt(subtitles))

        output_path = os.path.join(tmpdir, "output.mp4")

        if use_soft_subtitles:
            # 4a) Add soft subtitles (muxed as subtitle track)
            _mux_soft_subs(video_path, srt_path, output_path, subtitle_format,target_language)
        else:
            # 4b) Burn-in modern styled subtitles with dynamic sizing
            # Convert color names to hex values
            color_map = {
                "yellow": "FFFF00",
                "black": "000000",
                "white": "FFFFFF",
                "red": "FF0000",
                "green": "00FF00",
                "blue": "0000FF",
                "cyan": "00FFFF",
            }
            text_color = color_map.get(
                subtitle_color.lower(), subtitle_color.replace("#", "")
            )

            # Calculate dynamic subtitle parameters based on video dimensions
            dynamic_font_size, dynamic_margins = _calculate_dynamic_subtitle_params(
                video_width, video_height, font_size_percentage, margin_percentage
            )

            logger.info(
                f"Dynamic subtitle sizing: font_size={dynamic_font_size}, margins={dynamic_margins}"
            )

            # Build modern subtitle style with dynamic sizing
            style = build_subtitle_style(
                preset=subtitle_style,  # 'outline' or 'boxed'
                font_name="Inter",  # or "Arial" if you prefer
                font_size=dynamic_font_size,
                text_hex=text_color,
                box_alpha_hex="60",  # only used by 'boxed'
                margins=dynamic_margins,
            )

            # Apply subtitles with modern styling
            sub_filter = f"subtitles={srt_path}:force_style='{style}'"
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    video_path,
                    "-vf",
                    sub_filter,
                    "-c:a",
                    "copy",
                    "-movflags",
                    "+faststart",  # better streaming
                    output_path,
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        with open(output_path, "rb") as out_file:
            return out_file.read()


@celery_app.task(name="add_subtitle_to_video")
def add_subtitle_to_video_task(
    file_id: str,
    origin_language: str,
    target_language: str,
    owner_id: str,
    output_filename: str,
    subtitle_color: str = "white",
    subtitle_background_color: str = "black",
    subtitle_highlight_color: str = "cyan",
    use_soft_subtitles: bool = False,
    subtitle_style: str = "outline",
    font_size_percentage: float = 4.0,
    margin_percentage: float = 5.0,
    subtitle_format: str = "mov_text",
) -> str:  # pragma: no cover - worker
    load_res = _load_video_from_file_id(file_id)
    if load_res.is_err():
        error_msg = load_res.err() or "Unknown error occurred while loading video file"
        raise Exception(error_msg)
    content_opt = load_res.ok()
    if content_opt is None:
        raise Exception("Unable to load file")
    content = content_opt
    output_bytes = add_subtitle_to_video(
        content,
        origin_language,
        target_language,
        subtitle_color,
        subtitle_background_color,
        subtitle_highlight_color,
        use_soft_subtitles,
        subtitle_style,
        font_size_percentage,
        margin_percentage,
        subtitle_format,
    )
    new_file_id = str(uuid.uuid4())
    file_repo = SqlAlchemyFileRepository()
    storage = GCPFileStorage()
    add_file_use_case = AddFileUseCase(file_repo, storage)
    result = add_file_use_case.execute(
        id_value=new_file_id,
        owner_id_value=owner_id,
        name=output_filename,
        content=output_bytes,
        directory_id_value=None,
    )
    if result.is_err():  # pragma: no cover - validation/network
        error_msg = result.err() or "Unknown error occurred during file persistence"
        raise Exception(error_msg)
    return new_file_id


@celery_app.task(name="add_subtitle_to_video_from_path")
def add_subtitle_to_video_from_path_task(
    file_path: str,
    origin_language: str,
    target_language: str,
    output_path: str,
    subtitle_color: str = "white",
    subtitle_background_color: str = "black",
    subtitle_highlight_color: str = "cyan",
    use_soft_subtitles: bool = False,
    subtitle_style: str = "outline",
    font_size_percentage: float = 4.0,
    margin_percentage: float = 5.0,
    subtitle_format: str = "mov_text",
) -> str:  # pragma: no cover - worker
    """
    Add subtitles to a video file from a file path and save to output path.
    Returns the output file path on success.
    """
    load_res = _load_video_from_file_path(file_path)
    if load_res.is_err():
        error_msg = load_res.err() or "Unknown error occurred while loading video file"
        raise Exception(error_msg)
    content_opt = load_res.ok()
    if content_opt is None:
        raise Exception("Unable to load file")
    content = content_opt

    output_bytes = add_subtitle_to_video(
        content,
        origin_language,
        target_language,
        subtitle_color,
        subtitle_background_color,
        subtitle_highlight_color,
        use_soft_subtitles,
        subtitle_style,
        font_size_percentage,
        margin_percentage,
        subtitle_format,
    )

    # Write output to specified path
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(output_bytes)

        return output_path
    except Exception as e:
        raise Exception(f"Failed to write output file {output_path}: {str(e)}")


@final
class CeleryAddSubtitleTaskQueue(AddSubtitleTaskPort):
    __slots__ = ()

    def enqueue_add_subtitles(
        self,
        file_id: str,
        origin_language: str,
        target_language: str,
        owner_id: str,
        output_filename: str,
        subtitle_color: str = "white",
        subtitle_background_color: str = "black",
        subtitle_highlight_color: str = "cyan",
        use_soft_subtitles: bool = False,
        subtitle_style: str = "outline",
        font_size_percentage: float = 4.0,
        margin_percentage: float = 5.0,
        subtitle_format: str = "mov_text",
    ) -> Result[str, str]:
        try:
            task = add_subtitle_to_video_task.delay(
                file_id,
                origin_language,
                target_language,
                owner_id,
                output_filename,
                subtitle_color,
                subtitle_background_color,
                subtitle_highlight_color,
                use_soft_subtitles,
                subtitle_style,
                font_size_percentage,
                margin_percentage,
                subtitle_format,
            )
            return Ok(task.id)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def get_task_status(self, task_id: str) -> Result[tuple[str, str | None], str]:
        try:
            async_result = celery_app.AsyncResult(task_id)
            status = async_result.status
            if async_result.successful():
                file_id = str(async_result.get())
                return Ok((status, file_id))
            return Ok((status, None))
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
