"""Synthetic dataset generators for local + Azure Blob demos."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate_churn_dataset(n_customers: int = 2000, seed: int = 42) -> pd.DataFrame:
    """Create a fictional telecom-style churn dataset."""
    rng = np.random.default_rng(seed)
    tenure = rng.integers(1, 72, size=n_customers)
    monthly_charges = rng.normal(70, 25, size=n_customers).clip(20, 150)
    total_charges = monthly_charges * tenure * rng.uniform(0.85, 1.1, size=n_customers)
    contract = rng.choice(["month-to-month", "one-year", "two-year"], size=n_customers, p=[0.55, 0.25, 0.20])
    internet = rng.choice(["dsl", "fiber", "none"], size=n_customers, p=[0.35, 0.45, 0.20])
    support_tickets = rng.poisson(1.2, size=n_customers)
    payment_delay_days = rng.exponential(3.0, size=n_customers).clip(0, 45)

    # Latent churn propensity
    logit = (
        -1.8
        + 0.035 * (monthly_charges - 70)
        - 0.04 * tenure
        + 0.35 * (contract == "month-to-month")
        + 0.25 * (internet == "fiber")
        + 0.28 * support_tickets
        + 0.04 * payment_delay_days
    )
    prob = 1 / (1 + np.exp(-logit))
    churned = (rng.random(n_customers) < prob).astype(int)

    return pd.DataFrame(
        {
            "customer_id": [f"C{100000 + i}" for i in range(n_customers)],
            "tenure_months": tenure,
            "monthly_charges": np.round(monthly_charges, 2),
            "total_charges": np.round(total_charges, 2),
            "contract_type": contract,
            "internet_service": internet,
            "support_tickets": support_tickets,
            "payment_delay_days": np.round(payment_delay_days, 2),
            "churned": churned,
        }
    )


def generate_revenue_series(n_months: int = 48, seed: int = 7) -> pd.DataFrame:
    """Create a monthly revenue time series with trend + seasonality + noise."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2022-01-01", periods=n_months, freq="MS")
    t = np.arange(n_months)
    trend = 120_000 + 1_800 * t
    seasonality = 8_000 * np.sin(2 * np.pi * t / 12)
    noise = rng.normal(0, 3_500, size=n_months)
    revenue = np.maximum(trend + seasonality + noise, 50_000)
    return pd.DataFrame({"month": dates, "revenue": np.round(revenue, 2)})


def write_datasets(raw_dir: str | Path = "data/raw") -> dict[str, Path]:
    """Write synthetic CSVs under data/raw and return their paths."""
    out = Path(raw_dir)
    out.mkdir(parents=True, exist_ok=True)
    churn_path = out / "customers_churn.csv"
    revenue_path = out / "monthly_revenue.csv"
    generate_churn_dataset().to_csv(churn_path, index=False)
    generate_revenue_series().to_csv(revenue_path, index=False)
    return {"churn": churn_path, "revenue": revenue_path}


if __name__ == "__main__":
    paths = write_datasets()
    for name, path in paths.items():
        print(f"{name}: {path} ({path.stat().st_size} bytes)")
