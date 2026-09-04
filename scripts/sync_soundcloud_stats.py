"""Sincroniza las reproducciones de SoundCloud de los artistas con link.

Suma el `playback_count` de todas las pistas públicas vía la api-v2 de
SoundCloud (`scraper/adapters/soundcloud.py::reproducciones`). Si la fuente no
se puede leer, conserva el valor anterior y no inventa un cero.

Uso:
    .venv/bin/python scripts/sync_soundcloud_stats.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository
from scraper.adapters.soundcloud import reproducciones


def sincronizar() -> tuple[int, int]:
    """Sincroniza las reproducciones y devuelve `(actualizados, errores)`."""
    session = SessionLocal()
    actualizados = 0
    errores = 0
    try:
        for artista in ArtistRepository(session).todos():
            enlaces = [
                l
                for l in artista.links
                if l.plataforma == "soundcloud" and not l.es_busqueda
            ]
            if not enlaces:
                continue
            try:
                total = reproducciones(enlaces[0].url)
                artista.reproducciones_soundcloud = total
                artista.fecha_captura = date.today()
                session.commit()
                actualizados += 1
                print(f"{artista.nombre}: {total} reproducciones en soundcloud")
            except Exception as exc:
                session.rollback()
                errores += 1
                print(f"Error con {artista.nombre}: {exc}")
    finally:
        session.close()
    return actualizados, errores


def main() -> None:
    actualizados, errores = sincronizar()
    print(f"Artistas actualizados: {actualizados} · errores: {errores}")


if __name__ == "__main__":
    main()