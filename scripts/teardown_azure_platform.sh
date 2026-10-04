#!/usr/bin/env bash
# Delete the Decision Intelligence Platform resource group (async).
set -euo pipefail
RG="${AZURE_RESOURCE_GROUP:-rg-decision-intelligence}"
echo "Deleting resource group ${RG}..."
az group delete --name "${RG}" --yes --no-wait
echo "Delete accepted (async)."
