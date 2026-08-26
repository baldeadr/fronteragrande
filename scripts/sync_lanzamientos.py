"""Orquestador de sincronización de lanzamientos.

Ejecuta Bandcamp, SoundCloud y Spotify (en batches paralelos via GitHub Actions).

Uso:
    python scripts/sync_lanzamientos.py              # normal (incremental)
    python scripts/sync_lanzamientos.py --solo-nuevos  # catch-up inicial
    python scripts/sync_lanzamientos.py --force-all    # re-sync total
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository
from db.models import FeedItem
from scripts.recalcular_actividad import recalcular


def get_artistas_pendientes(
    solo_nuevos: bool = False, force_all: bool = False, max_artists: int = 20
):
    """Obtiene artistas que necesitan sincronización.

    Prioridad:
    1. Artistas sin items de Spotify (nunca sincronizados)
    2. Artistas con timestamp más antiguo (> 7 días)
    """
    from db.models import FeedItem
    from datetime import datetime, timedelta

    session = SessionLocal()
    try:
        repo = ArtistRepository(session)
        # Solo artistas con al menos un link de plataforma soportada
        artistas = [
            a
            for a in repo.todos()
            if any(
                l.plataforma in ("spotify", "bandcamp", "soundcloud", "beatport", "mixcloud")
                and not l.es_busqueda
                for l in a.links
            )
        ]

        if solo_nuevos or not force_all:
            # Filtrar: sin items de Spotify O timestamp NULL O > 7 días
            siete_dias = datetime.utcnow() - timedelta(days=7)
            artistas = [
                a for a in artistas
                if (
                    solo_nuevos
                    and a.id not in session.query(FeedItem.artist_id).filter_by(fuente="spotify")
                )
                or a.ultimo_sync_lanzamientos is None
                or a.ultimo_sync_lanzamientos < siete_dias
            ]
            # Ordenar: NULL primero, luego más antiguos
            artistas.sort(
                key=lambda a: (
                    a.ultimo_sync_lanzamientos is not None,
                    a.ultimo_sync_lanzamientos or "",
                )
            )

        if not force_all:
            artistas = artistas[:max_artists]

        return artistas
    finally:
        session.close()


def main(solo_nuevos: bool = False, force_all: bool = False) -> int:
    """Ejecuta sincronización completa: Bandcamp → SoundCloud → Spotify (delegado a batches)."""
    from scripts.sync_bandcamp import main as sync_bandcamp
    from scripts.sync_soundcloud import main as sync_soundcloud

    print("=== Sincronizando Bandcamp ===")
    sync_bandcamp(artistas=None, solo_nuevos=solo_nuevos)

    print("\n=== Sincronizando SoundCloud ===")
    sync_soundcloud(artistas=None, solo_nuevos=solo_nuevos)

    print("\n=== Spotify delegado a GitHub Actions (batches paralelos) ===")
    print("  Ejecuta: gh workflow run sync-spotify-batch -f batch=0 ...")

    # Recalcular actividad al final
    print("\n=== Recalculando actividad ===")
    cambios = recalcular()
    print(f"Cambios de actividad: {len(cambios)}")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo-nuevos", action="store_true", help="Solo artistas sin sync previo")
    parser.add_argument("--force-all", action="store_true", help="Re-sincronizar todos (ignora timestamp)")
    args = parser.parse_args()

    main(solo_nuevos=args.solo_nuevos, force_all=args.force_all)