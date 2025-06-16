from __future__ import annotations

import os
from pathlib import Path
from typing import Final, List

from codebase_to_llm.domain.selected_text import SelectedText

from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.rules import Rules

from .ports import ClipboardPort, DirectoryRepositoryPort


class CopyContextUseCase:  # noqa: D101 (public‑API docstring not mandatory here)
    __slots__ = ("_repo", "_clipboard")

    def __init__(self, repo: DirectoryRepositoryPort, clipboard: ClipboardPort):
        self._repo: Final = repo
        self._clipboard: Final = clipboard

    # ──────────────────────────────────────────────────────────────────
    def execute(
        self,
        files: List[Path],
        snippets: List[SelectedText] | None = None,
        rules: Rules | None = None,
        user_request: str | None = None,
        include_tree: bool = True,
    ) -> Result[None, str]:  # noqa: D401 (simple verb)
        parts: List[str] = []

        if include_tree:
            tree_result = self._repo.build_tree()
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

        if snippets:
            for snippet in snippets:
                tag = f"<{snippet.path}:{snippet.start}:{snippet.end}>"
                parts.append(tag)
                parts.append(snippet.text)
                parts.append(f"</{snippet.path}:{snippet.start}:{snippet.end}>")

        if rules and rules.rules():
            parts.append("<rules_to_follow>")
            for rule in rules.rules():
                parts.append(rule.content())
            parts.append("</rules_to_follow>")

        if user_request:
            parts.append("<user_request>")
            parts.append(user_request)
            parts.append("</user_request>")

        self._clipboard.set_text(os.linesep.join(parts))
        return Ok(None)
