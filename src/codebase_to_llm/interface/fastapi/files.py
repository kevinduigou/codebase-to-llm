from __future__ import annotations

import mimetypes
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from codebase_to_llm.application.uc_add_file import AddFileUseCase
from codebase_to_llm.application.uc_get_file import GetFileUseCase
from codebase_to_llm.application.uc_update_file import UpdateFileUseCase
from codebase_to_llm.application.uc_delete_file import DeleteFileUseCase
from codebase_to_llm.application.uc_list_files import ListFilesUseCase
from codebase_to_llm.domain.user import User

from .dependencies import _file_repo, _file_storage, get_current_user
from .schemas import UploadFileRequest, UpdateFileRequest

router = APIRouter(prefix="/files", tags=["File Management"])


@router.post("/", summary="Upload a new file")
def upload_file(
    request: UploadFileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Upload a new file to the system."""
    file_id = str(uuid.uuid4())
    use_case = AddFileUseCase(_file_repo, _file_storage)
    result = use_case.execute(
        file_id,
        current_user.id().value(),
        request.name,
        request.content.encode("utf-8"),
        request.directory_id,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    file = result.ok()
    assert file is not None
    return {"id": file.id().value(), "name": file.name()}


@router.get("/", summary="List all files")
def list_files(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, str | None]]:
    use_case = ListFilesUseCase(_file_repo)
    result = use_case.execute(current_user.id().value())
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    files = result.ok()
    assert files is not None
    return [
        {
            "id": f.id().value(),
            "name": f.name(),
            "directory_id": (
                dir_id.value() if (dir_id := f.directory_id()) is not None else None
            ),
        }
        for f in files
    ]


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    use_case = GetFileUseCase(_file_repo, _file_storage)
    result = use_case.execute(current_user.id().value(), file_id)
    if result.is_err():
        raise HTTPException(status_code=404, detail=result.err())

    result_data = result.ok()
    if result_data is None:
        raise HTTPException(status_code=404, detail="File not found")
    file, content = result_data  # file: your domain object, content: bytes
    mt, _ = mimetypes.guess_type(file.name())
    headers = {"Content-Disposition": f'attachment; filename="{file.name()}"'}
    return Response(
        content, media_type=mt or "application/octet-stream", headers=headers
    )


@router.get("/{file_id}", summary="Get file by ID")
def get_file(
    file_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str | None]:
    """Get a file by its ID."""
    use_case = GetFileUseCase(_file_repo, _file_storage)
    result = use_case.execute(current_user.id().value(), file_id)
    if result.is_err():
        raise HTTPException(status_code=404, detail=result.err())
    result_data = result.ok()
    if result_data is None:
        raise HTTPException(status_code=404, detail="File not found")
    file, content = result_data
    dir_id = file.directory_id()
    return {
        "id": file.id().value(),
        "name": file.name(),
        "directory_id": dir_id.value() if dir_id is not None else None,
    }


@router.put("/{file_id}", summary="Update file")
def update_file(
    file_id: str,
    request: UpdateFileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Update file metadata."""
    use_case = UpdateFileUseCase(_file_repo)
    result = use_case.execute(
        current_user.id().value(),
        file_id,
        request.new_name,
        request.new_directory_id,
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "updated"}


@router.delete("/{file_id}", summary="Delete file")
def delete_file(
    file_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Delete a file by its ID."""
    use_case = DeleteFileUseCase(_file_repo, _file_storage)
    result = use_case.execute(current_user.id().value(), file_id)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    return {"status": "deleted"}
