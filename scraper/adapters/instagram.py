"""Adaptador oEmbed de Instagram (endpoint público sin token).

Endpoint: https://graph.facebook.com/v18.0/instagram_oembed?url={post_url}
Devuelve: {html, thumbnail_url, width, height, provider_name, ...}
"""

from scraper.adapters.oembed import oembed_get

INSTAGRAM_OEMBED_URL = "https://graph.facebook.com/v18.0/instagram_oembed"


def instagram_oembed(url: str) -> dict | None:
    """Devuelve metadatos de un post/reel público, o `None` si falla."""
    return oembed_get(url, INSTAGRAM_OEMBED_URL)


def instagram_thumbnail(url: str) -> str:
    """Extrae la URL de miniatura del oEmbed."""
    datos = instagram_oembed(url)
    return (datos or {}).get("thumbnail_url", "")


def instagram_embed_html(url: str) -> str:
    """Extrae el HTML del embed del oEmbed."""
    datos = instagram_oembed(url)
    return (datos or {}).get("html", "")