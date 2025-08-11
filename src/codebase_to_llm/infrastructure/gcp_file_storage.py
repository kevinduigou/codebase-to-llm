from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import final

from codebase_to_llm.application.ports import FileStoragePort
from codebase_to_llm.domain.stored_file import StoredFile
from codebase_to_llm.domain.result import Result, Ok, Err
from codebase_to_llm.config import CONFIG

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from google.cloud import storage  # type: ignore[import-not-found]


@final
class GCPFileStorage(FileStoragePort):
    """Store files in a Google Cloud Storage bucket."""

    __slots__ = ("_bucket_name",)
    _bucket_name: str

    def __init__(self, bucket_name: str | None = None) -> None:
        self._bucket_name = bucket_name or CONFIG.gcp_bucket_name

    def _client(self) -> "storage.Client":  # pragma: no cover - network
        from google.cloud import storage

        return storage.Client()

    def save(self, file: StoredFile, content: bytes) -> Result[None, str]:
        try:
            client = self._client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.blob(file.id().value())
            blob.upload_from_string(content)
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def load(self, file: StoredFile) -> Result[bytes, str]:
        try:
            client = self._client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.blob(file.id().value())
            data = blob.download_as_bytes()
            return Ok(data)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))

    def delete(self, file: StoredFile) -> Result[None, str]:
        try:
            client = self._client()
            bucket = client.bucket(self._bucket_name)
            blob = bucket.blob(file.id().value())
            blob.delete()
            return Ok(None)
        except Exception as exc:  # noqa: BLE001
            return Err(str(exc))
