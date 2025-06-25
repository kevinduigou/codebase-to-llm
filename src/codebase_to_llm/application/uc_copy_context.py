from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import List, final


from codebase_to_llm.domain.prompt import Prompt
from codebase_to_llm.domain.result import Err, Ok, Result

from .ports import (
    ClipboardPort,
    ContextBufferPort,
    DirectoryRepositoryPort,
    PromptRepositoryPort,
    RulesRepositoryPort,
)


def get_full_context(
    repo: DirectoryRepositoryPort,
    prompt_repo: PromptRepositoryPort,
    context_buffer: ContextBufferPort,
    rules_repo: RulesRepositoryPort,
    include_tree: bool = False,
    root_directory_path: str | None = None,
) -> Result[str, str]:

    parts: List[str] = []

    if include_tree:
        tree_result = repo.build_tree()
        if tree_result.is_err():
            return Err(tree_result.err() or "Error building tree")

        parts.extend(
            [
                "<tree_structure>",
                tree_result.ok() or "",
                "</tree_structure>",
            ]
        )

    for file_ in context_buffer.get_files():
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

    if context_buffer.get_snippets():
        for snippet in context_buffer.get_snippets():
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
    if context_buffer.get_external_sources():
        for external_source in context_buffer.get_external_sources():
            tag = f"<{external_source.url}>"
            parts.append(tag)
            parts.append(external_source.content)
            parts.append(f"</{external_source.url}>")

    rules_result = rules_repo.load_rules()
    if rules_result.is_ok():
        rules_val = rules_result.ok()
        assert rules_val is not None
        if (
            rules_val.rules()
            and len(list(filter(lambda x: x.enabled(), rules_val.rules()))) > 0
        ):
            parts.append("<rules_to_follow>")
            for rule in rules_val.rules():
                if rule.enabled():
                    parts.append(rule.content())
            parts.append("</rules_to_follow>")

    if prompt_repo.get_prompt().is_ok():
        user_prompt: Prompt | None = prompt_repo.get_prompt().ok()

        if user_prompt is not None:
            user_prompt_full_text_result: Result[str, str] = user_prompt.full_text()
            if user_prompt_full_text_result.is_ok():
                parts.append("<user_request>")
                parts.append(user_prompt_full_text_result.ok() or "")
                parts.append("</user_request>")
            else:
                return Err(
                    user_prompt_full_text_result.err()
                    or "Error getting prompt full text"
                )
    else:
        return Err(prompt_repo.get_prompt().err() or "Error getting prompt")

    return Ok(os.linesep.join(parts))


@final
@dataclass
class CopyContextUseCase:  # noqa: D101 (public‑API docstring not mandatory here)

    def __init__(
        self,
        context_buffer: ContextBufferPort,
        rules_repo: RulesRepositoryPort,
        clipboard: ClipboardPort,
    ):
        self._context_buffer = context_buffer
        self._rules_repo = rules_repo
        self._clipboard = clipboard

    def execute(
        self,
        repo: DirectoryRepositoryPort,
        prompt_repo: PromptRepositoryPort,
        include_tree: bool = True,
        root_directory_path: str | None = None,
    ) -> Result[None, str]:  # noqa: D401 (simple verb)
        full_contxt_result: Result[str, str] = get_full_context(
            repo,
            prompt_repo,
            self._context_buffer,
            self._rules_repo,
            include_tree,
            root_directory_path,
        )
        if full_contxt_result.is_ok():
            self._clipboard.set_text(full_contxt_result.ok())
        else:
            return Err(full_contxt_result.err() or "Error getting full context")
        return Ok(None)
