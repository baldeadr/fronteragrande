"""Actualiza las fotos de perfil de los artistas desde sus redes (URLs, sin descargar).

Prioriza las **API oficiales** de los artistas conectados (Meta: página FB o
cuenta IG de negocio; YouTube Data API si hay `YOUTUBE_API_KEY`) y cae al
scraping público (`og:image`) como respaldo. El avatar de TikTok se actualiza
en `scripts/sync_feed_tiktok.py` (donde ya se rota el token).
Re-ejecutable: re-correrlo refresca las URLs (las de redes pueden caducar).
"""

import os
from datetime import datetime

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from db.models import Artist
from scraper.adapters import imagenes


def _imagen_meta(artista) -> tuple[str, str]:
    """Foto vía Graph API: página FB y, si no, cuenta IG de negocio."""
    if not artista.fb_page_id or not artista.fb_page_token:
        return "", ""
    url = imagenes.meta_picture(artista.fb_page_id, artista.fb_page_token)
    if url:
        return url, "fb"
    if artista.ig_user_id:
        url = imagenes.ig_picture(artista.ig_user_id, artista.fb_page_token)
        if url:
            return url, "ig"
    return "", ""


def _imagen_api(artista) -> tuple[str, str]:
    """Foto de perfil vía API oficiales; "" si ninguna responde."""
    if artista.fb_page_id and artista.fb_page_token:
        url, origen = _imagen_meta(artista)
        if url:
            return url, origen
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if api_key:
        url = imagenes.youtube_thumbnail_de_canal(artista.links, api_key)
        if url:
            return url, "yt"
    return "", ""


def main() -> None:
    session = SessionLocal()
    con_imagen = 0
    sin_imagen = 0
    try:
        for artista in session.query(Artist).order_by(Artist.nombre).all():
            url, origen = _imagen_api(artista)
            if not url:
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
