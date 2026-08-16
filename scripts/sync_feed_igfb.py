"""Sincroniza posts de Facebook/Instagram de artistas conectados a Meta.

Solo procesa artistas con `fb_page_token` (conectados por OAuth, ver
`backend/feed_meta.py`). Para cada uno trae los últimos posts de su página
FB y su cuenta IG de negocio y los registra en `feed_items` (sin duplicar
por URL). Al final recalcula `estado_activo`.

Uso:
    .venv/bin/python scripts/sync_feed_igfb.py
"""

import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.feed_meta import ig_bio, ig_media, pagina_about, pagina_posts
from db.database import SessionLocal
from lib.helpers import es_bio_clara
from lib.repository import ArtistRepository, FeedRepository

try:
    MAX_ITEMS = max(1, int(os.getenv("META_SYNC_LIMIT", "10")))
except ValueError:
    MAX_ITEMS = 10


def main():
    session = SessionLocal()
    total = 0
    try:
        artistas = ArtistRepository(session).conectados_meta()
        if not artistas:
            print("Ningún artista conectado a Meta todavía.")
            return

        for artista in artistas:
            nuevos = 0
            feed = FeedRepository(session)
            try:
                if artista.fb_page_id:
                    for p in pagina_posts(artista.fb_page_id, artista.fb_page_token, MAX_ITEMS):
                        if _registrar(feed, artista, "fb", p):
                            nuevos += 1
                if artista.ig_user_id:
                    for m in ig_media(artista.ig_user_id, artista.fb_page_token, MAX_ITEMS):
                        if _registrar(feed, artista, "ig", m):
                            nuevos += 1
                if not artista.bio:
                    _escribir_bio_meta(artista)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error con {artista.nombre}: {e}")
            total += nuevos
            print(f"{artista.nombre}: {nuevos} nuevos")
        print(f"Total de posts nuevos: {total}")
    finally:
        session.close()

    from scripts.recalcular_actividad import recalcular

    cambios = recalcular()
    print(f"Cambios de actividad tras el sync: {len(cambios)}")


def _registrar(feed: FeedRepository, artista, fuente: str, item: dict) -> bool:
    """Crea el FeedItem si la URL aún no existe. Devuelve True si lo creó."""
    url = item.get("url") or ""
    if not url:
        return False
    if feed.existe_url(url):
        return False
    feed.crear(
        artist_id=artista.id,
        fuente=fuente,
        tipo="post",
        titulo=(item.get("titulo") or "")[:200],
        url=url,
        fecha=item.get("fecha"),
        imagen=item.get("imagen") or None,
        detalle="",
    )
    return True


def _escribir_bio_meta(artista) -> None:
    """Escribe la bio del artista desde Meta si está clara (FB → IG).

    Solo aplica a artistas conectados (la cuenta autorizada administra la
    página), así que la fuente es del propio artista.
    """
    hoy = date.today().isoformat()
    try:
        bio = pagina_about(artista.fb_page_id, artista.fb_page_token) if artista.fb_page_id else ""
        origen = "Facebook"
        if not es_bio_clara(bio) and artista.ig_user_id:
            bio = ig_bio(artista.ig_user_id, artista.fb_page_token)
            origen = "Instagram"
        if es_bio_clara(bio):
            artista.bio = bio
            nota = f"Bio de {origen} ({hoy})."
            if not artista.notas or nota not in artista.notas:
                artista.notas = (artista.notas + " · " + nota).strip(" · ")
            print(f"Bio escrita desde Meta: {artista.nombre} ({origen})")
    except Exception as e:
        print(f"Bio de Meta no disponible para {artista.nombre}: {e}")


if __name__ == "__main__":
    main()
