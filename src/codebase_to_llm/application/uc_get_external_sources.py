from dataclasses import dataclass

from codebase_to_llm.application.ports import ContextBufferPort
from codebase_to_llm.domain.context_buffer import ExternalSource
from codebase_to_llm.domain.result import Ok, Result


@dataclass
class GetExternalSourcesUseCase:
    """Retrieve all external sources from the context buffer."""

    def __init__(self, context_buffer: ContextBufferPort) -> None:
        self._context_buffer = context_buffer

    def execute(self) -> Result[list[ExternalSource], str]:
        external_sources = self._context_buffer.get_external_sources()
        return Ok(external_sources)
