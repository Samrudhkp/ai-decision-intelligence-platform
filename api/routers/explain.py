"""Explainability API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/explain", tags=["explain"])


@router.get("/shap")
def shap_summary() -> dict[str, Any]:
    path = Path("models/explainability/metadata.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Run SHAP explanations first")
    return json.loads(path.read_text(encoding="utf-8"))
