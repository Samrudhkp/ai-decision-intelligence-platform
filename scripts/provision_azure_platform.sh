#!/usr/bin/env bash
# Provision low-cost Azure resources for the Decision Intelligence Platform.
# Auth: az login (or service principal env vars). No secrets written to git.
set -euo pipefail

LOCATION="${AZURE_LOCATION:-eastus}"
RG="${AZURE_RESOURCE_GROUP:-rg-decision-intelligence}"
SUFFIX="$(openssl rand -hex 3)"
STORAGE="${AZURE_STORAGE_ACCOUNT_NAME:-stdip${SUFFIX}}"
STORAGE="$(echo "${STORAGE}" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9' | cut -c1-24)"

if [[ -n "${AZURE_CLIENT_ID:-}" && -n "${AZURE_CLIENT_SECRET:-}" && -n "${AZURE_TENANT_ID:-}" ]]; then
  az login --service-principal \
    -u "${AZURE_CLIENT_ID}" \
    -p "${AZURE_CLIENT_SECRET}" \
    --tenant "${AZURE_TENANT_ID}" \
    --output none
fi
if [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]]; then
  az account set --subscription "${AZURE_SUBSCRIPTION_ID}"
fi

echo "==> Creating resource group ${RG} in ${LOCATION}"
az group create --name "${RG}" --location "${LOCATION}" -o table

echo "==> Creating storage account ${STORAGE}"
az storage account create \
  --name "${STORAGE}" \
  --resource-group "${RG}" \
  --location "${LOCATION}" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --allow-blob-public-access false \
  --min-tls-version TLS1_2 \
  --https-only true \
  -o table

echo "==> Creating containers"
# Container create can use account key while RBAC propagates
az storage container create --name raw-datasets --account-name "${STORAGE}" --auth-mode key -o table
az storage container create --name processed-datasets --account-name "${STORAGE}" --auth-mode key -o table

echo "==> Granting Storage Blob Data Contributor to signed-in user (data-plane access)"
USER_OID="$(az ad signed-in-user show --query id -o tsv 2>/dev/null || true)"
if [[ -n "${USER_OID}" ]]; then
  az role assignment create \
    --assignee-object-id "${USER_OID}" \
    --assignee-principal-type User \
    --role "Storage Blob Data Contributor" \
    --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RG}/providers/Microsoft.Storage/storageAccounts/${STORAGE}" \
    -o none || true
fi

OUT_FILE="${1:-.azure-platform.env}"
cat > "${OUT_FILE}" <<EOF
AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)
AZURE_LOCATION=${LOCATION}
AZURE_RESOURCE_GROUP=${RG}
AZURE_STORAGE_ACCOUNT_NAME=${STORAGE}
AZURE_STORAGE_ACCOUNT_URL=https://${STORAGE}.blob.core.windows.net
AZURE_STORAGE_CONTAINER_RAW=raw-datasets
AZURE_STORAGE_CONTAINER_PROCESSED=processed-datasets
EOF

echo "==> Wrote non-secret resource names to ${OUT_FILE} (gitignored)"
echo "Done. Copy values into your local .env as needed."
