from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Final, List, final


from codebase_to_llm.domain.result import Err, Ok, Result
from codebase_to_llm.domain.rules import Rules

from .ports import (
    ClipboardPort,
    ContextBufferPort,
    DirectoryRepositoryPort,
    RulesRepositoryPort,
)


@final
@dataclass
class CopyContextUseCase:  # noqa: D101 (public‑API docstring not mandatory here)

    def __init__(
        self,
        context_buffer: ContextBufferPort,
        rules_repo: RulesRepositoryPort,
        repo: DirectoryRepositoryPort,
        clipboard: ClipboardPort,
    ):
        self._context_buffer = context_buffer
        self._rules_repo = rules_repo
        self._repo = repo
        self._clipboard = clipboard

    def execute(
        self,
        user_request: str | None = None,
        include_tree: bool = True,
        root_directory_path: str | None = None,
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

        for file_ in self._context_buffer.get_files():
            if root_directory_path is not None:
                root_path = Path(root_directory_path)
                try:
                    rel_path = file_.path.relative_to(root_path)
                except ValueError:
                    rel_path = file_.path
            else:
                rel_path = file_.path
            tag = f"<{rel_path}>"
            parts.append(tag)
            parts.append(file_.content)
            parts.append(f"</{rel_path}>")

        if self._context_buffer.get_snippets():
            for snippet in self._context_buffer.get_snippets():
                if root_directory_path is not None:
                    root_path = Path(root_directory_path)
                    try:
                        rel_path = snippet.path.relative_to(root_path)
                    except ValueError:
                        rel_path = snippet.path
                else:
                    rel_path = snippet.path
                tag = f"<{rel_path}:{snippet.start}:{snippet.end}>"
                parts.append(tag)
                parts.append(snippet.content)
                parts.append(f"</{rel_path}:{snippet.start}:{snippet.end}>")
        if self._context_buffer.get_external_sources():
            for external_source in self._context_buffer.get_external_sources():
                tag = f"<{external_source.url}>"
                parts.append(tag)
                parts.append(external_source.content)
                parts.append(f"</{external_source.url}>")

        rules_result = self._rules_repo.load_rules()
        if rules_result.is_ok():
            rules_val = rules_result.ok()
            assert rules_val is not None
            if (
                rules_val.rules()
                and len(list(filter(lambda x: x.enabled() == True, rules_val.rules())))
                > 0
            ):
                parts.append("<rules_to_follow>")
                for rule in rules_val.rules():
                    if rule.enabled():
                        parts.append(rule.content())
                parts.append("</rules_to_follow>")

        if user_request:
            parts.append("<user_request>")
            parts.append(user_request)
            parts.append("</user_request>")
        self._clipboard.set_text(os.linesep.join(parts))
        return Ok(None)
