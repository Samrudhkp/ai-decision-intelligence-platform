# Azure resources for the Decision Intelligence Platform

Provisioned against the authenticated subscription (East US, pay-as-you-go friendly).

## Portal links (click to inspect)

| What | Link |
|------|------|
| Subscription | [Azure subscription](https://portal.azure.com/#@/resource/subscriptions/7146a0eb-4440-48e9-8d8b-55b54b45f380/overview) |
| Resource group | [rg-decision-intelligence](https://portal.azure.com/#@/resource/subscriptions/7146a0eb-4440-48e9-8d8b-55b54b45f380/resourceGroups/rg-decision-intelligence/overview) |
| Storage account | [stdipfd2177](https://portal.azure.com/#@/resource/subscriptions/7146a0eb-4440-48e9-8d8b-55b54b45f380/resourceGroups/rg-decision-intelligence/providers/Microsoft.Storage/storageAccounts/stdipfd2177/overview) |
| Containers blade | [Blob containers](https://portal.azure.com/#@/resource/subscriptions/7146a0eb-4440-48e9-8d8b-55b54b45f380/resourceGroups/rg-decision-intelligence/providers/Microsoft.Storage/storageAccounts/stdipfd2177/containersList) |
| Cost Management | [Cost analysis](https://portal.azure.com/#view/Microsoft_Azure_CostManagement/Menu/~/costanalysis) |
| All resources | [Resource list](https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/Microsoft.Resources%2Fresources) |

## Live lab resources

| Resource | Value |
|----------|--------|
| Resource group | `rg-decision-intelligence` |
| Region | `eastus` |
| Storage account | `stdipfd2177` |
| Account URL | `https://stdipfd2177.blob.core.windows.net` |
| Containers | `raw-datasets`, `processed-datasets` |
| Auth | Azure CLI / chained credential (no keys in git) |

## Blob URLs currently uploaded

### raw-datasets
- https://stdipfd2177.blob.core.windows.net/raw-datasets/customers_churn.csv
- https://stdipfd2177.blob.core.windows.net/raw-datasets/monthly_revenue.csv

### processed-datasets
- https://stdipfd2177.blob.core.windows.net/processed-datasets/churn/comparison.json
- https://stdipfd2177.blob.core.windows.net/processed-datasets/segmentation/segment_profiles.json
- https://stdipfd2177.blob.core.windows.net/processed-datasets/forecasting/baseline_forecast.json
- https://stdipfd2177.blob.core.windows.net/processed-datasets/forecasting/pytorch_forecast.json
- https://stdipfd2177.blob.core.windows.net/processed-datasets/explainability/shap_feature_importance.json
- https://stdipfd2177.blob.core.windows.net/processed-datasets/explainability/shap_summary.png
- https://stdipfd2177.blob.core.windows.net/processed-datasets/pipeline_summary.json

> Connection strings and secrets are **not** stored in this repository.  
> Local agent/runtime names are written to `.azure-platform.env` (gitignored).

## Azure Machine Learning (minimal / near-zero cost)

Created **without any compute VMs** so you are not charged for training machines.

| What | Value / link |
|------|----------------|
| Workspace | [`mlw-decision-intelligence`](https://ml.azure.com/?wsid=/subscriptions/7146a0eb-4440-48e9-8d8b-55b54b45f380/resourceGroups/rg-decision-intelligence/providers/Microsoft.MachineLearningServices/workspaces/mlw-decision-intelligence) |
| Portal resource | [Workspace blade](https://portal.azure.com/#@/resource/subscriptions/7146a0eb-4440-48e9-8d8b-55b54b45f380/resourceGroups/rg-decision-intelligence/providers/Microsoft.MachineLearningServices/workspaces/mlw-decision-intelligence/overview) |
| Registered data | `customers-churn-raw`, `monthly-revenue-raw` |
| Registered model | `churn-best-model` (from local joblib) |
| Compute clusters/instances | **None** |

### Free vs paid (plain English)

| Item | Cost impact |
|------|-------------|
| Azure ML **workspace** itself | Free |
| Reusing existing Blob Storage | Already have it (pennies for tiny demo files) |
| Key Vault + App Insights + Log Analytics (auto-created) | Free/near-free at demo scale |
| **Compute Instance / Cluster / endpoint VMs** | **Costs money** — do not create these for a free lab |
| Local training (`scripts/run_pipeline.py`) | Free (runs on this machine, not Azure VMs) |

Provision helper: `./scripts/provision_azure_ml.sh`

## Provision / teardown

```bash
# Requires: az login
chmod +x scripts/*.sh
./scripts/provision_azure_platform.sh        # creates RG + storage + containers
./scripts/teardown_azure_platform.sh         # az group delete
```

## Python helpers

```bash
set -a && source .azure-platform.env && set +a
PYTHONPATH=. python scripts/run_pipeline.py --upload-azure
PYTHONPATH=. python -m src.utils.azure_storage smoke
```

Optional: send MLflow runs to the Azure ML workspace tracker (still no compute VMs):

```bash
export AZURE_ML_TRACKING_URI="azureml://eastus.api.azureml.ms/mlflow/v1.0/subscriptions/7146a0eb-4440-48e9-8d8b-55b54b45f380/resourceGroups/rg-decision-intelligence/providers/Microsoft.MachineLearningServices/workspaces/mlw-decision-intelligence"
PYTHONPATH=. python scripts/run_pipeline.py
```
