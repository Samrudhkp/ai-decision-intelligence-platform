# Azure resources for the Decision Intelligence Platform

Provisioned against the authenticated subscription (East US, pay-as-you-go friendly).

## Live lab resources (current)

| Resource | Value |
|----------|--------|
| Resource group | `rg-decision-intelligence` |
| Region | `eastus` |
| Storage account | `stdipfd2177` |
| Account URL | `https://stdipfd2177.blob.core.windows.net` |
| Containers | `raw-datasets`, `processed-datasets` |
| Auth | Azure CLI / `DefaultAzureCredential` (no keys in git) |

> Connection strings and secrets are **not** stored in this repository.  
> Local agent/runtime names are written to `.azure-platform.env` (gitignored).

## What was intentionally deferred

- **Azure Machine Learning workspace** — create later when training/deploy starts (higher cost).
- Model endpoints / App Service — after FastAPI prediction APIs exist.

## Provision / teardown

```bash
# Requires: az login
chmod +x scripts/*.sh
./scripts/provision_azure_platform.sh        # creates RG + storage + containers
./scripts/teardown_azure_platform.sh         # az group delete
```

## Python helpers

```bash
# Load resource names, then smoke-test upload to raw-datasets
set -a && source .azure-platform.env && set +a
python -m src.utils.azure_storage smoke
```

APIs:

- `upload_raw_dataset` / `download_raw_dataset`
- `upload_processed_dataset`
- `list_blobs`
