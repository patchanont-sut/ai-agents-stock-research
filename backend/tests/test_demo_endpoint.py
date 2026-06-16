"""Smoke test for the demo endpoint."""
import sys

sys.path.insert(0, "backend")

from main import app
from fastapi.testclient import TestClient


def test_demo_endpoint_returns_200():
    """GET /api/demo/analysis returns 200 with key fields."""
    client = TestClient(app)
    response = client.get("/api/demo/analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["status"] == "complete"
    assert "cio_decision" in data
    assert "investment_memo" in data