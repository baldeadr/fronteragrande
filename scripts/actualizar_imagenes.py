"""Actualiza las fotos de perfil de los artistas desde sus redes (URLs, sin descargar).

Prioriza las **API oficiales** de los artistas conectados (Meta: página FB o
cuenta IG de negocio; YouTube Data API si hay `YOUTUBE_API_KEY`) y cae al
scraping público (`og:image`) como respaldo. El avatar de TikTok se actualiza
en `scripts/sync_feed_tiktok.py` (donde ya se rota el token).
Re-ejecutable: re-correrlo refresca las URLs (las de redes pueden caducar).
Guarda todas las URLs candidatas en `imagen_candidatas` para selección manual.
Respeta selecciones manuales (`imagen_origen == "manual"`).
"""

import os
from datetime import datetime

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from db.models import Artist
from scraper.adapters import imagenes
from scraper.jerarquias import PRIORIDAD_FOTO_DE_PERFIL


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
    respetados = 0
    try:
        for artista in session.query(Artist).order_by(Artist.nombre).all():
            # 1. Extraer TODAS las imágenes candidatas (scraping + API)
            candidatas = imagenes.extraer_todas_imagenes(artista.links)

            # 2. API oficiales (Meta, YouTube) tienen prioridad sobre scraping
            api_url, api_origen = _imagen_api(artista)
            if api_url:
                candidatas[api_origen] = api_url  # pisa si ya existía

            # 3. Seleccionar la mejor automáticamente (para imagen_perfil)
            #    Respeta selección manual: si imagen_origen == "manual", no toca imagen_perfil/imagen_origen
            seleccion_manual = artista.imagen_origen == "manual"
            url, origen = artista.imagen_perfil or "", artista.imagen_origen or ""
            if not seleccion_manual:
                url, origen = "", ""
                for plataforma in PRIORIDAD_FOTO_DE_PERFIL:
                    if plataforma in candidatas:
                        url = candidatas[plataforma]
                        origen = plataforma
                        break

            # 4. Guardar todo
            artista.imagen_candidatas = candidatas or None
            if not seleccion_manual:
                artista.imagen_perfil = url or None
                artista.imagen_origen = origen or None
            artista.imagen_actualizada = datetime.utcnow()
            if url:
                con_imagen += 1
                if seleccion_manual:
                    respetados += 1
                    print(f"[==] {artista.nombre:24s} ← {origen} (manual respetada, candidatas: {list(candidatas.keys())})")
                else:
                    print(f"[OK] {artista.nombre:24s} ← {origen} (candidatas: {list(candidatas.keys())})")
            else:
                sin_imagen += 1
                print(f"[--] {artista.nombre:24s} sin imagen")
        session.commit()
    finally:
        session.close()

    print(f"\nCon imagen: {con_imagen} · Sin imagen: {sin_imagen} · Selecciones manuales respetadas: {respetados}")


if __name__ == "__main__":
    main()
