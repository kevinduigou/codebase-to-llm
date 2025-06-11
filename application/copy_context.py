from __future__ import annotations

import os
from pathlib import Path
from typing import Final, List

from application.ignore_service import IgnoreService
from domain.result import Err, Ok, Result

from .ports import ClipboardPort, DirectoryRepositoryPort


class CopyContextUseCase:  # noqa: D101 (public‑API docstring not mandatory here)
    __slots__ = ("_repo", "_clipboard","_ignore_service")

    def __init__(self, repo: DirectoryRepositoryPort, clipboard: ClipboardPort, ignore_service: IgnoreService):
        self._repo: Final = repo
        self._clipboard: Final = clipboard
        self._ignore_service = ignore_service

    # ──────────────────────────────────────────────────────────────────
    def execute(
        self,
        files: List[Path],
        rules: str | None = None,
        user_request: str | None = None,
        include_tree: bool = True,
    ) -> Result[None, str]:  # noqa: D401 (simple verb)
        parts: List[str] = []

        if include_tree:
            tokens = self._ignore_service.load_tokens()
            tree_result = self._repo.build_tree(tokens.ok())
            if tree_result.is_err():
                return Err(tree_result.err())  # type: ignore[arg-type]

            parts.extend(
                [
                    "<tree_structure>",
                    tree_result.ok() or "",
                    "</tree_structure>",
                ]
            )

        for file_ in files:
            content_result = self._repo.read_file(file_)
            tag = f"<{file_}>"
            parts.append(tag)
            if content_result.is_ok():
                parts.append(content_result.ok() or "")  # type: ignore[list-item,arg-type]
            # On failure, embed empty body — could embed error instead if desired.
            parts.append(f"</{file_}>")

        if rules and rules.strip():
            parts.extend(
                [
                    "<rules_to_follow>",
                    rules.strip(),
                    "</rules_to_follow>",
                ]
            )

        if user_request:
            parts.append("<user_request>")
            parts.append(user_request)
            parts.append("</user_request>")

        self._clipboard.set_text(os.linesep.join(parts))
        return Ok(None)
