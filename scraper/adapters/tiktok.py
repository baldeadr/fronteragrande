"""Adaptador TikTok: metadatos de un video/post vía oEmbed público.

El perfil de TikTok bloquea bots (reto JS/captcha), así que no se puede
listar automáticamente los posts recientes de una cuenta. Sin embargo, el
endpoint oficial de oEmbed responde sin API key y devuelve título, autor,
miniatura e HTML embebible; se usa para previsualizar contenido en el feed
(la ingesta sigue siendo manual, por URL de post).
"""

import re

from scraper.adapters.oembed import oembed_get
from scraper.errors import ScraperError

OEMBED_URL = "https://www.tiktok.com/oembed"

RE_VIDEO = re.compile(r"/video/(\d{6,})")


class TikTokError(ScraperError):
    pass


def tiktok_video_id(url: str) -> str:
    """Extrae el ID numérico de un video de TikTok."""
    m = RE_VIDEO.search(url or "")
    return m.group(1) if m else ""


def tiktok_embed_url(url: str) -> str:
    """URL de iframe embebible oficial de TikTok para un video."""
    video_id = tiktok_video_id(url)
    if video_id:
        return f"https://www.tiktok.com/embed/v2/{video_id}"
    return ""


def tiktok_oembed(url: str) -> dict | None:
    """Consulta oEmbed público de TikTok (sin API key).

    Devuelve un dict con `title`, `author_name`, `thumbnail_url`,
    `video_id` y `embed_url`, o `None` si falla o no es embebible.
    """
    datos = oembed_get(url, OEMBED_URL)
    if datos is None:
        return None

    video_id = datos.get("video_id") or tiktok_video_id(url)
    if not video_id:
        return None
    return {
        "title": datos.get("title") or "",
        "author_name": datos.get("author_name") or "",
        "thumbnail_url": datos.get("thumbnail_url") or "",
        "video_id": video_id,
        "embed_url": tiktok_embed_url(url),
    }