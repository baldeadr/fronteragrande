"""Registra en el feed el contenido nuevo de cada artista por plataforma.

Plataformas y su vía de datos (ver `scraper/adapters/`):
- **Spotify**: API oficial (álbumes y sencillos propios, client credentials).
- **Bandcamp**: cuadrícula de la página del artista (fecha = año del título).
- **SoundCloud**: api-v2 pública (client_id extraído del bundle de la web).
- **Beatport**: `__NEXT_DATA__` de la página del artista (sin API pública).
- **Mixcloud**: API REST pública (`api.mixcloud.com`).

Todos los items pasan por `FeedRepository.crear_si_nuevo` (sin duplicar por
URL). No hay ventana temporal: entra todo el historial de lanzamientos que
exponga cada plataforma (más historial, mejor). El tope `SYNC_LANZAMIENTOS_LIMIT`
limita cuántos items por plataforma se consultan (no es una ventana). Al final
recalcula `estado_activo`.

Uso:
    .venv/bin/python scripts/sync_lanzamientos.py
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.notificaciones import notificar_todos
from lib.repository import (
    ArtistRepository,
    FeedRepository,
    PushSubscriptionRepository,
    SettingsRepository,
)
from scraper.adapters.bandcamp import ultimos_lanzamientos as bandcamp_items
from scraper.adapters.beatport import ultimos_lanzamientos as beatport_items
from scraper.adapters.mixcloud import ultimos_sets as mixcloud_items
from scraper.adapters.soundcloud import ultimas_pistas as soundcloud_items
from scraper.adapters.spotify import artist_id_from_url, get_artist_releases

try:
    MAX_ITEMS = max(1, int(os.getenv("SYNC_LANZAMIENTOS_LIMIT", "20")))
except ValueError:
    MAX_ITEMS = 20


def _extraer_spotify(artista, enlace, limite: int) -> list[dict]:
    artist_id = artist_id_from_url(enlace.url)
    if not artist_id:
        return []
    return get_artist_releases(artist_id, limite)


# Cada plataforma: (extractor de items normalizados, nombre de fuente).
PLATAFORMAS = {
    "spotify": _extraer_spotify,
    "bandcamp": lambda a, e, n: bandcamp_items(e.url, n),
    "soundcloud": lambda a, e, n: soundcloud_items(e.url, n),
    "beatport": lambda a, e, n: beatport_items(e.url, n),
    "mixcloud": lambda a, e, n: mixcloud_items(e.url, n),
}


def main() -> None:
    session = SessionLocal()
    total = 0
    try:
        feed = FeedRepository(session)
        for artista in ArtistRepository(session).todos():
            enlaces = [l for l in artista.links if l.plataforma in PLATAFORMAS and not l.es_busqueda]
            for enlace in enlaces:
                nuevos = 0
                try:
                    for item in PLATAFORMAS[enlace.plataforma](artista, enlace, MAX_ITEMS):
                        if feed.crear_si_nuevo(
                            artista.id, enlace.plataforma, "lanzamiento", item
                        ):
                            nuevos += 1
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    print(f"{artista.nombre} ({enlace.plataforma}): {exc}")
                total += nuevos
                if enlace.plataforma == "spotify":
                    time.sleep(0.5)
                if nuevos:
                    print(f"{artista.nombre}: {nuevos} nuevos en {enlace.plataforma}")
        if total and SettingsRepository(session).obtener_bool("notificar_auto_feed"):
            enviadas = notificar_todos(
                PushSubscriptionRepository(session),
                "Nuevo material en Frontera Grande",
                f"Hay {total} lanzamientos nuevos de la escena.",
                "/feed",
            )
            session.commit()
            if enviadas:
                print(f"Aviso enviado a {enviadas} suscriptores")
        print(f"Total de items nuevos: {total}")
    finally:
        session.close()

    from scripts.recalcular_actividad import recalcular

    cambios = recalcular()
    print(f"Cambios de actividad tras el sync: {len(cambios)}")


if __name__ == "__main__":
    main()