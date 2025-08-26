from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from codebase_to_llm.interface.fastapi.app import app


class _MockBlob:
    def __init__(self, content: bytes, content_type: str = "video/mp4") -> None:
        self.content = content
        self.content_type = content_type
        self.size = len(content)

    def exists(self) -> bool:
        return True

    def reload(self) -> None:
        pass

    def download_as_bytes(self, start: int = 0, end: int | None = None) -> bytes:
        if end is None:
            return self.content[start:]
        return self.content[start:end]


def test_stream_file_from_gcp(monkeypatch):
    """Test streaming a file from GCP Storage."""
    mock_blob = _MockBlob(b"test video data")
    mock_bucket = Mock()
    mock_bucket.blob.return_value = mock_blob
    mock_client = Mock()
    mock_client.bucket.return_value = mock_bucket

    with patch(
        "codebase_to_llm.interface.fastapi.stream._get_gcp_client",
        return_value=mock_client,
    ):
        client = TestClient(app)
        response = client.get("/stream/sample.mp4")

        assert response.status_code == 200
        assert response.content == b"test video data"
        assert response.headers["Content-Type"] == "video/mp4"
        assert "Accept-Ranges" in response.headers
        assert response.headers["Accept-Ranges"] == "bytes"


def test_stream_file_from_gcp_with_range(monkeypatch):
    """Test streaming a file from GCP Storage with range request."""
    mock_blob = _MockBlob(b"0123456789abcdef")
    mock_bucket = Mock()
    mock_bucket.blob.return_value = mock_blob
    mock_client = Mock()
    mock_client.bucket.return_value = mock_bucket

    with patch(
        "codebase_to_llm.interface.fastapi.stream._get_gcp_client",
        return_value=mock_client,
    ):
        client = TestClient(app)
        response = client.get("/stream/sample.mp4", headers={"Range": "bytes=0-7"})

        assert response.status_code == 206  # Partial Content
        assert response.content == b"01234567"
        assert response.headers["Content-Type"] == "video/mp4"
        assert "Content-Range" in response.headers
        assert response.headers["Content-Range"] == "bytes 0-7/16"


def test_stream_file_not_found(monkeypatch):
    """Test streaming a non-existent file."""
    mock_blob = Mock()
    mock_blob.exists.return_value = False
    mock_bucket = Mock()
    mock_bucket.blob.return_value = mock_blob
    mock_client = Mock()
    mock_client.bucket.return_value = mock_bucket

    with patch(
        "codebase_to_llm.interface.fastapi.stream._get_gcp_client",
        return_value=mock_client,
    ):
        client = TestClient(app)
        response = client.get("/stream/nonexistent.mp4")

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
