"""Sincroniza estadísticas públicas de YouTube de los artistas.

Requiere `YOUTUBE_API_KEY`. Resuelve los canales registrados y actualiza
suscriptores y vistas totales. Si un artista tiene varios canales oficiales
(cuentas duplicadas por disputas o pérdida de acceso), las métricas se SUMAN:
cada canal sigue vigente, así el metro refleja el alcance real combinado. Si un
canal oculta los suscriptores, conserva lo anterior y no inventa un cero.

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

            suscriptores: list[int] = []
            vistas: list[int] = []
            fallos = 0
            for link in canales:
                try:
                    channel_id = channel_id_from_url(link.url)
                    if not channel_id:
                        raise ScraperError("No se pudo resolver el channel_id")
                    datos = channel_statistics(channel_id, api_key)
                except Exception as exc:
                    fallos += 1
                    print(f"  [error] {artista.nombre} · {link.url}: {exc}")
                    continue
                if datos["suscriptores"] is not None:
                    suscriptores.append(datos["suscriptores"])
                if datos["vistas"] is not None:
                    vistas.append(datos["vistas"])

            if not suscriptores and not vistas:
                if fallos == len(canales):
                    errores += 1
                    print(
                        f"Error con {artista.nombre}: no se leyeron sus "
                        f"{len(canales)} canal(es)"
                    )
                continue
            if suscriptores:
                artista.followers_yt = sum(suscriptores)
            if vistas:
                artista.vistas_yt = sum(vistas)
            artista.fecha_captura = date.today()
            session.commit()
            actualizados += 1
            n_canales = f" · {len(canales)} canales" if len(canales) > 1 else ""
            print(
                f"{artista.nombre}{n_canales}: {artista.followers_yt or 'ocultos'} "
                f"suscriptores · {artista.vistas_yt or 0} vistas"
            )
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
