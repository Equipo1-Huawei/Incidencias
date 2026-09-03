#!/usr/bin/env bash
# unblock_atlas.sh - Reversion de la regla de bloqueo de base de datos
set -euo pipefail

CONTAINER_NAME="triage-nextjs"
LOG_FILE="./logs/chaos_events.log"
mkdir -p "$(dirname "$LOG_FILE")"

docker exec --user root "$CONTAINER_NAME" iptables -D OUTPUT -p tcp --dport 443 -j REJECT --reject-with tcp-reset || true

echo "{\"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\", \"event\": \"CHAOS_DB_UNBLOCKED\", \"target\": \"$CONTAINER_NAME\"}" >> "$LOG_FILE"
