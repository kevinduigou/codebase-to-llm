from codebase_to_llm.application.ports import (
    ApiKeyRepositoryPort,
    ContextBufferPort,
    DirectoryRepositoryPort,
    LLMAdapterPort,
    ModelRepositoryPort,
    PromptRepositoryPort,
    RulesRepositoryPort,
)
from codebase_to_llm.application.uc_copy_context import get_full_context
from codebase_to_llm.domain.model import ModelId
from codebase_to_llm.domain.llm import ResponseGenerated
from codebase_to_llm.domain.result import Err, Ok, Result


class GenerateLLMResponseUseCase:
    def __init__(self):
        pass

    def execute(
        self,
        model_id: ModelId,
        llm_adapter: LLMAdapterPort,
        model_repo: ModelRepositoryPort,
        api_key_repo: ApiKeyRepositoryPort,
        repo: DirectoryRepositoryPort,
        prompt_repo: PromptRepositoryPort,
        context_buffer: ContextBufferPort,
        rules_repo: RulesRepositoryPort,
        include_tree: bool = True,
        root_directory_path: str | None = None,
    ) -> Result[ResponseGenerated, str]:
        full_contxt_result: Result[str, str] = get_full_context(
            repo,
            prompt_repo,
            context_buffer,
            rules_repo,
            include_tree,
            root_directory_path,
        )

        full_context = full_contxt_result.ok()
        if full_context is None:
            return Err("Failed to get full context")

        model_result = model_repo.find_model_by_id(model_id)
        if model_result.is_err():
            return Err(model_result.err() or "Error getting model")

        model = model_result.ok()
        if model is None:
            return Err("Failed to get model")

        api_key_result = api_key_repo.find_api_key_by_id(model.api_key_id())
        if api_key_result.is_err():
            return Err(api_key_result.err() or "Error getting API key")

        api_key = api_key_result.ok()
        if api_key is None:
            return Err("Failed to get API key")

        generate_response_result = llm_adapter.generate_response(
            full_context, model.name().value(), api_key
        )

        if generate_response_result.is_err():
            return Err(generate_response_result.err() or "Error generating response")

        response_text = generate_response_result.ok()
        if response_text is None:
            return Err("Failed to get response text")

        return Ok(ResponseGenerated(response_text))
