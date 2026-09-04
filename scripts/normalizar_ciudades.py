"""Normaliza la ciudad de artistas y eventos a la forma canónica "Base TM/TX".

Uniforma el lado de frontera en la BD: toda ciudad de la región cerrada
(Tamaulipas + Valle del Río Grande) queda como "Ciudad TM" o "Ciudad TX"
(espejo de `web/lib/ciudades.ts`). Los valores desconocidos y `[PENDIENTE]`
se conservan tal cual (no se inventa el lado).

Uso:
    .venv/bin/python scripts/normalizar_ciudades.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from db.models import Artist, Event
from lib.helpers import normalizar_ciudad


def main() -> None:
    session = SessionLocal()
    cambios: list[tuple[str, str, str]] = []

    for artista in session.query(Artist).all():
        nuevo = normalizar_ciudad(artista.ciudad)
        if nuevo != artista.ciudad:
            cambios.append((f"artista {artista.slug}", artista.ciudad, nuevo))
            artista.ciudad = nuevo

    for evento in session.query(Event).all():
        nuevo = normalizar_ciudad(evento.ciudad)
        if nuevo != evento.ciudad:
            cambios.append((f"evento {evento.nombre!r}", evento.ciudad, nuevo))
            evento.ciudad = nuevo

    session.commit()

    if cambios:
        print(f"=== Ciudades normalizadas ({len(cambios)}) ===")
        for quien, antes, despues in sorted(cambios):
            print(f"  {quien}: {antes!r} → {despues!r}")
    else:
        print("Sin cambios: todas las ciudades ya están en forma canónica.")

    session.close()


if __name__ == "__main__":
    main()