#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v docker >/dev/null 2>&1; then
  docker compose -f docker-compose.yml down --remove-orphans || true
  docker compose -f docker-compose.cuda.yml down --remove-orphans || true
  docker compose -f docker-compose.monitoring.yml down --remove-orphans || true
fi

echo "Stopped default (ROCm), CUDA, and monitoring stacks (if running)."
