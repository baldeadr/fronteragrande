"""Regenera los CSV semilla desde la base de datos.

La BD es la fuente de verdad operativa; este script exporta su estado
documental (artistas + eventos) a `data/escena_local.csv` y `data/eventos.csv`
con el mismo esquema que entiende el seed (round-trip limpio).

Uso:
    .venv/bin/python scripts/exportar_csv.py
    DATABASE_URL="<neon>" .venv/bin/python scripts/exportar_csv.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from db.export import exportar


def main() -> int:
    session = SessionLocal()
    try:
        resultado = exportar(session)
    finally:
        session.close()
    print(
        f"Export completado: {resultado['artistas']} artistas, "
        f"{resultado['eventos']} eventos, "
        f"{resultado['meses_metricas']} series mensuales de métricas."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())