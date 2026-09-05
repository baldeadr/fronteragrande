"""Limpia los ítems de feed duplicados por su URL canónica.

Los videos de YouTube admiten varias formas de URL para la misma pieza
(`watch?v=<id>` y `/shorts/<id>`); antes de normalizar la des-duplicación,
un mismo short podía haberse guardado dos veces con formatos distintos.
Este script deja solo la fila más antigua por video_id de YouTube y elimina
el resto.

Uso:
    .venv/bin/python scripts/limpiar_duplicados_feed.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select

from db.database import SessionLocal
from db.models import FeedItem
from lib.helpers import youtube_video_id


def main():
    session = SessionLocal()
    try:
        items = session.execute(select(FeedItem)).scalars().all()
        vistos: dict[str, FeedItem] = {}
        duplicados = 0
        for fi in items:
            vid = youtube_video_id(fi.url or "") if fi.fuente == "yt" else ""
            clave = vid or fi.url
            previo = vistos.get(clave)
            if previo is None:
                vistos[clave] = fi
                continue
            conservar = min(previo, fi, key=lambda i: i.created_at)
            eliminar = previo if conservar is not fi else fi
            session.delete(eliminar)
            duplicados += 1
        session.commit()
        print(f"Duplicados eliminados: {duplicados}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
