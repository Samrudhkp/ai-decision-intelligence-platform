"""K-Means customer segmentation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FEATURE_COLUMNS = [
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "contract_type",
    "internet_service",
    "support_tickets",
    "payment_delay_days",
]
CATEGORICAL = ["contract_type", "internet_service"]
NUMERIC = [
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "support_tickets",
    "payment_delay_days",
]


def _pipeline(n_clusters: int, seed: int) -> Pipeline:
    pre = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", pre),
            ("kmeans", KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)),
        ]
    )


def _segment_name(row: pd.Series) -> str:
    """Label a cluster from its aggregate profile (order matters)."""
    if row["churn_rate"] >= 0.18 and row["monthly_charges"] >= 70:
        return "high_value_at_risk"
    if row["tenure_months"] >= 45 and row["monthly_charges"] >= 70:
        return "loyal_premium"
    if row["tenure_months"] <= 20:
        return "new_customers"
    if row["monthly_charges"] < 55:
        return "value_seekers"
    return "steady_core"


def fit_segments(
    data_path: str | Path = "data/raw/customers_churn.csv",
    models_dir: str | Path = "models/segmentation",
    n_clusters: int = 4,
    seed: int = 42,
    experiment_name: str = "decision-intelligence-segmentation",
) -> dict[str, Any]:
    """Fit K-Means and write cluster labels + profiles."""
    df = pd.read_csv(data_path)
    pipe = _pipeline(n_clusters, seed)
    labels = pipe.fit_predict(df[FEATURE_COLUMNS])
    labeled = df.copy()
    labeled["cluster"] = labels

    profiles = (
        labeled.groupby("cluster")
        .agg(
            customers=("customer_id", "count"),
            tenure_months=("tenure_months", "mean"),
            monthly_charges=("monthly_charges", "mean"),
            total_charges=("total_charges", "mean"),
            support_tickets=("support_tickets", "mean"),
            payment_delay_days=("payment_delay_days", "mean"),
            churn_rate=("churned", "mean"),
        )
        .reset_index()
    )
    profiles["segment_name"] = profiles.apply(_segment_name, axis=1)

    out = Path(models_dir)
    out.mkdir(parents=True, exist_ok=True)
    model_path = out / "kmeans.joblib"
    labels_path = out / "cluster_assignments.csv"
    profiles_path = out / "segment_profiles.json"

    joblib.dump(pipe, model_path)
    labeled[["customer_id", "cluster"]].to_csv(labels_path, index=False)
    profiles_records = profiles.round(3).to_dict(orient="records")
    profiles_path.write_text(json.dumps(profiles_records, indent=2), encoding="utf-8")

    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=f"kmeans_k{n_clusters}"):
        mlflow.log_params({"n_clusters": n_clusters, "seed": seed})
        mlflow.log_metric("inertia", float(pipe.named_steps["kmeans"].inertia_))
        mlflow.log_artifact(str(profiles_path))

    meta = {
        "model_path": str(model_path),
        "labels_path": str(labels_path),
        "profiles_path": str(profiles_path),
        "n_clusters": n_clusters,
        "profiles": profiles_records,
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def predict_segments(records: list[dict[str, Any]], models_dir: str | Path = "models/segmentation") -> list[int]:
    model_path = Path(models_dir) / "kmeans.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"No segmentation model at {model_path}")
    pipe = joblib.load(model_path)
    frame = pd.DataFrame(records)
    return [int(x) for x in pipe.predict(frame[FEATURE_COLUMNS])]


if __name__ == "__main__":
    print(json.dumps(fit_segments(), indent=2))
