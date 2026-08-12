"""Actualiza las fotos de perfil de los artistas desde sus redes (URLs, sin descargar).

Recorre todos los artistas, prueba sus plataformas en orden de preferencia y
guarda la primera imagen de perfil que cada uno expone públicamente.
Re-ejecutable: re-correrlo refresca las URLs (las de redes pueden caducar).
"""

from datetime import datetime

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from db.models import Artist
from scraper.adapters import imagenes


def main() -> None:
    session = SessionLocal()
    con_imagen = 0
    sin_imagen = 0
    try:
        for artista in session.query(Artist).order_by(Artist.nombre).all():
            url, origen = imagenes.imagen_de_artista(artista.links)
            artista.imagen_perfil = url or None
            artista.imagen_origen = origen or None
            artista.imagen_actualizada = datetime.utcnow()
            if url:
                con_imagen += 1
                print(f"[OK] {artista.nombre:24s} ← {origen}")
            else:
                sin_imagen += 1
                print(f"[--] {artista.nombre:24s} sin imagen")
        session.commit()
    finally:
        session.close()

    print(f"\nCon imagen: {con_imagen} · Sin imagen: {sin_imagen}")


if __name__ == "__main__":
    main()
