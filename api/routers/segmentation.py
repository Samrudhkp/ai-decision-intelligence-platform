"""Segmentation API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.segmentation.cluster import predict_segments

router = APIRouter(prefix="/segmentation", tags=["segmentation"])


class SegmentFeatures(BaseModel):
    tenure_months: int = Field(..., ge=0)
    monthly_charges: float
    total_charges: float
    contract_type: str
    internet_service: str
    support_tickets: int = Field(..., ge=0)
    payment_delay_days: float = Field(..., ge=0)


class SegmentRequest(BaseModel):
    records: list[SegmentFeatures]


@router.get("/profiles")
def segment_profiles() -> dict[str, Any]:
    path = Path("models/segmentation/segment_profiles.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fit segmentation first (scripts/run_pipeline.py)")
    return {"profiles": json.loads(path.read_text(encoding="utf-8"))}


@router.post("/predict")
def segment_predict(payload: SegmentRequest) -> dict[str, Any]:
    try:
        clusters = predict_segments([r.model_dump() for r in payload.records])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"clusters": clusters}
