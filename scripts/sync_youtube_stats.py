"""Sincroniza estadísticas públicas de YouTube de los artistas.

Requiere `YOUTUBE_API_KEY`. Resuelve el canal desde el enlace registrado y
actualiza suscriptores, vistas totales y fecha de captura. Si un canal oculta
los suscriptores, conserva el valor anterior y no inventa un cero.

Uso:
    .venv/bin/python scripts/sync_youtube_stats.py
"""

import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository
from scraper.adapters.youtube import channel_id_from_url, channel_statistics
from scraper.errors import ScraperError


def sincronizar(api_key: str) -> tuple[int, int]:
    """Sincroniza canales y devuelve `(actualizados, errores)`."""
    session = SessionLocal()
    actualizados = 0
    errores = 0
    try:
        for artista in ArtistRepository(session).todos():
            canales = [
                link
                for link in artista.links
                if link.plataforma == "yt" and not link.es_busqueda
            ]
            if not canales:
                continue
            try:
                channel_id = channel_id_from_url(canales[0].url)
                if not channel_id:
                    raise ScraperError("No se pudo resolver el channel_id")
                datos = channel_statistics(channel_id, api_key)
                if datos["suscriptores"] is not None:
                    artista.followers_yt = datos["suscriptores"]
                if datos["vistas"] is not None:
                    artista.vistas_yt = datos["vistas"]
                artista.fecha_captura = date.today()
                session.commit()
                actualizados += 1
                print(
                    f"{artista.nombre}: {artista.followers_yt or 'ocultos'} "
                    f"suscriptores · {artista.vistas_yt or 0} vistas"
                )
            except Exception as exc:
                session.rollback()
                errores += 1
                print(f"Error con {artista.nombre}: {exc}")
    finally:
        session.close()
    return actualizados, errores


def main() -> None:
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        print("YOUTUBE_API_KEY no está configurada; no se sincronizó nada.")
        return
    actualizados, errores = sincronizar(api_key)
    print(f"Canales actualizados: {actualizados} · errores: {errores}")


if __name__ == "__main__":
    main()
