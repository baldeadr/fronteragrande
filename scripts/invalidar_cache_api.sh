#!/usr/bin/env bash
# Invalida la caché pública de la API (artistas/feed/stats/ranking) tras los
# syncs de GitHub Actions (que escriben directo en la BD, fuera del proceso
# de la API). Si falta ADMIN_PASSWORD se omite en silencio.
#
# Variables de entorno opcionales:
#   API_PUBLIC_URL   URL base de la API (por defecto la de Render).
#   ADMIN_PASSWORD   token de administrador (X-Admin-Token).
set -euo pipefail

API_URL="${API_PUBLIC_URL:-https://fronteragrande-api.onrender.com}"

if [ -z "${ADMIN_PASSWORD:-}" ]; then
  echo "[cache] Sin ADMIN_PASSWORD: se omite la invalidación de la caché."
  exit 0
fi

echo "[cache] Invalidando caché pública de ${API_URL} …"
curl -s -o /dev/null -w "[cache] HTTP %{http_code}\n" \
  -X POST "${API_URL}/api/admin/cache-invalidate" \
  -H "X-Admin-Token: ${ADMIN_PASSWORD}"