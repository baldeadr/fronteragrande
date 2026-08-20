"""Sincroniza videos y seguidores de TikTok de artistas conectados.

Solo procesa artistas con `tt_refresh_token` (conectados por OAuth, ver
`backend/feed_tiktok.py`). Para cada uno rota el refresh token, actualiza
`followers_tt` (alimenta ranking y stats) y registra los videos recientes en
`feed_items` (fuente `tt`, sin duplicar por URL). Si `video.list` no está
aprobado por TikTok, registra solo seguidores.

Uso:
    .venv/bin/python scripts/sync_feed_tiktok.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.feed_tiktok import refrescar, user_info, video_list
from db.database import SessionLocal
from lib.notificaciones import notificar_todos
from lib.repository import ArtistRepository, FeedRepository, PushSubscriptionRepository, SettingsRepository

try:
    MAX_ITEMS = max(1, int(os.getenv("TIKTOK_SYNC_LIMIT", "20")))
except ValueError:
    MAX_ITEMS = 20


def main():
    session = SessionLocal()
    total = 0
    try:
        artistas = ArtistRepository(session).conectados_tiktok()
        if not artistas:
            print("Ningún artista conectado a TikTok todavía.")
            return

        for artista in artistas:
            nuevos = 0
            feed = FeedRepository(session)
            try:
                tokens = refrescar(artista.tt_refresh_token)
                artista.tt_refresh_token = tokens["refresh_token"]
                if tokens["open_id"]:
                    artista.tt_user_id = tokens["open_id"]

                info = user_info(tokens["access_token"])
                if info["follower_count"]:
                    artista.followers_tt = info["follower_count"]
                if info["avatar_url"]:
                    artista.imagen_perfil = info["avatar_url"]
                    artista.imagen_origen = "tt"
                    artista.imagen_actualizada = datetime.utcnow()

                try:
                    for v in video_list(tokens["access_token"], MAX_ITEMS):
                        if _registrar(feed, artista, v):
                            nuevos += 1
                except Exception as exc:
                    print(f"  {artista.nombre}: video.list no disponible ({exc})")
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error con {artista.nombre}: {e}")
            total += nuevos
            print(f"{artista.nombre}: {nuevos} videos nuevos")
        print(f"Total de videos nuevos: {total}")
        if total and SettingsRepository(session).obtener_bool("notificar_auto_feed"):
            enviadas = notificar_todos(
                PushSubscriptionRepository(session),
                "Nueva actividad en Frontera Grande",
                f"Hay {total} videos nuevos de la escena.",
                "/feed",
            )
            session.commit()
            if enviadas:
                print(f"Aviso enviado a {enviadas} suscriptores")
    finally:
        session.close()

    from scripts.recalcular_actividad import recalcular

    cambios = recalcular()
    print(f"Cambios de actividad tras el sync: {len(cambios)}")


def _registrar(feed: FeedRepository, artista, video: dict) -> bool:
    """Crea el FeedItem si la URL aún no existe. Devuelve True si lo creó."""
    return feed.crear_si_nuevo(artista.id, "tt", "video", video)


if __name__ == "__main__":
    main()