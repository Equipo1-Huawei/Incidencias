#!/usr/bin/env bash
# block_atlas.sh - Bloqueo de salida al puerto de base de datos dentro del contenedor
# Nota: Supabase es hosted (HTTPS/443), este script simula caida de red general
set -euo pipefail

CONTAINER_NAME="triage-nextjs"
LOG_FILE="./logs/chaos_events.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "{\"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\", \"event\": \"CHAOS_DB_BLOCKED\", \"target\": \"$CONTAINER_NAME\"}" >> "$LOG_FILE"

# Bloquea trafego HTTPS saliente (Supabase API usa HTTPS/443)
docker exec --user root "$CONTAINER_NAME" iptables -I OUTPUT -p tcp --dport 443 -j REJECT --reject-with tcp-reset
