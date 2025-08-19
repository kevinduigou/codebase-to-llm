from __future__ import annotations

import logging
import os
import re
import subprocess
import tempfile
import uuid
from typing_extensions import final
from openai import OpenAI

from codebase_to_llm.application.ports import TranslationTaskPort
from codebase_to_llm.application.uc_add_file import AddFileUseCase
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.stored_file import StoredFileId
from codebase_to_llm.infrastructure.gcp_file_storage import GCPFileStorage
from codebase_to_llm.infrastructure.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from codebase_to_llm.infrastructure.celery_app import celery_app

logger = logging.getLogger(__name__)


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
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional translator. Translate the following text to "
                    f"{target_lang_name}. Maintain the original meaning and tone. Only return the translated text, nothing else."
                ),
            },
            {"role": "user", "content": text},
        ],
        temperature=0.3,
    )
    content = response.choices[0].message.content
    assert content is not None
    return content.strip()


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


def _load_video_from_file(file_id: str) -> Result[bytes, str]:
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


def _download_video(url: str, path: str) -> None:
    subprocess.run(
        ["yt-dlp", "-f", "mp4", "-o", path, url],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _process_video(content: bytes, target_language: str) -> bytes:
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "input.mp4")
        with open(video_path, "wb") as fh:
            fh.write(content)
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
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="srt"
            )
        if target_language != "en":
            subtitles = parse_srt(transcript)
            for subtitle in subtitles:
                text = subtitle["text"]
                assert isinstance(text, str)
                subtitle["text"] = translate_text(client, text, target_language)
            transcript = format_srt(subtitles)
        srt_path = os.path.join(tmpdir, "subtitles.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        output_path = os.path.join(tmpdir, "output.mp4")
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                video_path,
                "-vf",
                f"subtitles={srt_path}",
                "-c:a",
                "copy",
                output_path,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        with open(output_path, "rb") as out_file:
            return out_file.read()


@celery_app.task(name="translate_video")
def translate_video_task(
    file_id: str,
    target_language: str,
    owner_id: str,
    output_filename: str,
) -> str:  # pragma: no cover - worker
    load_res = _load_video_from_file(file_id)
    if load_res.is_err():
        raise Exception(load_res.err())
    content_opt = load_res.ok()
    if content_opt is None:
        raise Exception("Unable to load file")
    content = content_opt
    output_bytes = _process_video(content, target_language)
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
        raise Exception(result.err())
    return new_file_id


@final
class CeleryTranslationTaskQueue(TranslationTaskPort):
    __slots__ = ()

    def enqueue_translation(
        self,
        file_id: str,
        target_language: str,
        owner_id: str,
        output_filename: str,
    ) -> Result[str, str]:
        try:
            task = translate_video_task.delay(
                file_id, target_language, owner_id, output_filename
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
