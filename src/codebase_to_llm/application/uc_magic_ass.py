from __future__ import annotations

from codebase_to_llm.application.ports import (
    ApiKeyRepositoryPort,
    ModelRepositoryPort,
    LLMAdapterPort,
)
from codebase_to_llm.domain.result import Result, Ok, Err


def execute(
    content: str,
    prompt: str,
    llm_adapter: LLMAdapterPort,
    model_repo: ModelRepositoryPort,
    api_key_repo: ApiKeyRepositoryPort,
) -> Result[str, str]:
    models_result = model_repo.load_models()
    if models_result.is_err():
        return Err(models_result.err() or "Failed to load models")
    models = models_result.ok()
    if models is None or models.is_empty():
        return Err("No models available")
    model = models.models()[0]

    api_key_result = api_key_repo.find_api_key_by_id(model.api_key_id())
    if api_key_result.is_err():
        return Err(api_key_result.err() or "Failed to load API key")
    api_key = api_key_result.ok()
    if api_key is None:
        return Err("API key not found")

    composed_prompt = f"{prompt}\n\n{content}"
    response_result = llm_adapter.generate_response(
        composed_prompt, model.name().value(), api_key, None
    )
    if response_result.is_err():
        return Err(response_result.err() or "LLM generation failed")
    stream = response_result.ok()
    if stream is None:
        return Err("No response stream")
    try:
        updated_content = ""
        for chunk in stream:
            if hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    updated_content += delta.content
    except Exception as exc:  # noqa: BLE001
        return Err(f"Error processing response stream: {exc}")
    return Ok(updated_content)
