"""Shared HTTP client for market data providers."""
from __future__ import annotations

import httpx

_client: httpx.AsyncClient | None = None


def get_data_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=15.0)
    return _client


async def close_data_http_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
