from dataclasses import dataclass
from pathlib import Path

from codebase_to_llm.application.ports import ContextBufferPort
from codebase_to_llm.domain.context_buffer import File
from codebase_to_llm.domain.result import Err, Ok, Result


@dataclass
class AddFileToContextBufferUseCase:
    def __init__(self, context_buffer: ContextBufferPort):
        self._context_buffer = context_buffer

    def execute(self, path: Path) -> Result[None, str]:
        file = File.try_from_path(path)
        if file.is_err():
            return Err(file.err())

        result = self._context_buffer.add_file(file.ok())
        if result.is_err():
            return Err(result.err())
        return Ok(None)
