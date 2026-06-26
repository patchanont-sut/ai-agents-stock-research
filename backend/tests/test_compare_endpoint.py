"""Smoke tests for comparison endpoints."""
from __future__ import annotations

import sys

sys.path.insert(0, "backend")

from fastapi.testclient import TestClient

from core.models import AnalysisStatus, CompareResult, CompareStockSummary
import main as main_module
from main import app


def clear_comparison_state() -> None:
    main_module._comparison_store.clear()
    main_module._comparison_progress.clear()


def test_compare_start_rejects_duplicate_symbols_after_normalization():
    client = TestClient(app)

    response = client.post(
        "/api/compare",
        json={"symbols": ["AAPL", " aapl "], "language": "en"},
    )

    assert response.status_code == 400
    assert "Duplicate" in response.json()["detail"]


def test_compare_start_normalizes_symbols_and_completes_fake_pipeline(monkeypatch):
    async def fake_run_comparison_pipeline(symbols: list[str], compare_id: str, language: str = "en") -> None:
        main_module._comparison_progress[compare_id] = {
            symbol: [f"analysis-{symbol}", "complete"] for symbol in symbols
        }
        main_module._comparison_store[compare_id] = CompareResult(
            id=compare_id,
            symbols=symbols,
            status=AnalysisStatus.COMPLETE,
            winner_symbol="AAPL",
            ranking_rationale="Ranking rationale: AAPL leads on confidence.",
            summaries=[
                CompareStockSummary(symbol="AAPL", cio_action="BUY"),
                CompareStockSummary(symbol="MSFT", cio_action="HOLD"),
            ],
            comparison_table=[
                {"symbol": "AAPL", "action": "BUY"},
                {"symbol": "MSFT", "action": "HOLD"},
            ],
            errors=[],
        )

    monkeypatch.setattr(main_module, "run_comparison_pipeline", fake_run_comparison_pipeline)
    clear_comparison_state()
    client = TestClient(app)

    response = client.post(
        "/api/compare",
        json={"symbols": [" aapl ", "MSFT"], "language": "en"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["symbols"] == ["AAPL", "MSFT"]

    compare_id = data["compare_id"]

    status_response = client.get(f"/api/compare/{compare_id}/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] == "complete"
    assert status_data["completed_symbols"] == ["AAPL", "MSFT"]
    assert status_data["symbol_progress"]["AAPL"][1] == "complete"

    result_response = client.get(f"/api/compare/{compare_id}/result")
    assert result_response.status_code == 200
    result_data = result_response.json()
    assert result_data["winner_symbol"] == "AAPL"
    assert result_data["summaries"][0]["symbol"] == "AAPL"
    assert result_data["summaries"][1]["symbol"] == "MSFT"


def test_compare_result_returns_202_while_pending():
    clear_comparison_state()
    compare_id = "compare-pending"
    main_module._comparison_store[compare_id] = CompareResult(
        id=compare_id,
        symbols=["AAPL", "MSFT"],
        status=AnalysisStatus.RUNNING,
    )

    client = TestClient(app)
    response = client.get(f"/api/compare/{compare_id}/result")

    assert response.status_code == 202
    assert "still in progress" in response.json()["detail"]
