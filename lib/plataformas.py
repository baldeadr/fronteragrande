"""Plataformas de la escena: registro único de comportamiento por red.

Centraliza (estilo `scraper/adapters/imagenes.py`) todo lo que depende de la
plataforma: detección de la fuente desde una URL, miniaturas vía oEmbed,
metadatos de enlace y previews del feed. Añadir una plataforma es registrar
su estrategia aquí, sin tocar los routers ni el feed.

Cada previewer recibe `(url, imagen_raw)` y devuelve el dict de preview o
`None` si la URL no aplica a esa plataforma.
"""

from typing import Callable

from db.models import ArtistLink
from lib.helpers import (
    facebook_embed_url,
    instagram_embed_url,
    instagram_post_code,
    youtube_thumbnail,
    youtube_video_id,
)
from scraper.adapters.facebook import facebook_oembed
from scraper.adapters.instagram import instagram_oembed
from scraper.adapters.tiktok import (
    tiktok_embed_url,
    tiktok_oembed,
    tiktok_video_id,
)

FUENTES_DETECTADAS = {
    "instagram.com": "ig",
    "facebook.com": "fb",
    "tiktok.com": "tt",
    "youtu": "yt",
}

FUENTE_CANONICA = {
    "yt": "yt",
    "youtube": "yt",
    "ig": "ig",
    "instagram": "ig",
    "fb": "fb",
    "facebook": "fb",
    "tt": "tt",
    "tiktok": "tt",
}

# Marcas de URL → plataforma, para los previews cuando la fuente no coincide.
MARCA_URL_A_PLATAFORMA = [
    ("youtu", "yt"),
    ("instagram.com", "ig"),
    ("facebook.com", "fb"),
    ("tiktok.com", "tt"),
]


def detectar_plataforma(url: str) -> str | None:
    """Detección de plataforma por dominio de la URL."""
    for dominio, fuente in FUENTES_DETECTADAS.items():
        if dominio in url:
            return fuente
    return None


def miniatura_oembed(fuente: str, url: str) -> str:
    """Miniatura vía oEmbed (solo para plataformas que lo permiten)."""
    if fuente == "ig":
        datos = instagram_oembed(url)
        return (datos or {}).get("thumbnail_url", "")
    if fuente == "fb":
        datos = facebook_oembed(url)
        return (datos or {}).get("thumbnail_url", "")
    if fuente == "tt":
        datos = tiktok_oembed(url)
        return (datos or {}).get("thumbnail_url", "")
    if fuente == "yt":
        return youtube_thumbnail(url)
    return ""


def link_con_metadatos(link: ArtistLink) -> dict:
    """Un enlace con datos extra para el 'puente a redes'."""
    plataforma = link.plataforma
    extra: dict = {}
    if plataforma == "yt":
        youtube_video_id(link.url)
        extra["canal"] = True
    if plataforma in ("spotify", "bandcamp", "soundcloud"):
        extra["embebible"] = True
    return {
        "plataforma": plataforma,
        "url": link.url,
        "es_busqueda": link.es_busqueda,
        "nota": link.nota,
        **extra,
    }


def _preview_youtube(url: str, imagen_raw: str) -> dict | None:
    video_id = youtube_video_id(url)
    if not video_id:
        return None
    return {
        "tipo": "youtube",
        "video_id": video_id,
        "embed_url": f"https://www.youtube.com/embed/{video_id}",
        "thumbnail": imagen_raw or youtube_thumbnail(url),
    }


def _preview_instagram(url: str, imagen_raw: str) -> dict | None:
    embed = instagram_embed_url(url)
    if embed:
        return {"tipo": "instagram", "embed_url": embed}
    return None


def _preview_facebook(url: str, imagen_raw: str) -> dict | None:
    embed = facebook_embed_url(url)
    if embed:
        return {"tipo": "facebook", "embed_url": embed}
    return None


def _preview_tiktok(url: str, imagen_raw: str) -> dict | None:
    datos = tiktok_oembed(url)
    if datos:
        return {
            "tipo": "tiktok",
            "video_id": datos["video_id"],
            "embed_url": datos["embed_url"],
            "thumbnail": datos["thumbnail_url"],
            "title": datos["title"],
            "author": datos["author_name"],
        }
    video_id = tiktok_video_id(url)
    if video_id:
        return {
            "tipo": "tiktok",
            "video_id": video_id,
            "embed_url": tiktok_embed_url(url),
            "thumbnail": "",
        }
    return None


PREVIEWS: dict[str, Callable[[str, str], dict | None]] = {
    "yt": _preview_youtube,
    "ig": _preview_instagram,
    "fb": _preview_facebook,
    "tt": _preview_tiktok,
}


def preview_feed(fila) -> dict:
    """Previews del feed estilo YouTube por plataforma.

    YouTube y TikTok muestran miniatura con botón de play; Instagram y
    Facebook se incrustan como iframe oficial (no se puede leer su miniatura
    sin credenciales). El resto solo imagen o texto.
    """
    url = fila.get("url")
    if isinstance(url, float) and url != url:  # NaN
        url = ""
    url = str(url or "")
    imagen_raw = fila.get("imagen")
    if isinstance(imagen_raw, float) and imagen_raw != imagen_raw:  # NaN
        imagen_raw = ""
    imagen_raw = str(imagen_raw or "")

    fuente = str(fila.get("fuente") or "").lower()
    canonical = FUENTE_CANONICA.get(fuente)
    if canonical is None:
        for marca, plataforma in MARCA_URL_A_PLATAFORMA:
            if marca in url:
                canonical = plataforma
                break

    previewer = PREVIEWS.get(canonical)
    if previewer:
        resultado = previewer(url, imagen_raw)
        if resultado:
            return resultado

    return {"tipo": "imagen" if imagen_raw else "texto", "thumbnail": imagen_raw}