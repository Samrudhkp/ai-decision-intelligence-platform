"""PyTorch neural-network revenue forecasting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mlflow
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from src.utils.mlflow_utils import configure_mlflow


class RevenueLSTM(nn.Module):
    def __init__(self, hidden_size: int = 32, num_layers: int = 1) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=1,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.head = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :])


def _make_windows(series: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []
    for i in range(len(series) - window):
        xs.append(series[i : i + window])
        ys.append(series[i + window])
    return np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.float32)


def fit_pytorch_forecaster(
    data_path: str | Path = "data/raw/monthly_revenue.csv",
    models_dir: str | Path = "models/forecasting",
    window: int = 12,
    horizon: int = 6,
    epochs: int = 80,
    lr: float = 1e-3,
    seed: int = 42,
    experiment_name: str = "decision-intelligence-forecasting",
) -> dict[str, Any]:
    """Train a small LSTM forecaster and persist weights + metrics."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    df = pd.read_csv(data_path, parse_dates=["month"]).sort_values("month")
    values = df["revenue"].to_numpy(dtype=np.float32)
    mean = float(values.mean())
    std = float(values.std() + 1e-6)
    scaled = (values - mean) / std

    if len(scaled) <= window + horizon + 2:
        raise ValueError("Not enough history for PyTorch forecaster.")

    train_series = scaled[:-horizon]
    x_train, y_train = _make_windows(train_series, window)
    dataset = TensorDataset(
        torch.from_numpy(x_train).unsqueeze(-1),
        torch.from_numpy(y_train).unsqueeze(-1),
    )
    loader = DataLoader(dataset, batch_size=8, shuffle=True)

    model = RevenueLSTM()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    model.train()
    for _ in range(epochs):
        for xb, yb in loader:
            opt.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            opt.step()

    # Recursive multi-step forecast on holdout start
    model.eval()
    history = list(train_series[-window:])
    preds_scaled: list[float] = []
    with torch.no_grad():
        for _ in range(horizon):
            inp = torch.tensor(history[-window:], dtype=torch.float32).view(1, window, 1)
            next_val = float(model(inp).item())
            preds_scaled.append(next_val)
            history.append(next_val)

    forecast = np.array(preds_scaled, dtype=np.float32) * std + mean
    actual = values[-horizon:]
    mae = float(np.mean(np.abs(forecast - actual)))
    mape = float(np.mean(np.abs((forecast - actual) / np.clip(actual, 1e-6, None))) * 100)

    # Future forecast beyond dataset end
    history = list(scaled[-window:])
    future_scaled: list[float] = []
    with torch.no_grad():
        for _ in range(horizon):
            inp = torch.tensor(history[-window:], dtype=torch.float32).view(1, window, 1)
            next_val = float(model(inp).item())
            future_scaled.append(next_val)
            history.append(next_val)
    future = np.array(future_scaled, dtype=np.float32) * std + mean
    future_months = pd.date_range(df["month"].iloc[-1] + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")

    out = Path(models_dir)
    out.mkdir(parents=True, exist_ok=True)
    weights_path = out / "pytorch_forecaster.pt"
    torch.save(
        {
            "state_dict": model.state_dict(),
            "mean": mean,
            "std": std,
            "window": window,
        },
        weights_path,
    )

    payload = {
        "model": "pytorch_lstm",
        "horizon": horizon,
        "window": window,
        "epochs": epochs,
        "metrics": {"mae": mae, "mape": mape},
        "holdout_forecast": forecast.tolist(),
        "holdout_actual": actual.tolist(),
        "future_forecast": [
            {"month": m.strftime("%Y-%m-%d"), "revenue": float(v)}
            for m, v in zip(future_months, future, strict=True)
        ],
        "weights_path": str(weights_path),
    }
    path = out / "pytorch_forecast.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    configure_mlflow(experiment_name=experiment_name)
    with mlflow.start_run(run_name="pytorch_lstm"):
        mlflow.log_params({"window": window, "horizon": horizon, "epochs": epochs, "lr": lr})
        mlflow.log_metrics({"mae": mae, "mape": mape})
        mlflow.log_artifact(str(path))

    payload["path"] = str(path)
    return payload


if __name__ == "__main__":
    print(json.dumps(fit_pytorch_forecaster(), indent=2))
