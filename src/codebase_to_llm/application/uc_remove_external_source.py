from dataclasses import dataclass

from codebase_to_llm.application.ports import ContextBufferPort
from codebase_to_llm.domain.result import Result


@dataclass
class RemoveExternalSourceUseCase:
    """Remove a single external source from the context buffer by URL."""

    def __init__(self, context_buffer: ContextBufferPort) -> None:
        self._context_buffer = context_buffer

    def execute(self, url: str) -> Result[None, str]:
        return self._context_buffer.remove_external_source(url)
