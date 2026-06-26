"""Smoke tests for the health endpoint."""
import sys

sys.path.insert(0, "backend")

from fastapi.testclient import TestClient

from main import app


def test_health_endpoint_returns_expected_metadata():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "MarketMind AI Dashboard",
        "version": "1.0.0",
    }
