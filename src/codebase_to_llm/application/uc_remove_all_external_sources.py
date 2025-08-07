from dataclasses import dataclass

from codebase_to_llm.application.ports import ContextBufferPort
from codebase_to_llm.domain.result import Ok, Result


@dataclass
class RemoveAllExternalSourcesUseCase:
    """Remove all external sources from the context buffer."""

    def __init__(self, context_buffer: ContextBufferPort) -> None:
        self._context_buffer = context_buffer

    def execute(self) -> Result[None, str]:
        for source in self._context_buffer.get_external_sources():
            self._context_buffer.remove_external_source(source.url)
        return Ok(None)
