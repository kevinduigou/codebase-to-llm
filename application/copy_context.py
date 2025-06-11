from __future__ import annotations

import os
from pathlib import Path
from typing import Final, List

from domain.result import Err, Ok, Result

from .ports import ClipboardPort, DirectoryRepositoryPort


class CopyContextUseCase:  # noqa: D101 (public‑API docstring not mandatory here)
    __slots__ = ("_repo", "_clipboard")

    def __init__(self, repo: DirectoryRepositoryPort, clipboard: ClipboardPort):
        self._repo: Final = repo
        self._clipboard: Final = clipboard

    # ──────────────────────────────────────────────────────────────────
    def execute(
        self, files: List[Path], rules: str | None = None
    ) -> Result[None, str]:  # noqa: D401 (simple verb)
        tree_result = self._repo.build_tree()
        if tree_result.is_err():
            return Err(tree_result.err())  # type: ignore[arg-type]

        parts: List[str] = [
            "<tree_structure>",
            tree_result.ok(),
            "</tree_structure>",
        ]  # type: ignore[list-item]

        if rules and rules.strip():
            parts.extend([
                "<rules_to_follow>",
                rules.strip(),
                "</rules_to_follow>",
            ])

        for file_ in files:
            content_result = self._repo.read_file(file_)
            tag = f"<{file_}>"
            parts.append(tag)
            if content_result.is_ok():
                parts.append(content_result.ok())  # type: ignore[list-item,arg-type]
            # On failure, embed empty body — could embed error instead if desired.
            parts.append(f"</{file_}>")

        self._clipboard.set_text(os.linesep.join(parts))
        return Ok(None)
