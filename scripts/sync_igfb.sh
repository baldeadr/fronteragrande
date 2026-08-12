#!/usr/bin/env bash
# Sincroniza posts de Facebook/Instagram de artistas conectados a Meta.
# Diseñado para ejecutarse desde cron; añade un log por fecha.
#
# Crontab sugerido (cada 6 horas):
#   0 */6 * * * /ruta/a/escena_local/scripts/sync_igfb.sh >> /tmp/sync_igfb.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sincronizando Meta …"
.venv/bin/python scripts/sync_feed_igfb.py
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync terminado."
