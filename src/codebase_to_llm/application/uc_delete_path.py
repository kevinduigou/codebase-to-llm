from dataclasses import dataclass
from pathlib import Path

from codebase_to_llm.application.ports import FileSystemPort
from codebase_to_llm.domain.result import Result


@dataclass
class DeletePathUseCase:
    _fs: FileSystemPort

    def execute(self, path: Path) -> Result[None, str]:
        return self._fs.delete_path(path)
