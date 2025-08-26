from __future__ import annotations

from typing import TYPE_CHECKING
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ...config import CONFIG

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from google.cloud import storage  # type: ignore[import-untyped]

router = APIRouter(prefix="/stream", tags=["File Streaming"])


def _get_gcp_client() -> "storage.Client":  # pragma: no cover - network
    from google.cloud import storage  # type: ignore[import-untyped]

    return storage.Client()


async def _stream_gcp_file(request: Request, file_id: str) -> StreamingResponse:
    """Stream file from GCP Storage using authenticated client with range support."""
    try:
        # Get range header for partial content support
        range_header = request.headers.get("range")

        # Use authenticated GCP client
        client = _get_gcp_client()
        bucket = client.bucket(CONFIG.gcp_bucket_name)
        blob = bucket.blob(file_id)

        # Check if blob exists
        if not blob.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

        # Get blob metadata
        blob.reload()
        content_type = blob.content_type or "application/octet-stream"
        content_length = blob.size

        # Handle range requests for video streaming
        if range_header:
            # Parse range header (e.g., "bytes=0-1023")
            range_match = range_header.replace("bytes=", "").split("-")
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else content_length - 1

            # Ensure end doesn't exceed file size
            end = min(end, content_length - 1)
            chunk_size = end - start + 1

            def generate_range():
                # Download the specific range
                data = blob.download_as_bytes(start=start, end=end + 1)
                yield data

            headers = {
                "Content-Range": f"bytes {start}-{end}/{content_length}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Type": content_type,
            }

            return StreamingResponse(
                generate_range(),
                status_code=206,  # Partial Content
                headers=headers,
                media_type=content_type,
            )
        else:
            # Stream entire file
            def generate_full():
                # Stream in chunks to avoid loading entire file in memory
                chunk_size = 8192  # 8KB chunks
                start = 0
                while start < content_length:
                    end = min(start + chunk_size - 1, content_length - 1)
                    chunk = blob.download_as_bytes(start=start, end=end + 1)
                    yield chunk
                    start = end + 1

            headers = {
                "Content-Length": str(content_length),
                "Accept-Ranges": "bytes",
                "Content-Type": content_type,
            }

            return StreamingResponse(
                generate_full(),
                status_code=200,
                headers=headers,
                media_type=content_type,
            )

    except Exception as exc:  # pragma: no cover - network
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(
            status_code=502, detail=f"Failed to stream file: {str(exc)}"
        ) from exc


@router.get("/{file_id:str}", summary="Stream file from GCP")
async def stream_file_from_gcp(file_id: str, request: Request) -> StreamingResponse:
    """Stream file from GCP Storage with range support for video playback."""
    return await _stream_gcp_file(request, file_id)
