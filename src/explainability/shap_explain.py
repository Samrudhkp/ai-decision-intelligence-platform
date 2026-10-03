"""SHAP explanation helpers for the churn model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from src.churn.train import FEATURE_COLUMNS


def explain_predictions(
    data_path: str | Path = "data/raw/customers_churn.csv",
    models_dir: str | Path = "models/churn",
    output_dir: str | Path = "models/explainability",
    sample_size: int = 200,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute SHAP values for the best churn model and save summary artifacts."""
    model_path = Path(models_dir) / "best_model.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Missing churn model at {model_path}")

    pipe = joblib.load(model_path)
    df = pd.read_csv(data_path)
    sample = df.sample(n=min(sample_size, len(df)), random_state=seed)
    x = sample[FEATURE_COLUMNS]

    # Transform features, then explain the classifier on the matrix
    x_transformed = pipe.named_steps["preprocess"].transform(x)
    if hasattr(x_transformed, "toarray"):
        x_transformed = x_transformed.toarray()
    feature_names = list(pipe.named_steps["preprocess"].get_feature_names_out())
    classifier = pipe.named_steps["model"]

    # TreeExplainer for RF/XGB; LinearExplainer fallback for logistic regression
    model_name = type(classifier).__name__.lower()
    if "logistic" in model_name:
        explainer = shap.LinearExplainer(classifier, x_transformed)
        raw_shap = explainer.shap_values(x_transformed)
    else:
        explainer = shap.TreeExplainer(classifier)
        raw_shap = explainer.shap_values(x_transformed)

    if isinstance(raw_shap, list):
        shap_values = np.asarray(raw_shap[1] if len(raw_shap) > 1 else raw_shap[0])
    else:
        shap_values = np.asarray(raw_shap)

    # Newer SHAP may return (n_samples, n_features, n_classes)
    if shap_values.ndim == 3:
        shap_values = shap_values[:, :, -1]
    if shap_values.ndim != 2:
        raise ValueError(f"Unexpected SHAP shape: {shap_values.shape}")

    mean_abs = np.abs(shap_values).mean(axis=0)
    importance = (
        pd.DataFrame({"feature": feature_names, "mean_abs_shap": mean_abs})
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    importance_path = out / "shap_feature_importance.json"
    importance_path.write_text(
        importance.head(20).to_json(orient="records", indent=2),
        encoding="utf-8",
    )

    plt.figure(figsize=(8, 5))
    top = importance.head(12).iloc[::-1]
    plt.barh(top["feature"], top["mean_abs_shap"], color="#1f6f8b")
    plt.xlabel("Mean |SHAP|")
    plt.title("Churn model — top SHAP features")
    plt.tight_layout()
    plot_path = out / "shap_summary.png"
    plt.savefig(plot_path, dpi=140)
    plt.close()

    # One local explanation example
    local_idx = 0
    local = {
        "customer_id": str(sample.iloc[local_idx].get("customer_id", local_idx)),
        "top_features": [
            {
                "feature": feature_names[i],
                "shap_value": float(np.asarray(shap_values)[local_idx, i]),
            }
            for i in np.argsort(-np.abs(np.asarray(shap_values)[local_idx]))[:8]
        ],
    }
    local_path = out / "shap_local_example.json"
    local_path.write_text(json.dumps(local, indent=2), encoding="utf-8")

    meta = {
        "importance_path": str(importance_path),
        "plot_path": str(plot_path),
        "local_example_path": str(local_path),
        "top_features": importance.head(10).to_dict(orient="records"),
        "local_example": local,
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


if __name__ == "__main__":
    print(json.dumps(explain_predictions(), indent=2))
