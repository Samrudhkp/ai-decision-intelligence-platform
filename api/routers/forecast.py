"""Forecasting API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/baseline")
def baseline_forecast() -> dict[str, Any]:
    path = Path("models/forecasting/baseline_forecast.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Run baseline forecasting first")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/pytorch")
def pytorch_forecast() -> dict[str, Any]:
    path = Path("models/forecasting/pytorch_forecast.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Run PyTorch forecasting first")
    return json.loads(path.read_text(encoding="utf-8"))
