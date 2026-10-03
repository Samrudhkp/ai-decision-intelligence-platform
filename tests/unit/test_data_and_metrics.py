"""Tests for synthetic data generation and churn evaluation helpers."""

from __future__ import annotations

from src.churn.train import evaluate_classifier
from src.utils.data_generation import generate_churn_dataset, generate_revenue_series


def test_generate_churn_dataset_shape() -> None:
    df = generate_churn_dataset(n_customers=100, seed=1)
    assert len(df) == 100
    assert "churned" in df.columns
    assert set(df["churned"].unique()).issubset({0, 1})


def test_generate_revenue_series() -> None:
    df = generate_revenue_series(n_months=24, seed=1)
    assert len(df) == 24
    assert (df["revenue"] > 0).all()


def test_evaluate_classifier_perfect() -> None:
    import numpy as np

    y = np.array([0, 1, 0, 1])
    p = np.array([0.1, 0.9, 0.2, 0.8])
    metrics = evaluate_classifier(y, p)
    assert metrics["accuracy"] == 1.0
    assert metrics["roc_auc"] == 1.0
