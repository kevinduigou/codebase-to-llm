from dataclasses import dataclass
from pathlib import Path

from codebase_to_llm.application.ports import ContextBufferPort
from codebase_to_llm.domain.result import Ok, Result


@dataclass
class RemoveElementsFromContextBufferUseCase:  # noqa: D101

    def __init__(self, context_buffer: ContextBufferPort):
        self._context_buffer_port = context_buffer

    def execute(self, context_buffer_elmts: list[str]) -> Result[None, str]:
        for elmts in context_buffer_elmts:
            if elmts.startswith("file:"):
                self._context_buffer_port.remove_file(Path(elmts.split(":")[1]))
            elif elmts.startswith("snippet:"):
                self._context_buffer_port.remove_snippet(
                    Path(elmts.split(":")[1]),
                    int(elmts.split(":")[2]),
                    int(elmts.split(":")[3]),
                )
            elif elmts.startswith("external_source:"):
                http_url = ":".join(elmts.split(":")[1:])
                self._context_buffer_port.remove_external_source(http_url)
        return Ok(None)
