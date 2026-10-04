#!/usr/bin/env bash
# Create a minimal Azure ML workspace with NO compute VMs (near-zero cost).
# Requires: az login + Azure CLI ML extension (az extension add -n ml)
set -euo pipefail

if [[ -f .azure-platform.env ]]; then
  # shellcheck disable=SC1091
  set -a && source .azure-platform.env && set +a
fi

RG="${AZURE_RESOURCE_GROUP:-rg-decision-intelligence}"
WS="${AZURE_ML_WORKSPACE_NAME:-mlw-decision-intelligence}"
LOC="${AZURE_ML_WORKSPACE_REGION:-eastus}"
STORAGE="${AZURE_STORAGE_ACCOUNT_NAME:?Set AZURE_STORAGE_ACCOUNT_NAME}"
SUB="${AZURE_SUBSCRIPTION_ID:-$(az account show --query id -o tsv)}"
STORAGE_ID="/subscriptions/${SUB}/resourceGroups/${RG}/providers/Microsoft.Storage/storageAccounts/${STORAGE}"

echo "==> Creating workspace ${WS} (reusing storage ${STORAGE}, no compute)"
az ml workspace create \
  --name "${WS}" \
  --resource-group "${RG}" \
  --location "${LOC}" \
  --storage-account "${STORAGE_ID}" \
  --public-network-access Enabled \
  -o table

echo "==> Registering data assets"
az ml data create -g "${RG}" -w "${WS}" -f infra/azureml/data_churn.yml -o table
az ml data create -g "${RG}" -w "${WS}" -f infra/azureml/data_revenue.yml -o table

if [[ -f models/churn/best_model.joblib ]]; then
  echo "==> Registering local churn model artifact"
  az ml model create -g "${RG}" -w "${WS}" -f infra/azureml/model_churn.yml -o table || true
else
  echo "==> Skipping model register (train first: PYTHONPATH=. python scripts/run_pipeline.py)"
fi

echo "Done. Do NOT create Compute Instance / Compute Cluster unless you accept VM charges."
