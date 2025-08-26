from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ...config import CONFIG

router = APIRouter(prefix="/stream", tags=["File Streaming"])

CLOUD_STORAGE_BASE_URL = f"https://storage.googleapis.com/{CONFIG.gcp_bucket_name}"


async def _proxy_gcp_file(request: Request, file_path: str) -> StreamingResponse:
    headers: dict[str, str] = {}
    range_header = request.headers.get("range")
    if range_header is not None:
        headers["Range"] = range_header
    file_url = f"{CLOUD_STORAGE_BASE_URL}/{file_path}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                file_url,
                headers=headers,
                stream=True,  # type: ignore[call-arg]
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    return StreamingResponse(
        response.aiter_bytes(),
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("Content-Type"),
    )


@router.get("/{file_path:path}", summary="Stream file from GCP")
async def stream_file_from_gcp(file_path: str, request: Request) -> StreamingResponse:
    return await _proxy_gcp_file(request, file_path)
