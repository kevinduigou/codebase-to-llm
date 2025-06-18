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
        file_result = File.try_from_path(path)
        if file_result.is_err():
            return Err(file_result.err() or "Unknown error")
        file = file_result.ok()
        if file is None:
            return Err("File creation failed")
        result = self._context_buffer.add_file(file)
        if result.is_err():
            return Err(result.err() or "Unknown error")
        return Ok(None)
