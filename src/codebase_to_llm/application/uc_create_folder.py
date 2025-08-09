from dataclasses import dataclass
from pathlib import Path

from codebase_to_llm.application.ports import FileSystemPort
from codebase_to_llm.domain.result import Result


@dataclass
class CreateFolderUseCase:
    _fs: FileSystemPort

    def execute(self, parent: Path, name: str) -> Result[None, str]:
        return self._fs.create_folder(parent, name)
