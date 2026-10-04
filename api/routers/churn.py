"""Churn prediction API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.churn.train import FEATURE_COLUMNS, predict_churn

router = APIRouter(prefix="/churn", tags=["churn"])


class ChurnFeatures(BaseModel):
    tenure_months: int = Field(..., ge=0)
    monthly_charges: float
    total_charges: float
    contract_type: str
    internet_service: str
    support_tickets: int = Field(..., ge=0)
    payment_delay_days: float = Field(..., ge=0)


class ChurnRequest(BaseModel):
    records: list[ChurnFeatures]


@router.get("/metrics")
def churn_metrics() -> dict[str, Any]:
    path = Path("models/churn/comparison.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Train churn models first (scripts/run_pipeline.py)")
    return {"metrics": json.loads(path.read_text(encoding="utf-8"))}


@router.post("/predict")
def churn_predict(payload: ChurnRequest) -> dict[str, Any]:
    try:
        records = [r.model_dump() for r in payload.records]
        preds = predict_churn(records)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"feature_columns": FEATURE_COLUMNS, "predictions": preds}
