"""Recomputa `estado_activo` de todos los artistas según la regla documentada.

La regla (`scraper/core.py`, `REGLA_ACTIVIDAD`) usa la señal más reciente
(lanzamiento, evento o feed) como referencia de actividad: un elemento
reciente del feed (≤ 6 meses) o un evento del cartel también cuentan. La
lógica vive en `lib/servicios.recalcular_actividad` (la comparten los
scripts y el panel de admin). Este script actualiza solo la BD (fuente de
verdad); el CSV semilla se regenera aparte con `scripts/exportar_csv.py`
cuando se quiera un snapshot.

Uso:
    .venv/bin/python scripts/recalcular_actividad.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.servicios import recalcular_actividad as _recalcular


def recalcular() -> list:
    """Recomputa `estado_activo` en la BD con su propia sesión.

    Devuelve la lista de cambios `(nombre, antes, después)`. Lo usan los
    scripts de sincronización al final de su corrida.
    """
    session = SessionLocal()
    try:
        cambios = _recalcular(session)
        session.commit()
        return cambios
    finally:
        session.close()


def main():
    cambios = recalcular()
    print(f"Cambios de actividad: {len(cambios)}")
    for nombre, antes, despues in cambios:
        print(f"  {nombre}: {antes} → {despues}")


if __name__ == "__main__":
    main()