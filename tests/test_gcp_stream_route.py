import httpx
from fastapi.testclient import TestClient

from codebase_to_llm.interface.fastapi.app import app


class _DummyResponse:
    def __init__(self, content: bytes) -> None:
        self.status_code = 200
        self.headers = {"Content-Type": "video/mp4"}
        self._content = content

    async def aiter_bytes(self):
        yield self._content

    def raise_for_status(self) -> None:
        return None


def test_stream_file_from_gcp(monkeypatch):
    async def _mock_get(
        self, url: str, headers: dict | None = None, stream: bool = False
    ):
        return _DummyResponse(b"data")

    monkeypatch.setattr(httpx.AsyncClient, "get", _mock_get)
    client = TestClient(app)
    response = client.get("/stream/sample.mp4")
    assert response.status_code == 200
    assert response.content == b"data"
    assert response.headers["Content-Type"] == "video/mp4"
