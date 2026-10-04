#!/usr/bin/env bash
# Deploy rg-sec-logs-lab: Storage + Consumption Function + Event Grid subscription.
# Requires: az CLI logged in (az login or service principal env vars).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT_ENV="${LAB_DIR}/.env"

if [[ -f "${ROOT_ENV}" ]]; then
  # shellcheck disable=SC1090
  set -a && source "${ROOT_ENV}" && set +a
fi

LOCATION="${AZURE_LOCATION:-eastus}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-sec-logs-lab}"
FAILURE_THRESHOLD="${FAILURE_THRESHOLD:-5}"
UNIQUE_SUFFIX="$(openssl rand -hex 3)"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-stseclogs${UNIQUE_SUFFIX}}"
FUNCTION_APP="${FUNCTION_APP:-fn-seclogs-${UNIQUE_SUFFIX}}"

# Storage account names: 3-24 chars, lowercase alphanumeric only
STORAGE_ACCOUNT="$(echo "${STORAGE_ACCOUNT}" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9' | cut -c1-24)"

upload_blob() {
  local container="$1"
  local name="$2"
  local file="$3"
  if az storage blob upload \
      --account-name "${STORAGE_ACCOUNT}" \
      --auth-mode login \
      --container-name "${container}" \
      --name "${name}" \
      --file "${file}" \
      --overwrite true; then
    return 0
  fi
  local key
  key="$(az storage account keys list -g "${RESOURCE_GROUP}" -n "${STORAGE_ACCOUNT}" --query '[0].value' -o tsv)"
  az storage blob upload \
    --account-name "${STORAGE_ACCOUNT}" \
    --account-key "${key}" \
    --container-name "${container}" \
    --name "${name}" \
    --file "${file}" \
    --overwrite true
}

download_report() {
  local name="$1"
  local out="$2"
  if az storage blob download \
      --account-name "${STORAGE_ACCOUNT}" \
      --auth-mode login \
      --container-name reports \
      --name "${name}" \
      --file "${out}" \
      --overwrite true 2>/dev/null; then
    return 0
  fi
  local key
  key="$(az storage account keys list -g "${RESOURCE_GROUP}" -n "${STORAGE_ACCOUNT}" --query '[0].value' -o tsv)"
  az storage blob download \
    --account-name "${STORAGE_ACCOUNT}" \
    --account-key "${key}" \
    --container-name reports \
    --name "${name}" \
    --file "${out}" \
    --overwrite true 2>/dev/null
}

echo "==> Subscription"
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
az account show --query '{name:name,id:id}' -o table

echo "==> Deploying infra (RG=${RESOURCE_GROUP}, storage=${STORAGE_ACCOUNT}, function=${FUNCTION_APP})"
az deployment sub create \
  --location "${LOCATION}" \
  --template-file "${LAB_DIR}/infra/main.bicep" \
  --parameters \
    location="${LOCATION}" \
    resourceGroupName="${RESOURCE_GROUP}" \
    storageAccountName="${STORAGE_ACCOUNT}" \
    functionAppName="${FUNCTION_APP}" \
    failureThreshold="${FAILURE_THRESHOLD}" \
  --name "sec-logs-lab-${UNIQUE_SUFFIX}"

echo "==> Publishing Function App code"
pushd "${LAB_DIR}/function_app" >/dev/null
if [[ ! -f local.settings.json ]]; then
  cp local.settings.json.example local.settings.json
fi
zip -r /tmp/fn-seclogs.zip . -x 'local.settings.json' -x '__pycache__/*' -x '*.pyc'
popd >/dev/null

az functionapp deployment source config-zip \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${FUNCTION_APP}" \
  --src /tmp/fn-seclogs.zip

echo "==> Waiting for function host"
sleep 25
az functionapp function show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${FUNCTION_APP}" \
  --function-name AnalyzeLoginLog \
  --query '{name:name, language:language}' -o table || true

echo "==> Uploading sample log (alice flagged)"
upload_blob logs login-log-alice-flagged.json "${LAB_DIR}/sample_logs/login-log-alice-flagged.json"

echo "==> Waiting for Event Grid → Function → report"
REPORT_READY=0
for i in $(seq 1 18); do
  if download_report login-log-alice-flagged-report.json /tmp/alice-report.json; then
    echo "Report ready:"
    cat /tmp/alice-report.json
    REPORT_READY=1
    break
  fi
  echo "  attempt ${i}/18 — not ready yet..."
  sleep 10
done

if [[ "${REPORT_READY}" -ne 1 ]]; then
  echo "WARNING: Report not found yet. Check Function logs:"
  echo "  az functionapp log tail -g ${RESOURCE_GROUP} -n ${FUNCTION_APP}"
fi

cat <<EOF

Deployment complete.
  Resource group : ${RESOURCE_GROUP}
  Storage account: ${STORAGE_ACCOUNT}
  Function app   : ${FUNCTION_APP}
  Logs container : logs
  Reports        : reports

Tear down when done:
  az group delete --name ${RESOURCE_GROUP} --yes --no-wait
EOF
