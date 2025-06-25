from codebase_to_llm.application.ports import (
    ApiKeyRepositoryPort,
    ContextBufferPort,
    DirectoryRepositoryPort,
    LLMAdapterPort,
    PromptRepositoryPort,
    RulesRepositoryPort,
)
from codebase_to_llm.application.uc_copy_context import get_full_context
from codebase_to_llm.domain.api_key import ApiKeyId
from codebase_to_llm.domain.llm import ResponseGenerated
from codebase_to_llm.domain.result import Err, Ok, Result


class GenerateLLMResponseUseCase:
    def __init__(self):
        pass

    def execute(
        self,
        model,
        api_key_id: ApiKeyId,
        llm_adapter: LLMAdapterPort,
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

        api_key_result = api_key_repo.find_api_key_by_id(api_key_id)
        if api_key_result.is_err():
            return Err(api_key_result.err() or "Error getting API key")

        generate_response_result = llm_adapter.generate_response(
            full_contxt_result.ok(), model, api_key_result.ok()
        )

        if generate_response_result.is_err():
            return Err(generate_response_result.err() or "Error generating response")

        return Ok(ResponseGenerated(generate_response_result.ok()))
