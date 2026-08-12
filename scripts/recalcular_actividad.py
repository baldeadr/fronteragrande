"""Recomputa `estado_activo` de todos los artistas según la regla documentada.

La regla (`scraper/core.py`, `REGLA_ACTIVIDAD`) usa la señal más reciente
(lanzamiento, evento o feed) como referencia de actividad: un elemento
reciente del feed (≤ 6 meses) también cuenta. Este script actualiza la BD y
el CSV semilla para mantener una sola verdad.

Uso:
    .venv/bin/python scripts/recalcular_actividad.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from db.database import SessionLocal
from lib.repository import ArtistRepository
from lib.servicios import ultimo_feed_de_artista
from scraper.core import estado_activo_recomputado

CSV_PATH = "data/escena_local.csv"


def recalcular() -> list:
    """Recomputa `estado_activo` en BD y CSV. Devuelve la lista de cambios."""
    session = SessionLocal()
    cambios = []
    nuevos = {}
    try:
        for artista in ArtistRepository(session).todos():
            ultimo_feed = ultimo_feed_de_artista(session, artista)
            nuevo = estado_activo_recomputado(artista, ultimo_feed=ultimo_feed)
            nuevos[artista.slug] = nuevo
            if nuevo != artista.estado_activo:
                cambios.append(
                    (artista.nombre, artista.estado_activo, nuevo, str(ultimo_feed or ""))
                )
                artista.estado_activo = nuevo
        session.commit()
    finally:
        session.close()

    if cambios:
        df = pd.read_csv(CSV_PATH, dtype=str)
        df["id"] = df["id"].astype(str)
        df.loc[df["id"].isin(nuevos), "estado_activo"] = df.loc[
            df["id"].isin(nuevos), "id"
        ].map(nuevos)
        df.to_csv(CSV_PATH, index=False, quoting=csv.QUOTE_ALL, lineterminator="\n")

    return cambios


def main():
    cambios = recalcular()
    print(f"Cambios de actividad: {len(cambios)}")
    for nombre, antes, despues, feed in cambios:
        print(f"  {nombre}: {antes} → {despues} (último feed: {feed or '—'})")


if __name__ == "__main__":
    main()