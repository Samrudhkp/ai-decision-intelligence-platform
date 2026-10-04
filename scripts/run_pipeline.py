#!/usr/bin/env python3
"""End-to-end local training pipeline + optional Azure Blob upload."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from src.churn.train import train_and_compare
from src.explainability.shap_explain import explain_predictions
from src.forecasting.baseline import fit_baseline
from src.forecasting.pytorch_model import fit_pytorch_forecaster
from src.segmentation.cluster import fit_segments
from src.utils.data_generation import write_datasets


def _maybe_load_env() -> None:
    for env_file in (Path(".azure-platform.env"), Path(".env")):
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Decision Intelligence Platform models")
    parser.add_argument("--upload-azure", action="store_true", help="Upload raw data + key artifacts to Blob")
    args = parser.parse_args()

    _maybe_load_env()
    paths = write_datasets()
    churn = train_and_compare(data_path=paths["churn"])
    segments = fit_segments(data_path=paths["churn"])
    baseline = fit_baseline(data_path=paths["revenue"])
    torch_forecast = fit_pytorch_forecaster(data_path=paths["revenue"])
    shap_meta = explain_predictions(data_path=paths["churn"])

    summary = {
        "datasets": {k: str(v) for k, v in paths.items()},
        "churn": churn,
        "segmentation": {"n_clusters": segments["n_clusters"], "profiles": segments["profiles"]},
        "forecast_baseline": baseline["metrics"],
        "forecast_pytorch": torch_forecast["metrics"],
        "shap_top_features": shap_meta["top_features"][:5],
    }

    if args.upload_azure:
        from src.utils.azure_storage import upload_processed_dataset, upload_raw_dataset

        uploaded = {
            "raw_churn": upload_raw_dataset(str(paths["churn"]), "customers_churn.csv"),
            "raw_revenue": upload_raw_dataset(str(paths["revenue"]), "monthly_revenue.csv"),
            "churn_comparison": upload_processed_dataset(
                "models/churn/comparison.json", "churn/comparison.json"
            ),
            "segment_profiles": upload_processed_dataset(
                "models/segmentation/segment_profiles.json",
                "segmentation/segment_profiles.json",
            ),
            "baseline_forecast": upload_processed_dataset(
                "models/forecasting/baseline_forecast.json",
                "forecasting/baseline_forecast.json",
            ),
            "pytorch_forecast": upload_processed_dataset(
                "models/forecasting/pytorch_forecast.json",
                "forecasting/pytorch_forecast.json",
            ),
            "shap_importance": upload_processed_dataset(
                "models/explainability/shap_feature_importance.json",
                "explainability/shap_feature_importance.json",
            ),
        }
        summary["azure_uploads"] = uploaded

    out = Path("models/pipeline_summary.json")
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
