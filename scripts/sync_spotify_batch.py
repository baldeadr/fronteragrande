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
    print(f"DEBUG: get_batch_artistas batch={batch} total_batches={total_batches} solo_nuevos={solo_nuevos}", flush=True)
    session = SessionLocal()
    try:
        print("DEBUG: Creating ArtistRepository", flush=True)
        repo = ArtistRepository(session)
        print("DEBUG: Getting all artists", flush=True)
        todos_artistas = repo.todos()
        print(f"DEBUG: Total artistas en BD: {len(todos_artistas)}", flush=True)
        
        todos = [
            a
            for a in todos_artistas
            if any(l.plataforma == "spotify" and not l.es_busqueda for l in a.links)
        ]
        print(f"DEBUG: Artistas con link Spotify: {len(todos)}", flush=True)

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
            print(f"DEBUG: Artistas sin items Spotify: {len(todos)}", flush=True)

        # Si total_batches=1, procesar todos
        if total_batches == 1:
            result = todos
            print(f"DEBUG: Single batch: {len(result)} artistas", flush=True)
            return result

        # Distribuir en batches
        batch_size = (len(todos) + total_batches - 1) // total_batches
        inicio = batch * batch_size
        fin = min(inicio + batch_size, len(todos))

        result = todos[inicio:fin]
        print(f"DEBUG: Batch {batch}: {len(result)} artistas (inicio={inicio}, fin={fin})", flush=True)
        # Limitar a 10 artistas por corrida para evitar rate limit global
        if total_batches == 1 and len(result) > 10:
            result = result[:10]
            print(f"DEBUG: Limitado a 10 artistas por corrida (de {len(todos)} totales)", flush=True)
        return result
    except Exception as e:
        print(f"DEBUG ERROR in get_batch_artistas: {e}", flush=True)
        raise
    finally:
        session.close()


def main(batch: int, total_batches: int, solo_nuevos: bool = False) -> int:
    """Procesa un batch de artistas para Spotify."""
    from db.models import FeedItem

    print(f"DEBUG: main batch={batch} total_batches={total_batches} solo_nuevos={solo_nuevos}", flush=True)
    session = SessionLocal()
    total = 0
    try:
        print("DEBUG: Creating FeedRepository", flush=True)
        feed = FeedRepository(session)
        print("DEBUG: Getting batch artists", flush=True)
        artistas = get_batch_artistas(batch, total_batches, solo_nuevos)

        if not artistas:
            print(f"Batch {batch}/{total_batches}: sin artistas que procesar", flush=True)
            return 0

        print(f"Batch {batch}/{total_batches}: {len(artistas)} artistas", flush=True)

        for artista in artistas:
            # Pequeño delay aleatorio entre artistas
            time.sleep(0.5 + (hash(artista.id) % 100) / 100.0)
            print(f"DEBUG: Procesando {artista.nombre}", flush=True)
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
                            print(f"  DEBUG: Calling get_artist_releases for {artista.nombre} (intento {intento+1})", flush=True)
                            items = get_artist_releases(artist_id, MAX_ITEMS)
                            print(f"  DEBUG: Got {len(items)} items", flush=True)
                            break
                        except Exception as e:
                            print(f"  DEBUG: Exception in get_artist_releases: {type(e).__name__}: {e}", flush=True)
                            if "Rate limit exceeded" in str(e):
                                print(f"  {artista.nombre}: Rate limit persistente, saltando artista", flush=True)
                                raise
                            if hasattr(e, "response") and e.response is not None:
                                print(f"  DEBUG: Response status: {e.response.status_code}", flush=True)
                                if e.response.status_code == 429:
                                    espera = int(e.response.headers.get("Retry-After", 2 + intento * 5))
                                    print(f"  {artista.nombre}: 429 - esperando {espera}s (intento {intento+1}/3)", flush=True)
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
                    print(f"{artista.nombre} (spotify): {exc}", flush=True)
                total += nuevos
                if nuevos:
                    print(f"  {artista.nombre}: {nuevos} nuevos en spotify", flush=True)
                time.sleep(2.0)

        print(f"Spotify batch {batch} total items nuevos: {total}", flush=True)
        return total
    except Exception as e:
        print(f"DEBUG ERROR in main: {e}", flush=True)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, required=True, help="Número de batch (0-indexado)")
    parser.add_argument("--total-batches", type=int, default=4, help="Total de batches")
    parser.add_argument("--solo-nuevos", action="store_true", help="Solo artistas sin items previos")
    args = parser.parse_args()

    main(args.batch, args.total_batches, args.solo_nuevos)