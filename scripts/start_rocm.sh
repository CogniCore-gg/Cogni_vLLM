#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created .env from .env.example. Update HF_TOKEN before production use."
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed or not in PATH."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: docker compose plugin is required."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: docker daemon is not reachable."
  exit 1
fi

if ! rg -N "^HF_TOKEN=.+$" .env >/dev/null 2>&1; then
  echo "WARNING: HF_TOKEN appears empty in .env. Gated models will fail to download."
fi

if [[ ! -e /dev/kfd || ! -e /dev/dri ]]; then
  echo "ERROR: ROCm devices not visible (/dev/kfd or /dev/dri missing)."
  exit 1
fi

echo "Starting stack (ROCm — default docker-compose.yml)..."
docker compose --env-file .env up -d --build
echo "Stack started. Run ./scripts/healthcheck.sh to verify readiness."
