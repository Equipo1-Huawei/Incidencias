#!/usr/bin/env bash
# block_atlas.sh - Bloqueo de salida al puerto 27017 dentro del contenedor de aplicación
set -euo pipefail

CONTAINER_NAME="triage-nextjs"
LOG_FILE="./logs/chaos_events.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "{\"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\", \"event\": \"CHAOS_ATLAS_BLOCKED\", \"target\": \"$CONTAINER_NAME\"}" >> "$LOG_FILE"

# Inserta regla iptables interna en el namespace de red del contenedor
docker exec --user root "$CONTAINER_NAME" iptables -I OUTPUT -p tcp --dport 27017 -j REJECT --reject-with tcp-reset
