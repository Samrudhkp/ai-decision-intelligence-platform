"""Baseline revenue forecasting (seasonal naive / moving average hybrid)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def fit_baseline(
    data_path: str | Path = "data/raw/monthly_revenue.csv",
    models_dir: str | Path = "models/forecasting",
    horizon: int = 6,
    season_length: int = 12,
) -> dict[str, Any]:
    """Fit a seasonal-naive baseline and evaluate on a holdout tail."""
    df = pd.read_csv(data_path, parse_dates=["month"]).sort_values("month")
    values = df["revenue"].to_numpy(dtype=float)

    if len(values) <= horizon + season_length:
        raise ValueError("Not enough history for seasonal baseline evaluation.")

    train = values[:-horizon]
    actual = values[-horizon:]
    # Seasonal naive: y_hat(t) = y(t - season)
    forecast = train[-season_length : -season_length + horizon]
    if len(forecast) < horizon:
        # fallback: repeat last seasonal cycle
        cycle = train[-season_length:]
        forecast = np.resize(cycle, horizon)

    mae = float(np.mean(np.abs(forecast - actual)))
    mape = float(np.mean(np.abs((forecast - actual) / np.clip(actual, 1e-6, None))) * 100)

    last_cycle = values[-season_length:]
    future = np.resize(last_cycle, horizon)
    future_months = pd.date_range(df["month"].iloc[-1] + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")

    out = Path(models_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": "seasonal_naive_baseline",
        "horizon": horizon,
        "season_length": season_length,
        "metrics": {"mae": mae, "mape": mape},
        "holdout_forecast": forecast.tolist(),
        "holdout_actual": actual.tolist(),
        "future_forecast": [
            {"month": m.strftime("%Y-%m-%d"), "revenue": float(v)}
            for m, v in zip(future_months, future, strict=True)
        ],
    }
    path = out / "baseline_forecast.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["path"] = str(path)
    return payload


if __name__ == "__main__":
    print(json.dumps(fit_baseline(), indent=2))
