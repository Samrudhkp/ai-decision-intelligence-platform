"""Azure Blob Storage helpers.

Credentials are never hard-coded. Resolution order:
1. AZURE_STORAGE_CONNECTION_STRING (local/dev only)
2. AZURE_STORAGE_ACCOUNT_URL (or name) + DefaultAzureCredential
   (az login, managed identity, or AZURE_CLIENT_ID / SECRET / TENANT_ID)
"""

from __future__ import annotations

import os
from pathlib import Path

from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    EnvironmentCredential,
    ManagedIdentityCredential,
)
from azure.storage.blob import BlobServiceClient

from src.utils.config import get_settings


def _credential() -> ChainedTokenCredential:
    """Prefer env SP / CLI login; avoid long IMDS hangs in local/dev VMs."""
    chain: list[object] = []
    if (
        os.environ.get("AZURE_TENANT_ID")
        and os.environ.get("AZURE_CLIENT_ID")
        and os.environ.get("AZURE_CLIENT_SECRET")
    ):
        chain.append(EnvironmentCredential())
    chain.append(AzureCliCredential())
    chain.append(ManagedIdentityCredential())
    return ChainedTokenCredential(*chain)  # type: ignore[arg-type]


def get_blob_service_client() -> BlobServiceClient:
    """Build a BlobServiceClient from environment / Azure CLI / managed identity."""
    settings = get_settings()

    if settings.azure_storage_connection_string:
        return BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )

    account_url = settings.azure_storage_account_url
    if not account_url and settings.azure_storage_account_name:
        account_url = (
            f"https://{settings.azure_storage_account_name}.blob.core.windows.net"
        )

    if not account_url:
        raise RuntimeError(
            "Set AZURE_STORAGE_ACCOUNT_URL or AZURE_STORAGE_ACCOUNT_NAME "
            "(and authenticate via az login / managed identity / service principal). "
            "Optionally set AZURE_STORAGE_CONNECTION_STRING for local/dev only."
        )

    return BlobServiceClient(account_url=account_url, credential=_credential())


def upload_blob(
    local_path: str | Path,
    blob_name: str,
    *,
    container: str | None = None,
) -> str:
    """Upload a local file to a container. Returns the blob URL."""
    settings = get_settings()
    container_name = container or settings.azure_storage_container_raw
    path = Path(local_path)
    if not path.is_file():
        raise FileNotFoundError(f"Local file not found: {path}")

    client = get_blob_service_client()
    blob = client.get_blob_client(container=container_name, blob=blob_name)
    with path.open("rb") as handle:
        blob.upload_blob(handle, overwrite=True)
    return blob.url


def download_blob(
    blob_name: str,
    local_path: str | Path,
    *,
    container: str | None = None,
) -> Path:
    """Download a blob to a local path. Returns the local Path."""
    settings = get_settings()
    container_name = container or settings.azure_storage_container_raw
    destination = Path(local_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    client = get_blob_service_client()
    blob = client.get_blob_client(container=container_name, blob=blob_name)
    with destination.open("wb") as handle:
        download = blob.download_blob()
        handle.write(download.readall())
    return destination


def upload_raw_dataset(local_path: str, blob_name: str) -> str:
    """Upload a local file to the configured raw-datasets container."""
    settings = get_settings()
    return upload_blob(
        local_path,
        blob_name,
        container=settings.azure_storage_container_raw,
    )


def download_raw_dataset(blob_name: str, local_path: str) -> Path:
    """Download a blob from the raw-datasets container to a local path."""
    settings = get_settings()
    return download_blob(
        blob_name,
        local_path,
        container=settings.azure_storage_container_raw,
    )


def upload_processed_dataset(local_path: str, blob_name: str) -> str:
    """Upload a local file to the configured processed-datasets container."""
    settings = get_settings()
    return upload_blob(
        local_path,
        blob_name,
        container=settings.azure_storage_container_processed,
    )


def list_blobs(container: str | None = None, prefix: str = "") -> list[str]:
    """List blob names in a container (optional prefix filter)."""
    settings = get_settings()
    container_name = container or settings.azure_storage_container_raw
    client = get_blob_service_client()
    container_client = client.get_container_client(container_name)
    return [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]


# Allow `python -m src.utils.azure_storage smoke` style checks without leaking secrets.
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2 or sys.argv[1] != "smoke":
        print("Usage: python -m src.utils.azure_storage smoke")
        raise SystemExit(2)

    # Optional: load .azure-platform.env / .env into process env for local runs
    for env_file in (Path(".azure-platform.env"), Path(".env")):
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

    get_settings.cache_clear()
    sample = Path("data/raw/azure_smoke_marker.txt")
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text("decision-intelligence-platform azure smoke test\n", encoding="utf-8")
    url = upload_raw_dataset(str(sample), "smoke/azure_smoke_marker.txt")
    names = list_blobs(prefix="smoke/")
    print(f"uploaded: {url}")
    print(f"listed: {names}")
