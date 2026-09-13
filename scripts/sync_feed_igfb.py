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

from backend.feed_meta import (
    ig_bio,
    ig_media,
    ig_seguidores,
    pagina_about,
    pagina_posts,
    pagina_seguidores,
)
from db.database import SessionLocal
from lib.helpers import es_bio_clara
from lib.notificaciones import notificar_todos
from lib.repository import ArtistRepository, FeedRepository, PushSubscriptionRepository, SettingsRepository
from lib.servicios import registrar_snapshots

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
                _actualizar_seguidores_meta(artista, session)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error con {artista.nombre}: {e}")
            total += nuevos
            print(f"{artista.nombre}: {nuevos} nuevos")
        if total and SettingsRepository(session).obtener_bool("notificar_auto_feed"):
            enviadas = notificar_todos(
                PushSubscriptionRepository(session),
                "Nueva actividad en Frontera Grande",
                f"Hay {total} publicaciones nuevas de la escena.",
                "/feed",
            )
            session.commit()
            if enviadas:
                print(f"Aviso enviado a {enviadas} suscriptores")
        print(f"Total de posts nuevos: {total}")
    finally:
        session.close()

    from scripts.recalcular_actividad import recalcular

    cambios = recalcular()
    print(f"Cambios de actividad tras el sync: {len(cambios)}")


def _registrar(feed: FeedRepository, artista, fuente: str, item: dict) -> bool:
    """Crea el FeedItem si la URL aún no existe. Devuelve True si lo creó."""
    return feed.crear_si_nuevo(artista.id, fuente, "post", item)


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


def _actualizar_seguidores_meta(artista, session=None) -> None:
    """Actualiza `followers_fb`/`followers_ig` desde la Graph API.

    Solo escribe cuando la API devuelve un valor: si la página oculta sus
    seguidores o el campo falta, se conserva el valor anterior (no se
    inventa un cero), igual que en `sync_youtube_stats`. Cuando hay sesión y
    el artista está persistido (`id`), cada valor leído se registra además en
    `metric_snapshots` (el registro mensual).
    """
    actualizado = False
    medidas: list[dict] = []
    if artista.fb_page_id:
        try:
            seguidores = pagina_seguidores(artista.fb_page_id, artista.fb_page_token)
            if seguidores is not None:
                artista.followers_fb = seguidores
                medidas.append(
                    {
                        "plataforma": "fb",
                        "metrica": "seguidores",
                        "valor": seguidores,
                        "fuente": "meta_graph",
                    }
                )
                actualizado = True
        except Exception as e:
            print(f"Seguidores FB no disponibles para {artista.nombre}: {e}")
    if artista.ig_user_id:
        try:
            seguidores = ig_seguidores(artista.ig_user_id, artista.fb_page_token)
            if seguidores is not None:
                artista.followers_ig = seguidores
                medidas.append(
                    {
                        "plataforma": "ig",
                        "metrica": "seguidores",
                        "valor": seguidores,
                        "fuente": "meta_graph",
                    }
                )
                actualizado = True
        except Exception as e:
            print(f"Seguidores IG no disponibles para {artista.nombre}: {e}")
    if medidas and session is not None and getattr(artista, "id", None) is not None:
        registrar_snapshots(session, artista.id, medidas)
    if actualizado:
        artista.fecha_captura = date.today()


if __name__ == "__main__":
    main()
