#!/usr/bin/env bash
set -euo pipefail

COLLECTION_PATH="${COLLECTION_PATH:-tests/postman/collection.json}"
AUTH_BASE_URL="${AUTH_BASE_URL:-http://localhost:8001}"
ACCOUNT_BASE_URL="${ACCOUNT_BASE_URL:-http://localhost:8002}"
TRANSACTION_BASE_URL="${TRANSACTION_BASE_URL:-http://localhost:8003}"
CLIENT_ID="${CLIENT_ID:-web-portal}"
CLIENT_SECRET="${CLIENT_SECRET:-change-me}"
USERNAME="${USERNAME:-analyst@example.com}"
PASSWORD="${PASSWORD:-P@ssw0rd!}"

npx --yes newman run "$COLLECTION_PATH" \
  --env-var authBaseUrl="$AUTH_BASE_URL" \
  --env-var accountBaseUrl="$ACCOUNT_BASE_URL" \
  --env-var transactionBaseUrl="$TRANSACTION_BASE_URL" \
  --env-var clientId="$CLIENT_ID" \
  --env-var clientSecret="$CLIENT_SECRET" \
  --env-var username="$USERNAME" \
  --env-var password="$PASSWORD" \
  --bail
