from __future__ import annotations

import uuid
from typing_extensions import final

from codebase_to_llm.application.ports import BurnAssTaskPort
from codebase_to_llm.application.uc_add_file import AddFileUseCase
from codebase_to_llm.application import uc_get_ass_file_by_video_id
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.stored_file import StoredFileId
from codebase_to_llm.infrastructure.gcp_file_storage import GCPFileStorage
from codebase_to_llm.infrastructure.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from codebase_to_llm.infrastructure.sqlalchemy_video_subtitle_repository import (
    SqlAlchemyVideoSubtitleRepository,
)
from codebase_to_llm.infrastructure.ffmpeg_burn_ass_subtitle import (
    FFMPEGBurnAssSubtitle,
)
from codebase_to_llm.infrastructure.celery_app import celery_app


def _load_video_from_file_id(file_id: str) -> Result[bytes, str]:
    file_repo = SqlAlchemyFileRepository()
    storage = GCPFileStorage()
    id_res = StoredFileId.try_create(file_id)
    if id_res.is_err():
        return Err(id_res.err() or "Invalid file id")
    stored_id = id_res.ok()
    assert stored_id is not None
    file_res = file_repo.get(stored_id)
    if file_res.is_err():
        return Err(file_res.err() or "File not found")
    stored_file = file_res.ok()
    assert stored_file is not None
    content_res = storage.load(stored_file)
    if content_res.is_err():
        return Err(content_res.err() or "Unable to load file content")
    data = content_res.ok()
    assert data is not None
    return Ok(data)


@celery_app.task(name="burn_ass_subtitle")
def burn_ass_subtitle_task(
    video_file_id: str, output_filename: str, owner_id: str
) -> str:  # pragma: no cover - worker
    load_res = _load_video_from_file_id(video_file_id)
    if load_res.is_err():  # pragma: no cover - worker
        raise Exception(load_res.err() or "Failed to load video")
    video_bytes = load_res.ok()
    assert video_bytes is not None

    video_subtitle_repo = SqlAlchemyVideoSubtitleRepository()
    file_repo = SqlAlchemyFileRepository()
    storage = GCPFileStorage()
    subtitle_res = uc_get_ass_file_by_video_id.execute(
        video_file_id, video_subtitle_repo, file_repo, storage
    )
    if subtitle_res.is_err():  # pragma: no cover - worker
        raise Exception(subtitle_res.err() or "Subtitle retrieval failed")
    subtitle_data = subtitle_res.ok()
    assert subtitle_data is not None
    _, subtitle_content = subtitle_data
    subtitle_bytes = subtitle_content.encode("utf-8")

    burner = FFMPEGBurnAssSubtitle()
    burn_res = burner.burn_ass_subtitle(video_bytes, subtitle_bytes)
    if burn_res.is_err():  # pragma: no cover - worker
        raise Exception(burn_res.err() or "Burn failed")
    output_bytes = burn_res.ok()
    assert output_bytes is not None

    new_file_id = str(uuid.uuid4())
    add_file_use_case = AddFileUseCase(file_repo, storage)
    add_res = add_file_use_case.execute(
        id_value=new_file_id,
        owner_id_value=owner_id,
        name=output_filename,
        content=output_bytes,
        directory_id_value=None,
    )
    if add_res.is_err():  # pragma: no cover - worker
        raise Exception(add_res.err() or "Failed to save file")
    return new_file_id


@final
class CeleryBurnAssTaskQueue(BurnAssTaskPort):
    """Celery-backed task queue for burning ASS subtitles."""

    __slots__ = ()

    def enqueue_burn_ass(
        self, video_file_id: str, output_filename: str, owner_id: str
    ) -> Result[str, str]:
        try:
            task = burn_ass_subtitle_task.delay(
                video_file_id, output_filename, owner_id
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
