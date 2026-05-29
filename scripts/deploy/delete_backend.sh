#!/usr/bin/env bash
set -euo pipefail

RG_NAME="${RG_NAME:-rg-genai-ops-copilot}"
CONTAINERAPP_NAME="${CONTAINERAPP_NAME:-ca-knowledgerk-api}"

echo "This will delete the backend Container App."
echo "Container App: $CONTAINERAPP_NAME"
echo "Resource Group: $RG_NAME"
echo ""
read -p "Continue? [y/N] " CONFIRM

if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Cancelled."
  exit 0
fi

if az containerapp show \
  --name "$CONTAINERAPP_NAME" \
  --resource-group "$RG_NAME" \
  >/dev/null 2>&1; then

  az containerapp delete \
    --name "$CONTAINERAPP_NAME" \
    --resource-group "$RG_NAME" \
    --yes

  echo "Deleted backend Container App: $CONTAINERAPP_NAME"
else
  echo "Container App does not exist: $CONTAINERAPP_NAME"
fi