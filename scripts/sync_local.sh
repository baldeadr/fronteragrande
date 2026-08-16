#!/usr/bin/env bash
# Sincroniza la BD local (descartable) desde la BD de producción (Neon).
#
# La BD de producción es la única fuente de verdad. Este script:
#   1. Exporta el estado documental de Neon a data/*.csv (scripts/exportar_csv.py).
#   2. Borra la BD local descartable.
#   3. Re-siembra la BD local desde el CSV exportado (seed insert-if-missing).
#
# Uso:
#   DATABASE_URL="<conexión de Neon>" ./scripts/sync_local.sh
#
# Requiere la connection string de Neon en la variable DATABASE_URL (no debe
# apuntar a SQLite local). No se versiona ninguna credencial.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -z "${DATABASE_URL:-}" || "$DATABASE_URL" == sqlite* ]]; then
    echo "ERROR: define DATABASE_URL con la conexión de Neon (PostgreSQL)." >&2
    echo "  Ej: DATABASE_URL=\"postgresql://...\" ./scripts/sync_local.sh" >&2
    exit 1
fi

echo "1) Exportando el estado de producción a data/*.csv …"
DATABASE_URL="$DATABASE_URL" .venv/bin/python scripts/exportar_csv.py

echo "2) Eliminando la BD local descartable …"
rm -f instance/local_scene.db

echo "3) Re-sembrando la BD local desde el CSV exportado …"
.venv/bin/python scripts/seed_db.py

echo "Listo: la BD local es un snapshot de producción."