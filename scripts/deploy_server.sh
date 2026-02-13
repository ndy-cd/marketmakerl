#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <user@host> [project_dir=/opt/marketmakerl]" >&2
  exit 1
fi

SERVER="$1"
PROJECT_DIR="${2:-/opt/marketmakerl}"

echo "[deploy] server=${SERVER} dir=${PROJECT_DIR}"
ssh "$SERVER" "mkdir -p ${PROJECT_DIR}"

echo "[deploy] syncing repository"
rsync -az --delete --exclude '.git' --exclude '.venv' --exclude 'venv' ./ "${SERVER}:${PROJECT_DIR}/"

echo "[deploy] building image and starting realtime strategy service"
ssh "$SERVER" "cd ${PROJECT_DIR} && docker compose -f docker-compose.server.yml build && docker compose -f docker-compose.server.yml up -d realtime-strategy"

echo "[deploy] done"
