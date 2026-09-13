"""Migra las capturas heredadas de oyentes de Spotify a la tabla unificada.

`metric_snapshots` es el registro único del historial de métricas. Hasta ahora
los oyentes mensuales de Spotify se guardaban aparte en
`spotify_listener_snapshots`; este script copia esas filas (una por perfil) a
la tabla nueva y respeta su `captured_at`, para que el historial previo no se
pierda. La tabla vieja se conserva por compatibilidad (nadie la lee ya).

Uso:
    .venv/bin/python scripts/backfill_metricas.py
    DATABASE_URL="<neon>" .venv/bin/python scripts/backfill_metricas.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import MetricSnapshotRepository, SpotifySnapshotRepository
from sqlalchemy import select
from db.models import SpotifyListenerSnapshot


def main() -> int:
    session = SessionLocal()
    migradas = 0
    try:
        filas = session.execute(
            select(SpotifyListenerSnapshot).order_by(
                SpotifyListenerSnapshot.captured_at.asc()
            )
        ).scalars().all()
        metricas = MetricSnapshotRepository(session)
        for fila in filas:
            if fila.oyentes_mensuales is None:
                continue
            ultimo = metricas.ultimo(fila.artist_id, "spotify", "oyentes_mensuales")
            if ultimo is None or ultimo.valor != fila.oyentes_mensuales:
                metricas.crear(
                    artist_id=fila.artist_id,
                    plataforma="spotify",
                    metrica="oyentes_mensuales",
                    valor=fila.oyentes_mensuales,
                    fuente=fila.fuente,
                    capturado_en=fila.captured_at,
                )
                migradas += 1
        session.commit()
        print(f"Snapshots de oyentes migrados: {migradas}/{len(filas)}")
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())