#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8101}"
API_KEY="${API_KEY:-${OPENAI_API_KEY:-}}"
AUTH_HEADER=()
if [[ -n "$API_KEY" ]]; then
  AUTH_HEADER=(-H "Authorization: Bearer ${API_KEY}")
fi

echo "Checking gateway health at ${BASE_URL}/health"
if curl -fsS "${AUTH_HEADER[@]}" "${BASE_URL}/health" >/tmp/cognicore_health.json; then
  echo "Gateway /health: OK"
  cat /tmp/cognicore_health.json
  echo
else
  echo "Gateway /health: FAILED"
  exit 1
fi

echo "Checking models endpoint at ${BASE_URL}/v1/models"
if curl -fsS "${AUTH_HEADER[@]}" "${BASE_URL}/v1/models" >/tmp/cognicore_models.json; then
  echo "/v1/models: OK"
  cat /tmp/cognicore_models.json
  echo
else
  echo "/v1/models: FAILED"
  exit 1
fi

echo "Healthcheck completed successfully."
