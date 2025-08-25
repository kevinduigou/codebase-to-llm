from __future__ import annotations

import logging
from typing_extensions import final

from codebase_to_llm.application.ports import SummaryTaskPort
from codebase_to_llm.application.uc_extract_video_summary import (
    ExtractVideoSummaryUseCase,
)
from codebase_to_llm.domain.model import ModelId
from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.infrastructure.celery_app import celery_app
from codebase_to_llm.infrastructure.llm_adapter import OpenAILLMAdapter
from codebase_to_llm.infrastructure.sqlalchemy_api_key_repository import (
    SqlAlchemyApiKeyRepository,
)
from codebase_to_llm.infrastructure.sqlalchemy_model_repository import (
    SqlAlchemyModelRepository,
)
from codebase_to_llm.infrastructure.url_external_source_repository import (
    UrlExternalSourceRepository,
)

logger = logging.getLogger(__name__)


@celery_app.task(name="extract_video_summary")
def extract_video_summary_task(
    url: str, model_id: str, owner_id: str
) -> list[dict[str, str]]:  # pragma: no cover - worker
    external_repo = UrlExternalSourceRepository()
    llm_adapter = OpenAILLMAdapter()
    model_repo = SqlAlchemyModelRepository(owner_id)
    api_key_repo = SqlAlchemyApiKeyRepository(owner_id)
    model_id_result = ModelId.try_create(model_id)
    if model_id_result.is_err():
        error_msg = model_id_result.err() or "Invalid model ID"
        raise Exception(error_msg)
    model_id_obj = model_id_result.ok()
    assert model_id_obj is not None
    use_case = ExtractVideoSummaryUseCase()
    result = use_case.execute(
        url, model_id_obj, external_repo, llm_adapter, model_repo, api_key_repo
    )
    if result.is_err():
        error_msg = result.err() or "Unknown error occurred during summary generation"
        raise Exception(error_msg)
    segments = result.ok()
    if segments is None:
        raise Exception("No summary extracted")
    return [i.model_dump() for i in segments]


@final
class CeleryVideoSummaryTaskQueue(SummaryTaskPort):
    __slots__ = ()

    def enqueue_summary(
        self, url: str, model_id: str, owner_id: str
    ) -> Result[str, str]:
        try:
            task = extract_video_summary_task.delay(url, model_id, owner_id)
            return Ok(task.id)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def get_task_status(
        self, task_id: str
    ) -> Result[tuple[str, list[dict[str, object]] | None], str]:
        try:
            async_result = celery_app.AsyncResult(task_id)
            status = async_result.status
            if async_result.successful():
                segments = async_result.get()
                return Ok((status, segments))
            return Ok((status, None))
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
