from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from codebase_to_llm.domain.prompt import Prompt
from codebase_to_llm.infrastructure.in_memory_prompt_repository import (
    InMemoryPromptRepository,
)


def test_set_and_get_prompt():
    repo = InMemoryPromptRepository()
    result_prompt = Prompt.try_create("hello")
    assert result_prompt.is_ok()
    prompt = result_prompt.ok()
    assert prompt is not None
    save_result = repo.set_prompt(prompt)
    assert save_result.is_ok()
    load_result = repo.get_prompt()
    assert load_result.is_ok()
    assert load_result.ok() == prompt
