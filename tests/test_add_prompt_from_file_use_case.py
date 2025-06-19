from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from codebase_to_llm.application.uc_add_prompt_from_file import AddPromptFromFileUseCase
from codebase_to_llm.infrastructure.in_memory_prompt_repository import InMemoryPromptRepository
from codebase_to_llm.domain.prompt import Prompt


def test_execute_success(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello")
    repo = InMemoryPromptRepository()
    use_case = AddPromptFromFileUseCase(repo)
    result = use_case.execute(file_path)
    assert result.is_ok()
    prompt = result.ok()
    assert prompt == Prompt.try_create("hello").ok()
    repo_result = repo.get_prompt()
    assert repo_result.is_ok()
    assert repo_result.ok() == prompt


def test_execute_empty_file(tmp_path: Path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("   \n")
    repo = InMemoryPromptRepository()
    use_case = AddPromptFromFileUseCase(repo)
    result = use_case.execute(file_path)
    assert result.is_err()
    assert "Prompt cannot be empty" in (result.err() or "")


def test_execute_file_error(tmp_path: Path):
    file_path = tmp_path / "missing.txt"
    repo = InMemoryPromptRepository()
    use_case = AddPromptFromFileUseCase(repo)
    result = use_case.execute(file_path)
    assert result.is_err()

