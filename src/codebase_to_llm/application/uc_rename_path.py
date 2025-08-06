from dataclasses import dataclass
from pathlib import Path

from codebase_to_llm.application.ports import FileSystemPort
from codebase_to_llm.domain.result import Result


@dataclass
class RenamePathUseCase:
    _fs: FileSystemPort

    def execute(self, path: Path, new_name: str) -> Result[None, str]:
        return self._fs.rename_path(path, new_name)
