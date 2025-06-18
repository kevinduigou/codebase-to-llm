from pathlib import Path

import sys

from codebase_to_llm.domain.context_buffer import Snippet
from codebase_to_llm.application.ports import ContextBufferPort, RulesRepositoryPort

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

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

    def add_external_source(self, url, text):
        self._external_sources.append(
            type("ExternalSource", (), {"url": url, "content": text})()
        )
        return None

    def remove_external_source(self, url):
        self._external_sources = [e for e in self._external_sources if e.url != url]
        return None

    def add_file(self, file):
        self._files.append(file)
        return None

    def remove_file(self, path):
        self._files = [f for f in self._files if f.path != path]
        return None

    def add_snippet(self, snippet):
        self._snippets.append(snippet)
        return None

    def remove_snippet(self, path, start, end):
        self._snippets = [
            s
            for s in self._snippets
            if not (s.path == path and s.start == start and s.end == end)
        ]
        return None

    def get_context_buffer(self):
        return None

    def clear(self):
        self._snippets = []
        self._files = []
        self._external_sources = []
        return None

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


def test_include_tree_flag(tmp_path: Path):
    (tmp_path / "file.txt").write_text("hello")
    repo = FileSystemDirectoryRepository(tmp_path)
    clipboard = FakeClipboard()
    context_buffer = FakeContextBuffer()
    rules_repo = FakeRulesRepo()
    use_case = CopyContextUseCase(context_buffer, rules_repo, repo, clipboard)
    use_case.execute()
    assert clipboard.text is not None
    assert "<tree_structure>" in clipboard.text
    clipboard2 = FakeClipboard()
    use_case2 = CopyContextUseCase(context_buffer, rules_repo, repo, clipboard2)
    use_case2.execute(include_tree=False)
    assert clipboard2.text is not None
    assert "<tree_structure>" not in clipboard2.text


def test_selected_text(tmp_path: Path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("line1\nline2\nline3\n")
    repo = FileSystemDirectoryRepository(tmp_path)
    clipboard = FakeClipboard()
    context_buffer = FakeContextBuffer()
    rules_repo = FakeRulesRepo()
    use_case = CopyContextUseCase(context_buffer, rules_repo, repo, clipboard)
    snippet_result = Snippet.try_create_from_path(file_path, 1, 2, "line1\nline2\n")
    assert snippet_result.is_ok()
    snippet = snippet_result.ok()
    assert snippet is not None
    context_buffer.add_snippet(snippet)
    use_case.execute()
    assert clipboard.text is not None
    expected_tag = f"<{file_path}:1:2>"
    assert expected_tag in clipboard.text
    assert "line1" in clipboard.text
