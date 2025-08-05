from pathlib import Path
from codebase_to_llm.application.ports import (
    ApiKeyRepositoryPort,
    ContextBufferPort,
    DirectoryRepositoryPort,
    PromptRepositoryPort,
)
from codebase_to_llm.application.uc_generate_llm_response import (
    GenerateLLMResponseUseCase,
)
from codebase_to_llm.domain.api_key import ApiKeyId
from codebase_to_llm.infrastructure.filesystem_api_key_repository import (
    FileSystemApiKeyRepository,
)
from codebase_to_llm.infrastructure.filesystem_directory_repository import (
    FileSystemDirectoryRepository,
)
from codebase_to_llm.infrastructure.filesystem_rules_repository import RulesRepository
from codebase_to_llm.infrastructure.in_memory_context_buffer_repository import (
    InMemoryContextBufferRepository,
)
from codebase_to_llm.infrastructure.in_memory_prompt_repository import (
    InMemoryPromptRepository,
)
from codebase_to_llm.infrastructure.llm_adapter import OpenAILLMAdapter
from unittest.mock import patch
from codebase_to_llm.domain.result import Ok
from codebase_to_llm.domain.rules import Rules


class TestGenerateLLMResponseUseCase:
    def test_generate_llm_response(self):

        with patch(
            "codebase_to_llm.application.uc_generate_llm_response.get_full_context",
            return_value=Ok("Just say Hello no more!"),
        ), patch.object(RulesRepository, "load_rules", return_value=Ok(Rules(()))):
            llm_adapter = OpenAILLMAdapter()
            rules_repo = RulesRepository()
            prompts_repo: PromptRepositoryPort = InMemoryPromptRepository()

            root = Path.cwd()
            repo: DirectoryRepositoryPort = FileSystemDirectoryRepository(root)
            context_buffer: ContextBufferPort = InMemoryContextBufferRepository()
            api_key_repo: ApiKeyRepositoryPort = FileSystemApiKeyRepository()

            result = GenerateLLMResponseUseCase().execute(
                model="gpt-4.1",
                api_key_id=ApiKeyId("OPENAI_API_KEY"),
                llm_adapter=llm_adapter,
                api_key_repo=api_key_repo,
                repo=repo,
                prompt_repo=prompts_repo,
                context_buffer=context_buffer,
                rules_repo=rules_repo,
                include_tree=False,
            )

        assert result.is_ok()
        response_generated = result.ok()
        assert response_generated is not None
        assert "Hello" in response_generated.response
