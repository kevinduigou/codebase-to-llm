from __future__ import annotations

from codebase_to_llm.application import (
    uc_update_ass_file_by_video_id,
    uc_delete_ass_file_by_video_id,
)
from codebase_to_llm.application.ports import (
    VideoSubtitleRepositoryPort,
    FileRepositoryPort,
    FileStoragePort,
)
from codebase_to_llm.domain.user import UserId
from codebase_to_llm.domain.stored_file import StoredFile, StoredFileId
from codebase_to_llm.domain.video_subtitle import VideoSubtitle
from codebase_to_llm.domain.result import Ok, Err


class InMemoryFileRepo(FileRepositoryPort):
    def __init__(self, files: dict[str, StoredFile]) -> None:
        self._files = files

    def add(self, file: StoredFile):  # pragma: no cover - unused
        return Ok(None)

    def get(self, file_id: StoredFileId):
        file = self._files.get(file_id.value())
        if file is None:
            return Err("not found")
        return Ok(file)

    def update(self, file: StoredFile):  # pragma: no cover - unused
        self._files[file.id().value()] = file
        return Ok(None)

    def remove(self, file_id: StoredFileId):
        self._files.pop(file_id.value(), None)
        return Ok(None)

    def list_for_user(self, owner_id: UserId):  # pragma: no cover - unused
        return Ok(list(self._files.values()))


class InMemoryFileStorage(FileStoragePort):
    def __init__(self, contents: dict[str, bytes]) -> None:
        self._contents = contents

    def save(self, file: StoredFile, content: bytes):
        self._contents[file.id().value()] = content
        return Ok(None)

    def load(self, file: StoredFile):  # pragma: no cover - unused
        data = self._contents.get(file.id().value())
        if data is None:
            return Err("not found")
        return Ok(data)

    def delete(self, file: StoredFile):
        self._contents.pop(file.id().value(), None)
        return Ok(None)


class InMemoryVideoSubtitleRepo(VideoSubtitleRepositoryPort):
    def __init__(self, association: VideoSubtitle) -> None:
        self._assoc = association

    def add(self, association: VideoSubtitle):  # pragma: no cover - unused
        self._assoc = association
        return Ok(None)

    def get(self, association_id):  # pragma: no cover - unused
        return Ok(self._assoc)

    def get_by_video_file_id(self, video_file_id):
        if self._assoc.video_file_id().value() != video_file_id.value():
            return Err("not found")
        return Ok(self._assoc)

    def update(self, association: VideoSubtitle):  # pragma: no cover - unused
        self._assoc = association
        return Ok(None)

    def remove(self, association_id):
        self._assoc = None  # type: ignore[assignment]
        return Ok(None)


def test_update_and_delete_ass_file() -> None:
    owner = UserId.try_create("u1").ok()
    assert owner is not None
    video_id = StoredFileId.try_create("video").ok()
    subtitle_id = StoredFileId.try_create("sub").ok()
    assert video_id is not None and subtitle_id is not None
    stored_file = StoredFile.try_create("sub", owner, "s.ass").ok()
    assert stored_file is not None
    association = VideoSubtitle.try_create("assoc", video_id, subtitle_id).ok()
    assert association is not None

    file_repo = InMemoryFileRepo({"sub": stored_file})
    storage = InMemoryFileStorage({"sub": b"old"})
    assoc_repo = InMemoryVideoSubtitleRepo(association)

    update_res = uc_update_ass_file_by_video_id.execute(
        "video", "new content", assoc_repo, file_repo, storage
    )
    assert update_res.is_ok()
    assert storage._contents["sub"] == b"new content"

    delete_res = uc_delete_ass_file_by_video_id.execute(
        "video", assoc_repo, file_repo, storage
    )
    assert delete_res.is_ok()
    assert "sub" not in storage._contents
    assert file_repo._files == {}
