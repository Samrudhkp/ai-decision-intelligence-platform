#!/usr/bin/env bash
# Delete the entire lab in one shot (resource group).
set -euo pipefail
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-sec-logs-lab}"
echo "Deleting resource group ${RESOURCE_GROUP}..."
az group delete --name "${RESOURCE_GROUP}" --yes --no-wait
echo "Delete accepted (async)."
