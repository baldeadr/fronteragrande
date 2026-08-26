"""Sincroniza pistas de SoundCloud para artistas con link válido."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository, FeedRepository
from db.models import FeedItem
from scraper.adapters.soundcloud import ultimas_pistas as soundcloud_items

try:
    MAX_ITEMS = max(1, int(os.getenv("SYNC_LANZAMIENTOS_LIMIT", "20")))
except ValueError:
    MAX_ITEMS = 20


def main(artistas=None, solo_nuevos=False) -> int:
    """Sincroniza SoundCloud.

    Args:
        artistas: lista de artistas a procesar. Si None, todos con link de SoundCloud.
        solo_nuevos: si True, solo artistas sin items previos de SoundCloud.
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
                    l.plataforma == "soundcloud" and not l.es_busqueda for l in a.links
                )
            ]

        if solo_nuevos:
            artistas_con_sc = session.query(FeedItem.artist_id).filter_by(
                fuente="soundcloud"
            ).subquery()
            artistas = [a for a in artistas if a.id not in artistas_con_sc]

        for artista in artistas:
            enlaces = [
                l for l in artista.links if l.plataforma == "soundcloud" and not l.es_busqueda
            ]
            for enlace in enlaces:
                nuevos = 0
                try:
                    for item in soundcloud_items(enlace.url, MAX_ITEMS):
                        if feed.crear_si_nuevo(
                            artista.id, "soundcloud", "lanzamiento", item
                        ):
                            nuevos += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    print(f"{artista.nombre} (soundcloud): {exc}")
                total += nuevos
                if nuevos:
                    print(f"{artista.nombre}: {nuevos} nuevos en soundcloud")

        print(f"SoundCloud total items nuevos: {total}")
        return total
    finally:
        session.close()


if __name__ == "__main__":
    main()