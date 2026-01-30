import pytest
import httpx
from app.agents.reasoning_agent import ReasoningAgent

class FailingTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request):
        raise httpx.ConnectError("connection failed")


@pytest.mark.anyio
async def test_ollama_fallback_after_retries(monkeypatch):
    agent = ReasoningAgent()
    OriginalAsyncClient = httpx.AsyncClient
    def mock_client(*args, **kwargs):
        return OriginalAsyncClient(transport=CountingTransport())

    monkeypatch.setattr(httpx, "AsyncClient", mock_client)

    result = await agent.reason("test query", [])

    assert result["confidence"] == 0.0
    assert "temporarily unavailable" in result["answer"].lower()

@pytest.mark.anyio
async def test_retry_attempts(monkeypatch):
    agent = ReasoningAgent()
    calls = {"count": 0}

    class CountingTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            calls["count"] += 1
            raise httpx.ConnectError("fail")
    OriginalAsyncClient = httpx.AsyncClient
    def mock_client(*args, **kwargs):
        return OriginalAsyncClient(transport=CountingTransport())

    monkeypatch.setattr(httpx, "AsyncClient", mock_client)

    await agent.reason("x", [])

    assert calls["count"] == 3
