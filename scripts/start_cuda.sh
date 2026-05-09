#!/usr/bin/env bash
# Optional NVIDIA CUDA stack. Primary deployment is ROCm (docker-compose.yml / ./scripts/start.sh).
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

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "ERROR: nvidia-smi not found. NVIDIA drivers may be missing."
  exit 1
fi

if ! nvidia-smi >/dev/null 2>&1; then
  echo "ERROR: NVIDIA GPUs not visible to host."
  exit 1
fi

echo "Starting CUDA stack..."
docker compose --env-file .env -f docker-compose.cuda.yml up -d --build
echo "CUDA stack started. Run ./scripts/healthcheck.sh to verify readiness."
