#!/usr/bin/env bash
# Sincroniza videos y seguidores de TikTok de artistas conectados.
# Diseñado para ejecutarse desde cron; añade un log por fecha.
#
# Crontab sugerido (cada 6 horas):
#   0 */6 * * * /ruta/a/escena_local/scripts/sync_tiktok.sh >> /tmp/sync_tiktok.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sincronizando TikTok …"
.venv/bin/python scripts/sync_feed_tiktok.py
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync terminado."