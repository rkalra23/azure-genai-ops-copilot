#!/usr/bin/env bash
set -euo pipefail

RG_NAME="${RG_NAME:-rg-genai-ops-copilot}"
CONTAINERAPP_NAME="${CONTAINERAPP_NAME:-ca-knowledgerk-api}"

if az containerapp show \
  --name "$CONTAINERAPP_NAME" \
  --resource-group "$RG_NAME" \
  >/dev/null 2>&1; then

  BACKEND_FQDN=$(az containerapp show \
    --name "$CONTAINERAPP_NAME" \
    --resource-group "$RG_NAME" \
    --query properties.configuration.ingress.fqdn \
    --output tsv)

  BACKEND_URL="https://$BACKEND_FQDN"

  echo "Container App exists."
  echo "Backend URL: $BACKEND_URL"
  echo ""
  echo "Health:"
  curl -s "$BACKEND_URL/health" || true
  echo ""
else
  echo "Container App does not exist."
fi