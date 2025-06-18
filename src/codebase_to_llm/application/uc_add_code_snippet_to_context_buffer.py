from pathlib import Path

from codebase_to_llm.application.ports import ContextBufferPort
from codebase_to_llm.domain.context_buffer import Snippet
from codebase_to_llm.domain.result import Err, Ok, Result


class AddCodeSnippetToContextBufferUseCase:

    def __init__(self, context_buffer: ContextBufferPort):
        self._context_buffer_port = context_buffer

    def execute(
        self, path: Path, start: int, end: int, text: str
    ) -> Result[Snippet, str]:
        snippet_result = Snippet.try_create_from_path(path, start, end, text)
        if snippet_result.is_err():
            return Err(snippet_result.err() or "Unknown error")
        snippet = snippet_result.ok()
        if snippet is None:
            return Err("Snippet creation failed")
        result = self._context_buffer_port.add_snippet(snippet)
        if result.is_err():
            return Err(result.err() or "Unknown error")
        return Ok(snippet)
