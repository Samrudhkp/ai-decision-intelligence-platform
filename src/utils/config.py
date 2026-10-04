"""Application settings loaded from environment variables / .env.

Credentials are never hard-coded. Azure auth prefers DefaultAzureCredential
(Azure CLI, managed identity, or service principal via AZURE_* env vars).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for API, dashboard, MLflow, and Azure."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "decision-intelligence-platform"
    app_env: str = "development"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    streamlit_port: int = 8501

    mlflow_tracking_uri: str = "http://127.0.0.1:5000"
    mlflow_experiment_name: str = "decision-intelligence"

    data_raw_dir: Path = Path("data/raw")
    data_processed_dir: Path = Path("data/processed")
    models_dir: Path = Path("models")

    azure_storage_account_name: str | None = None
    azure_storage_container_raw: str = "raw-datasets"
    azure_storage_container_processed: str = "processed-datasets"
    azure_storage_connection_string: str | None = None
    azure_storage_account_url: str | None = None

    azure_subscription_id: str | None = None
    azure_resource_group: str | None = None
    azure_ml_workspace_name: str | None = None
    azure_ml_workspace_region: str | None = None

    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
