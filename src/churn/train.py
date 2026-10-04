"""Customer churn training and model comparison."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd

from src.utils.mlflow_utils import configure_mlflow
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

FEATURE_COLUMNS = [
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "contract_type",
    "internet_service",
    "support_tickets",
    "payment_delay_days",
]
TARGET_COLUMN = "churned"
CATEGORICAL = ["contract_type", "internet_service"]
NUMERIC = [
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "support_tickets",
    "payment_delay_days",
]


def _preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ]
    )


def _models(seed: int = 42, scale_pos_weight: float = 1.0) -> dict[str, Any]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=seed
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=250,
            max_depth=10,
            class_weight="balanced_subsample",
            random_state=seed,
            n_jobs=-1,
        ),
        "xgboost": XGBClassifier(
            n_estimators=250,
            max_depth=5,
            learning_rate=0.07,
            subsample=0.9,
            colsample_bytree=0.9,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=seed,
            n_jobs=-1,
        ),
    }


def evaluate_classifier(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    y_pred = (y_prob >= 0.5).astype(int)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
    }


def train_and_compare(
    data_path: str | Path = "data/raw/customers_churn.csv",
    models_dir: str | Path = "models/churn",
    experiment_name: str = "decision-intelligence-churn",
    test_size: float = 0.2,
    seed: int = 42,
) -> dict[str, Any]:
    """Train LR / RF / XGBoost, compare metrics, persist best model + comparison."""
    df = pd.read_csv(data_path)
    x = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=test_size, random_state=seed, stratify=y
    )

    out_dir = Path(models_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Handle class imbalance for a more useful recall/F1 tradeoff
    pos = max(int((y_train == 1).sum()), 1)
    neg = max(int((y_train == 0).sum()), 1)
    scale_pos_weight = neg / pos

    configure_mlflow(experiment_name=experiment_name)
    comparison: list[dict[str, Any]] = []
    fitted: dict[str, Pipeline] = {}

    for name, estimator in _models(seed, scale_pos_weight=scale_pos_weight).items():
        pipe = Pipeline(
            steps=[
                ("preprocess", _preprocessor()),
                ("model", estimator),
            ]
        )
        with mlflow.start_run(run_name=name):
            pipe.fit(x_train, y_train)
            proba = pipe.predict_proba(x_test)[:, 1]
            metrics = evaluate_classifier(y_test.to_numpy(), proba)
            mlflow.log_params({"model": name, "test_size": test_size, "seed": seed})
            mlflow.log_metrics(metrics)
            mlflow.sklearn.log_model(pipe, artifact_path="model")
            joblib.dump(pipe, out_dir / f"{name}.joblib")
            fitted[name] = pipe
            comparison.append({"model": name, **metrics})

    comparison_df = pd.DataFrame(comparison).sort_values("roc_auc", ascending=False)
    best_name = str(comparison_df.iloc[0]["model"])
    best_path = out_dir / "best_model.joblib"
    joblib.dump(fitted[best_name], best_path)
    comparison_path = out_dir / "comparison.json"
    comparison_path.write_text(
        comparison_df.to_json(orient="records", indent=2),
        encoding="utf-8",
    )
    meta = {
        "best_model": best_name,
        "best_model_path": str(best_path),
        "comparison_path": str(comparison_path),
        "feature_columns": FEATURE_COLUMNS,
        "metrics": comparison_df.to_dict(orient="records"),
    }
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def load_churn_model(models_dir: str | Path = "models/churn") -> Any:
    path = Path(models_dir) / "best_model.joblib"
    if not path.exists():
        raise FileNotFoundError(f"No trained churn model at {path}. Run train_and_compare first.")
    return joblib.load(path)


def predict_churn(records: list[dict[str, Any]], models_dir: str | Path = "models/churn") -> list[dict[str, Any]]:
    model = load_churn_model(models_dir)
    frame = pd.DataFrame(records)
    missing = [c for c in FEATURE_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"Missing features: {missing}")
    proba = model.predict_proba(frame[FEATURE_COLUMNS])[:, 1]
    preds = (proba >= 0.5).astype(int)
    return [
        {
            "churn_probability": float(p),
            "churn_predicted": int(y),
        }
        for p, y in zip(proba, preds, strict=True)
    ]


if __name__ == "__main__":
    result = train_and_compare()
    print(json.dumps(result, indent=2))
