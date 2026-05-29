#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Azure GenAI Ops Copilot
# Deploy/recreate backend Container App
# -----------------------------

RG_NAME="${RG_NAME:-rg-genai-ops-copilot}"
LOCATION="${LOCATION:-canadacentral}"
ACR_NAME="${ACR_NAME:-acrgenaiopscopilotrkalra}"
IMAGE_NAME="${IMAGE_NAME:-azure-genai-ops-copilot}"
IMAGE_TAG="${IMAGE_TAG:-v3.6-deploy-test}"
CONTAINERAPP_ENV_NAME="${CONTAINERAPP_ENV_NAME:-cae-genai-ops-copilot}"
CONTAINERAPP_NAME="${CONTAINERAPP_NAME:-ca-knowledgerk-api}"

echo "==> Loading .env"

if [ ! -f ".env" ]; then
  echo "ERROR: .env file not found. Run this script from the repo root."
  exit 1
fi

set -a
source .env
set +a

echo "==> Checking Azure login"
az account show >/dev/null

echo "==> Getting ACR login server"
ACR_LOGIN_SERVER=$(az acr show \
  --name "$ACR_NAME" \
  --resource-group "$RG_NAME" \
  --query loginServer \
  --output tsv)

echo "ACR login server: $ACR_LOGIN_SERVER"

echo "==> Enabling ACR admin user"
az acr update \
  --name "$ACR_NAME" \
  --admin-enabled true \
  >/dev/null

echo "==> Getting ACR credentials"
ACR_USERNAME=$(az acr credential show \
  --name "$ACR_NAME" \
  --query 'username' \
  --output tsv)

ACR_PASSWORD=$(az acr credential show \
  --name "$ACR_NAME" \
  --query 'passwords[0].value' \
  --output tsv)

echo "==> Confirming Container Apps environment exists"
az containerapp env show \
  --name "$CONTAINERAPP_ENV_NAME" \
  --resource-group "$RG_NAME" \
  >/dev/null

echo "==> Confirming image tag exists in ACR"
az acr repository show-tags \
  --name "$ACR_NAME" \
  --repository "$IMAGE_NAME" \
  --output table

echo "==> Deploying image:"
echo "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"

if az containerapp show \
  --name "$CONTAINERAPP_NAME" \
  --resource-group "$RG_NAME" \
  >/dev/null 2>&1; then

  echo "==> Container App exists. Updating app."

  az containerapp update \
    --name "$CONTAINERAPP_NAME" \
    --resource-group "$RG_NAME" \
    --image "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG" \
    --set-env-vars \
      APP_API_KEY="$APP_API_KEY" \
      ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-http://127.0.0.1:5500,http://localhost:5500}" \
      AZURE_SEARCH_ENDPOINT="$AZURE_SEARCH_ENDPOINT" \
      AZURE_SEARCH_API_KEY="$AZURE_SEARCH_API_KEY" \
      AZURE_SEARCH_INDEX_NAME="$AZURE_SEARCH_INDEX_NAME" \
      AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
      AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
      AZURE_OPENAI_CHAT_DEPLOYMENT="$AZURE_OPENAI_CHAT_DEPLOYMENT" \
      AZURE_OPENAI_EMBEDDING_DEPLOYMENT="$AZURE_OPENAI_EMBEDDING_DEPLOYMENT" \
      AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
      DEFAULT_RERANK_MODE="${DEFAULT_RERANK_MODE:-azure_semantic}" \
      FINAL_CONTEXT_TOP_N="${FINAL_CONTEXT_TOP_N:-3}" \
      AZURE_SEARCH_SEMANTIC_CONFIG_NAME="${AZURE_SEARCH_SEMANTIC_CONFIG_NAME:-default}"

else

  echo "==> Container App does not exist. Creating app."

  az containerapp create \
    --name "$CONTAINERAPP_NAME" \
    --resource-group "$RG_NAME" \
    --environment "$CONTAINERAPP_ENV_NAME" \
    --image "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG" \
    --target-port 8000 \
    --ingress external \
    --registry-server "$ACR_LOGIN_SERVER" \
    --registry-username "$ACR_USERNAME" \
    --registry-password "$ACR_PASSWORD" \
    --env-vars \
      APP_API_KEY="$APP_API_KEY" \
      ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-http://127.0.0.1:5500,http://localhost:5500}" \
      AZURE_SEARCH_ENDPOINT="$AZURE_SEARCH_ENDPOINT" \
      AZURE_SEARCH_API_KEY="$AZURE_SEARCH_API_KEY" \
      AZURE_SEARCH_INDEX_NAME="$AZURE_SEARCH_INDEX_NAME" \
      AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
      AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
      AZURE_OPENAI_CHAT_DEPLOYMENT="$AZURE_OPENAI_CHAT_DEPLOYMENT" \
      AZURE_OPENAI_EMBEDDING_DEPLOYMENT="$AZURE_OPENAI_EMBEDDING_DEPLOYMENT" \
      AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
      DEFAULT_RERANK_MODE="${DEFAULT_RERANK_MODE:-azure_semantic}" \
      FINAL_CONTEXT_TOP_N="${FINAL_CONTEXT_TOP_N:-3}" \
      AZURE_SEARCH_SEMANTIC_CONFIG_NAME="${AZURE_SEARCH_SEMANTIC_CONFIG_NAME:-default}"
fi

echo "==> Getting backend URL"
BACKEND_FQDN=$(az containerapp show \
  --name "$CONTAINERAPP_NAME" \
  --resource-group "$RG_NAME" \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

BACKEND_URL="https://$BACKEND_FQDN"

echo ""
echo "Backend deployed:"
echo "$BACKEND_URL"
echo ""
echo "Health check:"
curl -s "$BACKEND_URL/health" || true
echo ""