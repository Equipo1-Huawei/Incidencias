#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="triage-nextjs"
LOG_FILE="./logs/chaos_events.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_event() {
    local msg="$1"
    echo "{\"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\", \"event\": \"$msg\", \"target\": \"$CONTAINER_NAME\"}" | tee -a "$LOG_FILE"
}

log_event "CHAOS_MEMORY_STRESS_START"

# Ejecuta stress-ng asignando 600M para superar el límite de 512M del contenedor
docker exec "$CONTAINER_NAME" sh -c "command -v stress-ng >/dev/null 2>&1 || (apk add --no-cache stress-ng || apt-get update && apt-get install -y stress-ng)"
docker exec -d "$CONTAINER_NAME" stress-ng --vm 1 --vm-bytes 600M --timeout 30s || true

log_event "CHAOS_MEMORY_STRESS_DISPATCHED"
