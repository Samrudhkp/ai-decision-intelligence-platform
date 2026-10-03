"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from api.routers import churn, explain, forecast, health, segmentation

app = FastAPI(
    title="Decision Intelligence Platform API",
    description=(
        "Enterprise AI forecasting and decision intelligence API: "
        "churn, segmentation, forecasting, and SHAP explanations."
    ),
    version="0.2.0",
)

app.include_router(health.router)
app.include_router(churn.router)
app.include_router(segmentation.router)
app.include_router(forecast.router)
app.include_router(explain.router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "decision-intelligence-platform",
        "status": "ok",
        "docs": "/docs",
    }
