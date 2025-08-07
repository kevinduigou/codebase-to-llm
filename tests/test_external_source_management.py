from codebase_to_llm.application.uc_get_external_sources import (
    GetExternalSourcesUseCase,
)
from codebase_to_llm.application.uc_remove_external_source import (
    RemoveExternalSourceUseCase,
)
from codebase_to_llm.application.uc_remove_all_external_sources import (
    RemoveAllExternalSourcesUseCase,
)
from codebase_to_llm.application.uc_clear_context_buffer import (
    ClearContextBufferUseCase,
)
from codebase_to_llm.domain.context_buffer import ExternalSource
from codebase_to_llm.infrastructure.in_memory_context_buffer_repository import (
    InMemoryContextBufferRepository,
)


def test_external_source_use_cases():
    repo = InMemoryContextBufferRepository()
    repo.add_external_source(ExternalSource("https://a", "c1", False))
    repo.add_external_source(ExternalSource("https://b", "c2", False))

    get_uc = GetExternalSourcesUseCase(repo)
    sources_result = get_uc.execute()
    assert sources_result.is_ok()
    assert len(sources_result.ok() or []) == 2

    remove_uc = RemoveExternalSourceUseCase(repo)
    remove_uc.execute("https://a")
    assert len(repo.get_external_sources()) == 1

    remove_all_uc = RemoveAllExternalSourcesUseCase(repo)
    remove_all_uc.execute()
    assert repo.get_external_sources() == []

    repo.add_external_source(ExternalSource("https://c", "c3", False))
    clear_uc = ClearContextBufferUseCase(repo)
    clear_uc.execute()
    assert repo.is_empty()
