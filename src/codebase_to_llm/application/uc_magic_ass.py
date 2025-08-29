from __future__ import annotations

from codebase_to_llm.application.ports import (
    ApiKeyRepositoryPort,
    ModelRepositoryPort,
    LLMAdapterPort,
)
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.domain.model import ModelId


def execute(
    content: str,
    prompt: str,
    model_id: str,
    llm_adapter: LLMAdapterPort,
    model_repo: ModelRepositoryPort,
    api_key_repo: ApiKeyRepositoryPort,
) -> Result[str, str]:
    model_id_result = ModelId.try_create(model_id)
    if model_id_result.is_err():
        return Err(model_id_result.err() or f"Invalid model ID: {model_id}")
    model_id_obj = model_id_result.ok()
    if model_id_obj is None:
        return Err(f"Failed to create ModelId from: {model_id}")

    model_result = model_repo.find_model_by_id(model_id_obj)
    if model_result.is_err():
        return Err(model_result.err() or f"Failed to find model with id: {model_id}")
    model = model_result.ok()
    if model is None:
        return Err(f"Model not found with id: {model_id}")

    api_key_result = api_key_repo.find_api_key_by_id(model.api_key_id())
    if api_key_result.is_err():
        return Err(api_key_result.err() or "Failed to load API key")
    api_key = api_key_result.ok()
    if api_key is None:
        return Err("API key not found")

    composed_prompt = f"<user_request>{prompt}<user_request>\n\n<content>{content}\n\n</content><instrcution>First Analyse what should be done based on user request then genrate the updated Output inside the tag <updated_content> </updated_content> (kepp the ass format)<instrucion>"
    response_result = llm_adapter.generate_response_deprecated(
        composed_prompt, model.name().value(), api_key, None
    )
    if response_result.is_err():
        return Err(response_result.err() or "LLM generation failed")
    stream = response_result.ok()
    if stream is None:
        return Err("No response stream")
    try:
        full_response = ""
        for chunk in stream:
            if hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    full_response += delta.content
    except Exception as exc:  # noqa: BLE001
        return Err(f"Error processing response stream: {exc}")

    # Extract content from updated_content tags
    start_tag = "<updated_content>"
    end_tag = "</updated_content>"

    start_index = full_response.find(start_tag)
    if start_index == -1:
        return Err("No <updated_content> tag found in LLM response")

    start_index += len(start_tag)
    end_index = full_response.find(end_tag, start_index)
    if end_index == -1:
        return Err("No closing </updated_content> tag found in LLM response")

    extracted_content = full_response[start_index:end_index].strip()
    if not extracted_content:
        return Err("Empty content found within <updated_content> tags")

    return Ok(extracted_content)
