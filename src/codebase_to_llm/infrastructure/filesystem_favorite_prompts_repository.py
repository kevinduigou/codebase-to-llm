from __future__ import annotations

from pathlib import Path
from typing import Final
import json

from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.application.ports import FavoritePromptsRepositoryPort
from codebase_to_llm.domain.favorite_prompts import FavoritePrompt, FavoritePrompts


class FavoritePromptsRepository(FavoritePromptsRepositoryPort):
    """Reads / writes the favorite prompts in the user’s home directory."""

    __slots__ = ("_path", "_prompts")

    def __init__(self, path: Path | None = None) -> None:
        default_path = Path.home() / ".copy_to_llm" / "favorite_prompts"
        self._path: Final = path or default_path
        self._prompts: FavoritePrompts | None = None

    def load_prompts(self) -> Result[FavoritePrompts, str]:
        try:
            if not self._path.exists():
                return Err("Favorite prompts file not found.")
            raw = self._path.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(raw) if raw.strip() else []
            prompts: list[FavoritePrompt] = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        name = str(item.get("name", ""))
                        content_raw = item.get("content")
                        content = str(content_raw) if content_raw is not None else ""
                        prompt_result = FavoritePrompt.try_create(name, content)
                        if prompt_result.is_err():
                            return Err(prompt_result.err() or "")
                        prompt = prompt_result.ok()
                        assert prompt is not None
                        prompts.append(prompt)
            prompts_result = FavoritePrompts.try_create(prompts)
            if prompts_result.is_err():
                return Err(prompts_result.err() or "")
            prompts_value = prompts_result.ok()
            assert prompts_value is not None
            self._prompts = prompts_value
            return Ok(prompts_value)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def save_prompts(self, prompts: FavoritePrompts) -> Result[None, str]:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = [
                {"name": p.name(), "content": p.content()} for p in prompts.prompts()
            ]
            self._path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

