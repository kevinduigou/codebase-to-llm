from pathlib import Path

import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from codebase_to_llm.domain.context_buffer import Snippet, ExternalSource
from codebase_to_llm.application.ports import (
    ContextBufferPort,
    RulesRepositoryPort,
    PromptRepositoryPort,
)
from codebase_to_llm.domain.prompt import (
    Prompt,
    PromptVariable,
    set_prompt_variable as domain_set_prompt_variable,
)
from codebase_to_llm.domain.result import Ok, Result

from codebase_to_llm.application.uc_copy_context import CopyContextUseCase
from codebase_to_llm.infrastructure.filesystem_directory_repository import (
    FileSystemDirectoryRepository,
)


class FakeClipboard:
    def __init__(self) -> None:
        self.text: str | None = None

    def set_text(self, text: str) -> None:
        self.text = text


class FakeContextBuffer(ContextBufferPort):
    def __init__(self):
        self._snippets = []
        self._files = []
        self._external_sources = []

    def get_files(self):
        return self._files

    def get_snippets(self):
        return self._snippets

    def get_external_sources(self):
        return self._external_sources

    def add_external_source(self, external_source: ExternalSource) -> Result[None, str]:
        self._external_sources.append(external_source)
        return Ok(None)

    def remove_external_source(self, url: str) -> Result[None, str]:
        self._external_sources = [e for e in self._external_sources if e.url != url]
        return Ok(None)

    def add_file(self, file) -> Result[None, str]:
        self._files.append(file)
        return Ok(None)

    def remove_file(self, path) -> Result[None, str]:
        self._files = [f for f in self._files if f.path != path]
        return Ok(None)

    def add_snippet(self, snippet) -> Result[None, str]:
        self._snippets.append(snippet)
        return Ok(None)

    def remove_snippet(self, path, start, end) -> Result[None, str]:
        self._snippets = [
            s
            for s in self._snippets
            if not (s.path == path and s.start == start and s.end == end)
        ]
        return Ok(None)

    def get_context_buffer(self):
        from codebase_to_llm.domain.context_buffer import ContextBuffer

        return ContextBuffer(self._files, self._snippets, self._external_sources)

    def clear(self) -> Result[None, str]:
        self._snippets = []
        self._files = []
        self._external_sources = []
        return Ok(None)

    def is_empty(self):
        return not (self._snippets or self._files or self._external_sources)

    def count_items(self):
        return len(self._snippets) + len(self._files) + len(self._external_sources)


class FakeRulesRepo(RulesRepositoryPort):
    def load_rules(self):
        class DummyRules:
            def rules(self):
                return []

        return type(
            "Ok", (), {"is_ok": lambda self: True, "ok": lambda self: DummyRules()}
        )()

    def save_rules(self, rules):
        return None

    def update_rule_enabled(self, name, enabled):
        return None


class FakePromptRepo(PromptRepositoryPort):
    def __init__(self):
        self._prompt = None

    def get_prompt(self) -> Result[Prompt | None, str]:
        return Ok(self._prompt)

    def set_prompt(self, prompt: Prompt) -> Result[None, str]:
        self._prompt = prompt
        return Ok(None)

    def get_variables_in_prompt(self) -> Result[list[PromptVariable], str]:
        if self._prompt:
            return Ok(self._prompt.get_variables())
        return Ok([])

    def set_prompt_variable(self, variable_key: str, content: str) -> Result[None, str]:
        if self._prompt:
            self._prompt = domain_set_prompt_variable(
                self._prompt, variable_key, content
            )
        return Ok(None)


def test_include_tree_flag(tmp_path: Path):
    (tmp_path / "file.txt").write_text("hello")
    repo = FileSystemDirectoryRepository(tmp_path)
    clipboard = FakeClipboard()
    context_buffer = FakeContextBuffer()
    rules_repo = FakeRulesRepo()
    prompt_repo = FakePromptRepo()
    use_case = CopyContextUseCase(context_buffer, rules_repo, clipboard)
    use_case.execute(repo, prompt_repo)
    assert clipboard.text is not None
    assert "<tree_structure>" in clipboard.text
    clipboard2 = FakeClipboard()
    use_case2 = CopyContextUseCase(context_buffer, rules_repo, clipboard2)
    use_case2.execute(repo, prompt_repo, include_tree=False)
    assert clipboard2.text is not None
    assert "<tree_structure>" not in clipboard2.text


def test_selected_text(tmp_path: Path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("line1\nline2\nline3\n")
    repo = FileSystemDirectoryRepository(tmp_path)
    clipboard = FakeClipboard()
    context_buffer = FakeContextBuffer()
    rules_repo = FakeRulesRepo()
    prompt_repo = FakePromptRepo()
    use_case = CopyContextUseCase(context_buffer, rules_repo, clipboard)
    snippet_result = Snippet.try_create_from_path(file_path, 1, 2, "line1\nline2\n")
    assert snippet_result.is_ok()
    snippet = snippet_result.ok()
    assert snippet is not None
    context_buffer.add_snippet(snippet)
    use_case.execute(repo, prompt_repo)
    assert clipboard.text is not None
    expected_tag = f"<{file_path}:1:2>"
    assert expected_tag in clipboard.text
    assert "line1" in clipboard.text
