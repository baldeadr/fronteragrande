"""Sincroniza lanzamientos de Bandcamp para artistas con link válido."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository, FeedRepository
from db.models import FeedItem
from scraper.adapters.bandcamp import ultimos_lanzamientos as bandcamp_items

try:
    MAX_ITEMS = max(1, int(os.getenv("SYNC_LANZAMIENTOS_LIMIT", "20")))
except ValueError:
    MAX_ITEMS = 20


def main(artistas=None, solo_nuevos=False) -> int:
    """Sincroniza Bandcamp.

    Args:
        artistas: lista de artistas a procesar. Si None, todos con link de Bandcamp.
        solo_nuevos: si True, solo artistas sin items previos de Bandcamp.
    """
    session = SessionLocal()
    total = 0
    try:
        feed = FeedRepository(session)
        repo = ArtistRepository(session)

        if artistas is None:
            artistas = [
                a
                for a in repo.todos()
                if any(
                    l.plataforma == "bandcamp" and not l.es_busqueda for l in a.links
                )
            ]

        # Filtrar solo_nuevos
        if solo_nuevos:
            artistas_con_bc = session.query(FeedItem.artist_id).filter_by(
                fuente="bandcamp"
            ).subquery()
            artistas = [a for a in artistas if a.id not in artistas_con_bc]

        for artista in artistas:
            enlaces = [
                l for l in artista.links if l.plataforma == "bandcamp" and not l.es_busqueda
            ]
            for enlace in enlaces:
                nuevos = 0
                try:
                    for item in bandcamp_items(enlace.url, MAX_ITEMS):
                        if feed.crear_si_nuevo(
                            artista.id, "bandcamp", "lanzamiento", item
                        ):
                            nuevos += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    print(f"{artista.nombre} (bandcamp): {exc}")
                total += nuevos
                if nuevos:
                    print(f"{artista.nombre}: {nuevos} nuevos en bandcamp")

        print(f"Bandcamp total items nuevos: {total}")
        return total
    finally:
        session.close()


if __name__ == "__main__":
    main()