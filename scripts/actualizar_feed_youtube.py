"""Actualiza el feed con los últimos videos de YouTube de cada artista.

Usa el feed RSS público del canal (`scraper/adapters/youtube.py`, sin API key,
sin consumo de cuota): para cada artista con canal vinculado, guarda sus
últimos videos en `feed_items` (sin duplicar por URL).

Uso:
    .venv/bin/python scripts/actualizar_feed_youtube.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository, FeedRepository
from scraper.adapters.youtube import latest_videos
from scraper.errors import ScraperError

MAX_VIDEOS = 15


def main():
    session = SessionLocal()
    nuevos = 0
    ya_existentes = 0
    errores = []
    try:
        for artista in ArtistRepository(session).todos():
            canales = [
                l for l in artista.links if l.plataforma == "yt" and not l.es_busqueda
            ]
            if not canales:
                continue
            for link in canales:
                try:
                    videos = latest_videos(link.url, max_videos=MAX_VIDEOS)
                except ScraperError as exc:
                    errores.append(f"{artista.nombre} · {link.url}: {exc}")
                    continue
                feed = FeedRepository(session)
                for v in videos:
                    if feed.existe_url(v["url"]):
                        ya_existentes += 1
                        continue
                    feed.crear(
                        artist_id=artista.id,
                        fuente="yt",
                        tipo="video",
                        titulo=v["titulo"],
                        url=feed._url_canonica(v["url"]),
                        fecha=v["fecha"],
                        imagen=v["imagen"] or None,
                        detalle=v["descripcion"],
                    )
                    nuevos += 1
            session.commit()
    finally:
        session.close()

    print(
        f"Videos nuevos: {nuevos} · ya registrados: {ya_existentes} · "
        f"errores: {len(errores)}"
    )
    for e in errores:
        print("  ✗", e)

    # Recalcula estado_activo con la señal más reciente del feed (igual que los
    # demás syncs), así un artista con videos recientes pasa a "activo".
    from scripts.recalcular_actividad import recalcular

    cambios = recalcular()
    print(f"Cambios de actividad: {len(cambios)}")
    for nombre, antes, despues in cambios:
        print(f"  {nombre}: {antes} → {despues}")


if __name__ == "__main__":
    main()