from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openai import Stream
from openai.types.responses import ResponseTextDeltaEvent, ResponseCompletedEvent

from codebase_to_llm.application.uc_generate_llm_response import (
    GenerateLLMResponseUseCase,
)
from codebase_to_llm.application.uc_get_model_api_key import GetModelApiKeyUseCase
from codebase_to_llm.domain.model import ModelId
from codebase_to_llm.domain.result import Result
from codebase_to_llm.domain.user import User

from .dependencies import (
    _context_buffer,
    _directory_repo,
    _llm_adapter,
    _prompt_repo,
    get_current_user,
    get_user_repositories,
)
from .schemas import GenerateResponseRequest, TestMessageRequest

router = APIRouter(prefix="/llm", tags=["LLM Operations"])


@router.post("/response", summary="Generate LLM response")
def generate_llm_response(
    request: GenerateResponseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Generate a response from the LLM using the current context."""
    api_key_repo, model_repo, rules_repo, _, _ = get_user_repositories(current_user)
    model_id_result = ModelId.try_create(request.model_id)
    if model_id_result.is_err():
        raise HTTPException(status_code=400, detail=model_id_result.err())
    model_id_obj = model_id_result.ok()
    assert model_id_obj is not None
    use_case = GenerateLLMResponseUseCase()
    result = use_case.execute(
        model_id_obj,
        _llm_adapter,
        model_repo,
        api_key_repo,
        _directory_repo,
        _prompt_repo,
        _context_buffer,
        rules_repo,
        request.include_tree,
        request.root_directory_path,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    event = result.ok()
    assert event is not None
    return {"response": event.response}


@router.post("/test-message", summary="Test message generation with a model")
def test_message_generation(
    request: TestMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    api_key_repo, model_repo, _, _, _ = get_user_repositories(current_user)

    model_id_result = ModelId.try_create(request.model_id)
    if model_id_result.is_err():
        raise HTTPException(status_code=400, detail=model_id_result.err())
    model_id_obj = model_id_result.ok()
    assert model_id_obj is not None

    details_result = GetModelApiKeyUseCase().execute(
        model_id_obj, model_repo, api_key_repo
    )
    if details_result.is_err():
        raise HTTPException(status_code=400, detail=details_result.err())
    details = details_result.ok()
    if details is None:
        raise HTTPException(status_code=404, detail="Model or API key not found")

    model_name, api_key = details

    try:
        response_stream: Result[Stream, str] = _llm_adapter.generate_response(
            request.message,
            model_name,
            api_key,
            previous_response_id=getattr(request, "previous_response_id", None),
        )

        def gen() -> Any:
            yield b": stream-start\n\n"
            stream = response_stream.ok()
            if stream is not None:
                for event in stream:
                    match event:
                        case ResponseTextDeltaEvent(delta=delta):
                            delta_payload = {
                                "type": "response.output_text.delta",
                                "delta": delta,
                            }
                            yield (
                                f"data: {json.dumps(delta_payload, ensure_ascii=False)}\n\n".encode(
                                    "utf-8"
                                )
                            )
                        case ResponseCompletedEvent(response=resp):
                            usage = getattr(resp, "usage", None)
                            usage_dict = None
                            if usage is not None:
                                usage_dict = {
                                    "completion_tokens": getattr(
                                        usage, "completion_tokens", None
                                    ),
                                    "prompt_tokens": getattr(
                                        usage, "prompt_tokens", None
                                    ),
                                    "total_tokens": getattr(
                                        usage, "total_tokens", None
                                    ),
                                }
                            payload: dict[str, Any] = {
                                "type": "response.completed",
                                "response": {
                                    "id": resp.id,
                                    "status": getattr(resp, "status", "completed"),
                                    "usage": usage_dict,
                                },
                            }
                            yield (
                                f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode(
                                    "utf-8"
                                )
                            )
                            yield b": stream-end\n\n"
                        case _:
                            pass

        return StreamingResponse(gen(), media_type="text/event-stream")

    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )
