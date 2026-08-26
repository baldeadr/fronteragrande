"""Sincroniza lanzamientos de Spotify para un batch de artistas.

Uso:
    python scripts/sync_spotify_batch.py --batch 0 --total-batches 4
    python scripts/sync_spotify_batch.py --solo-nuevos --batch 1 --total-batches 4
"""

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository, FeedRepository
from db.models import FeedItem
from scraper.adapters.spotify import artist_id_from_url, get_artist_releases

try:
    MAX_ITEMS = max(1, int(os.getenv("SYNC_LANZAMIENTOS_LIMIT", "10")))
except ValueError:
    MAX_ITEMS = 10


def get_batch_artistas(batch: int, total_batches: int, solo_nuevos: bool = False):
    """Obtiene artistas del batch correspondiente."""
    session = SessionLocal()
    try:
        repo = ArtistRepository(session)
        todos = [
            a
            for a in repo.todos()
            if any(l.plataforma == "spotify" and not l.es_busqueda for l in a.links)
        ]

        # Ordenar: NULL timestamp primero (nunca sincronizados), luego más antiguos
        todos.sort(
            key=lambda a: (
                a.ultimo_sync_lanzamientos is not None,
                a.ultimo_sync_lanzamientos or "",
            )
        )

        if solo_nuevos:
            # Solo artistas sin items de Spotify
            artistas_con_sp = session.query(FeedItem.artist_id).filter_by(
                fuente="spotify"
            ).subquery()
            todos = [a for a in todos if a.id not in artistas_con_sp]

        # Distribuir en batches
        batch_size = (len(todos) + total_batches - 1) // total_batches
        inicio = batch * batch_size
        fin = min(inicio + batch_size, len(todos))

        return todos[inicio:fin]
    finally:
        session.close()


def main(batch: int, total_batches: int, solo_nuevos: bool = False) -> int:
    """Procesa un batch de artistas para Spotify."""
    from db.models import FeedItem

    session = SessionLocal()
    total = 0
    try:
        feed = FeedRepository(session)
        artistas = get_batch_artistas(batch, total_batches, solo_nuevos)

        if not artistas:
            print(f"Batch {batch}/{total_batches}: sin artistas que procesar")
            return 0

        print(f"Batch {batch}/{total_batches}: {len(artistas)} artistas")

        for artista in artistas:
            enlaces = [
                l for l in artista.links if l.plataforma == "spotify" and not l.es_busqueda
            ]
            for enlace in enlaces:
                nuevos = 0
                try:
                    artist_id = artist_id_from_url(enlace.url)
                    if not artist_id:
                        continue

                    for intento in range(3):
                        try:
                            items = get_artist_releases(artist_id, MAX_ITEMS)
                            break
                        except Exception as e:
                            if hasattr(e, "response") and e.response.status_code == 429:
                                espera = int(e.response.headers.get("Retry-After", 2 + intento * 5))
                                print(f"  {artista.nombre}: 429 - esperando {espera}s (intento {intento+1}/3)")
                                time.sleep(espera)
                                continue
                            raise

                    for item in items:
                        if feed.crear_si_nuevo(
                            artista.id, "spotify", "lanzamiento", item
                        ):
                            nuevos += 1
                    session.commit()

                    # Actualizar timestamp de sync
                    from datetime import datetime
                    artista.ultimo_sync_lanzamientos = datetime.utcnow()
                    session.commit()

                except Exception as exc:
                    session.rollback()
                    print(f"{artista.nombre} (spotify): {exc}")
                total += nuevos
                if nuevos:
                    print(f"  {artista.nombre}: {nuevos} nuevos en spotify")
                time.sleep(0.5)

        print(f"Spotify batch {batch} total items nuevos: {total}")
        return total
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, required=True, help="Número de batch (0-indexado)")
    parser.add_argument("--total-batches", type=int, default=4, help="Total de batches")
    parser.add_argument("--solo-nuevos", action="store_true", help="Solo artistas sin items previos")
    args = parser.parse_args()

    main(args.batch, args.total_batches, args.solo_nuevos)