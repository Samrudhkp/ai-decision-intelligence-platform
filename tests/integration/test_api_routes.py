"""API integration tests for trained-model routes."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
MODELS_READY = Path("models/churn/comparison.json").exists()


@pytest.mark.skipif(not MODELS_READY, reason="Train models first via scripts/run_pipeline.py")
def test_churn_metrics() -> None:
    response = client.get("/churn/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "metrics" in body
    assert len(body["metrics"]) >= 3


@pytest.mark.skipif(not MODELS_READY, reason="Train models first via scripts/run_pipeline.py")
def test_churn_predict() -> None:
    payload = {
        "records": [
            {
                "tenure_months": 4,
                "monthly_charges": 110,
                "total_charges": 400,
                "contract_type": "month-to-month",
                "internet_service": "fiber",
                "support_tickets": 5,
                "payment_delay_days": 14,
            }
        ]
    }
    response = client.post("/churn/predict", json=payload)
    assert response.status_code == 200
    pred = response.json()["predictions"][0]
    assert 0.0 <= pred["churn_probability"] <= 1.0


@pytest.mark.skipif(
    not Path("models/segmentation/segment_profiles.json").exists(),
    reason="Fit segmentation first",
)
def test_segmentation_profiles() -> None:
    response = client.get("/segmentation/profiles")
    assert response.status_code == 200
    assert len(response.json()["profiles"]) >= 1


@pytest.mark.skipif(
    not Path("models/forecasting/pytorch_forecast.json").exists(),
    reason="Train forecaster first",
)
def test_forecast_pytorch() -> None:
    response = client.get("/forecast/pytorch")
    assert response.status_code == 200
    assert "metrics" in response.json()


@pytest.mark.skipif(
    not Path("models/explainability/metadata.json").exists(),
    reason="Run SHAP first",
)
def test_explain_shap() -> None:
    response = client.get("/explain/shap")
    assert response.status_code == 200
    assert "top_features" in response.json()
