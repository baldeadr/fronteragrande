"""Registra los eventos publicados por artistas conectados a Meta.

Solo procesa artistas con `fb_page_token` (conectados por OAuth, ver
`backend/feed_meta.py`) y con el permiso `pages_events` en el token. Para
cada uno trae los eventos de su página de Facebook y los registra en la
tabla `events` (sin duplicar por fuente) con el artista como promotor del
cartel. Al final recalcula `estado_activo` (un evento también es señal).

Uso:
    .venv/bin/python scripts/sync_eventos_meta.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.feed_meta import pagina_eventos
from db.database import SessionLocal
from lib.repository import ArtistRepository, EventRepository

MAX_ITEMS = max(1, int(os.getenv("META_SYNC_LIMIT", "25")))

FUENTE_TEXTO = "Facebook (página del artista) · {evento_id}"


def _registrar(eventos: EventRepository, artista, evento: dict) -> bool:
    """Crea el evento si su fuente (id de Facebook) aún no existe. True si lo creó."""
    fuente = FUENTE_TEXTO.format(evento_id=evento["id"])
    if eventos.por_fuente(fuente) is not None:
        return False
    eventos.crear(
        nombre=evento["nombre"],
        fecha=evento["fecha"].date(),
        lugar=evento["lugar"],
        ciudad=artista.ciudad or "",
        artistas=artista.nombre,
        que_demuestra="Evento publicado por el artista en su página de Facebook (fuente propia)",
        fuente=fuente,
    )
    return True


def main():
    session = SessionLocal()
    total = 0
    sin_permiso = 0
    try:
        artistas = ArtistRepository(session).conectados_meta()
        if not artistas:
            print("Ningún artista conectado a Meta todavía.")
            return
        eventos = EventRepository(session)
        for artista in artistas:
            if not artista.fb_page_id:
                continue
            nuevos = 0
            try:
                for e in pagina_eventos(artista.fb_page_id, artista.fb_page_token, MAX_ITEMS):
                    if _registrar(eventos, artista, e):
                        nuevos += 1
                session.commit()
            except Exception as exc:
                session.rollback()
                mensaje = str(exc).lower()
                if "permission" in mensaje or "pages_events" in mensaje:
                    sin_permiso += 1
                    print(f"{artista.nombre}: token sin permiso pages_events")
                else:
                    print(f"Error con {artista.nombre}: {exc}")
            total += nuevos
            print(f"{artista.nombre}: {nuevos} eventos nuevos")
        if sin_permiso:
            print(
                f"{sin_permiso} artista(s) necesitan reconectar Meta "
                "para conceder el permiso pages_events."
            )
        print(f"Total de eventos nuevos: {total}")
    finally:
        session.close()

    from scripts.recalcular_actividad import recalcular

    cambios = recalcular()
    print(f"Cambios de actividad tras el sync: {len(cambios)}")


if __name__ == "__main__":
    main()