"""MLflow tracking helpers (local directory or Azure ML workspace URI)."""

from __future__ import annotations

import os
from pathlib import Path

import mlflow

from src.utils.config import get_settings


def configure_mlflow(tracking_uri: str | None = None, experiment_name: str | None = None) -> str:
    """Configure MLflow tracking.

    Priority:
    1. Explicit tracking_uri argument
    2. MLFLOW_TRACKING_URI env / settings
    3. Azure ML workspace MLflow URI when AZURE_ML_TRACKING_URI is set
    4. Local ./mlruns
    """
    settings = get_settings()
    uri = (
        tracking_uri
        or os.environ.get("AZURE_ML_TRACKING_URI")
        or settings.mlflow_tracking_uri
        or "file:./mlruns"
    )
    # Prefer file store when the configured HTTP URI is the local default and unused
    if uri.startswith("http://127.0.0.1") and not os.environ.get("MLFLOW_FORCE_HTTP"):
        uri = "file:./mlruns"
    Path("mlruns").mkdir(exist_ok=True)
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(experiment_name or settings.mlflow_experiment_name)
    return uri
