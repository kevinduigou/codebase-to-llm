import pytest
from pathlib import Path
from codebase_to_llm.application.ports import (
    ApiKeyRepositoryPort,
    ContextBufferPort,
    DirectoryRepositoryPort,
    ModelRepositoryPort,
    PromptRepositoryPort,
)
from codebase_to_llm.application.uc_generate_llm_response import (
    GenerateLLMResponseUseCase,
)
from codebase_to_llm.domain.api_key import ApiKey, ApiKeys
from codebase_to_llm.domain.model import Model, Models, ModelId
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
from codebase_to_llm.domain.result import Ok, Err
from codebase_to_llm.domain.rules import Rules


USER_ID = "user-1"


class TestGenerateLLMResponseUseCase:
    @pytest.mark.skip(reason="Temporarily disabled for CI pipeline")
    def test_generate_llm_response(self):

        with (
            patch(
                "codebase_to_llm.application.uc_generate_llm_response.get_full_context",
                return_value=Ok("Just say Hello no more!"),
            ),
            patch.object(RulesRepository, "load_rules", return_value=Ok(Rules(()))),
        ):
            llm_adapter = OpenAILLMAdapter()
            rules_repo = RulesRepository()
            prompts_repo: PromptRepositoryPort = InMemoryPromptRepository()

            root = Path.cwd()
            repo: DirectoryRepositoryPort = FileSystemDirectoryRepository(root)
            context_buffer: ContextBufferPort = InMemoryContextBufferRepository()

            class DummyApiKeyRepo(ApiKeyRepositoryPort):
                def __init__(self) -> None:
                    api_key_res = ApiKey.try_create(
                        "OPENAI_API_KEY",
                        USER_ID,
                        "https://api.openai.com",
                        "sk-1234567890abcdef",
                    )
                    assert api_key_res.is_ok()
                    self._api_key = api_key_res.ok()

                def load_api_keys(self):  # type: ignore[override]
                    assert self._api_key is not None
                    return Ok(ApiKeys((self._api_key,)))

                def save_api_keys(self, api_keys):  # type: ignore[override]
                    return Ok(None)

                def find_api_key_by_id(self, api_key_id):  # type: ignore[override]
                    if (
                        self._api_key
                        and self._api_key.id().value() == api_key_id.value()
                    ):
                        return Ok(self._api_key)
                    return Err("not found")

            api_key_repo: ApiKeyRepositoryPort = DummyApiKeyRepo()

            class DummyModelRepo(ModelRepositoryPort):
                def __init__(self) -> None:
                    model_res = Model.try_create(
                        "m1", USER_ID, "gpt-4.1", "OPENAI_API_KEY"
                    )
                    assert model_res.is_ok()
                    self._model = model_res.ok()

                def load_models(self):  # type: ignore[override]
                    assert self._model is not None
                    models_res = Models.try_create((self._model,))
                    assert models_res.is_ok()
                    return Ok(models_res.ok())

                def save_models(self, models):  # type: ignore[override]
                    return Ok(None)

                def find_model_by_id(self, model_id):  # type: ignore[override]
                    if self._model and self._model.id().value() == model_id.value():
                        return Ok(self._model)
                    return Err("not found")

            model_repo: ModelRepositoryPort = DummyModelRepo()

            result = GenerateLLMResponseUseCase().execute(
                model_id=ModelId("m1"),
                llm_adapter=llm_adapter,
                model_repo=model_repo,
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
