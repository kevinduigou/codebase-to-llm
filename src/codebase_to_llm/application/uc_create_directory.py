from dataclasses import dataclass
from pathlib import Path
from typing_extensions import final

from codebase_to_llm.application.ports import DirectoryRepositoryPort
from codebase_to_llm.domain.result import Result


@final
@dataclass
class CreateDirectoryUseCase:
    _repo: DirectoryRepositoryPort

    def execute(self, path: Path) -> Result[None, str]:  # noqa: D401
        return self._repo.create_directory(path)
