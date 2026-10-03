"""Azure Blob Storage helpers (skeleton — no credentials in code).

Use environment variables from `.env` / Azure authentication:
- Preferred: DefaultAzureCredential (az login, managed identity, SP env vars)
- Optional local/dev: AZURE_STORAGE_CONNECTION_STRING
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from azure.storage.blob import BlobServiceClient


def get_blob_service_client() -> "BlobServiceClient":
    """Build a BlobServiceClient from environment / DefaultAzureCredential.

    Implementation will be completed when Azure integration is wired up.
    Raises NotImplementedError until that phase.
    """
    raise NotImplementedError(
        "Azure Blob client will be implemented in the Azure integration phase. "
        "Configure AZURE_STORAGE_* via .env — never hard-code secrets."
    )


def upload_raw_dataset(local_path: str, blob_name: str) -> None:
    """Upload a local file to the configured raw-datasets container."""
    raise NotImplementedError("Deferred to Azure integration phase.")


def download_raw_dataset(blob_name: str, local_path: str) -> None:
    """Download a blob from the raw-datasets container to a local path."""
    raise NotImplementedError("Deferred to Azure integration phase.")
