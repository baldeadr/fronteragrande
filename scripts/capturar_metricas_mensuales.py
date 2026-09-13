"""Ancla mensual del historial de métricas (red de seguridad).

Registra un snapshot del estado actual de TODOS los artistas, forzando la
fila aunque el valor no haya cambiado respecto al sync previo. Así cada mes
queda garantizado un punto en `metric_snapshots` para plataformas cuyo sync
es manual u ocasional (oyentes de Spotify, Mixcloud, semillas). Es la última
red sobre la captura por sync (que sí usa dedupe consecutivo).

Uso:
    .venv/bin/python scripts/capturar_metricas_mensuales.py
    DATABASE_URL="<neon>" .venv/bin/python scripts/capturar_metricas_mensuales.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository
from lib.servicios import medidas_actuales, registrar_snapshots


def main() -> int:
    session = SessionLocal()
    total = 0
    con_datos = 0
    try:
        for artista in ArtistRepository(session).todos():
            medidas = medidas_actuales(artista)
            creadas = registrar_snapshots(
                session, artista.id, medidas, forzar=True
            )
            total += creadas
            con_datos += 1 if medidas else 0
        session.commit()
        print(
            f"Snapshots forzados: {total} filas · "
            f"artistas con métricas: {con_datos}"
        )
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())