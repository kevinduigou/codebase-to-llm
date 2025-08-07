from dataclasses import dataclass

from codebase_to_llm.application.ports import ContextBufferPort
from codebase_to_llm.domain.result import Result


@dataclass
class ClearContextBufferUseCase:
    """Remove all elements from the context buffer."""

    def __init__(self, context_buffer: ContextBufferPort) -> None:
        self._context_buffer = context_buffer

    def execute(self) -> Result[None, str]:
        return self._context_buffer.clear()
