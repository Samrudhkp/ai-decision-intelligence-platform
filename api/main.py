"""FastAPI application entrypoint.

Prediction routers will be registered in later phases.
Run (after install): uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI

from api.routers import health

app = FastAPI(
    title="Decision Intelligence Platform API",
    description=(
        "Enterprise AI forecasting and decision intelligence API. "
        "Endpoints for churn, segmentation, forecasting, and SHAP explanations "
        "will be added as models are implemented."
    ),
    version="0.1.0",
)

app.include_router(health.router)


@app.get("/")
def root() -> dict[str, str]:
    """API root — confirms the service is reachable."""
    return {
        "service": "decision-intelligence-platform",
        "status": "ok",
        "docs": "/docs",
    }
