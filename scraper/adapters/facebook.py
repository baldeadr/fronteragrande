"""Adaptador oEmbed de Facebook (endpoint público sin token).

Endpoint: https://graph.facebook.com/v18.0/oembed_post?url={post_url}
Devuelve: {html, thumbnail_url, width, height, provider_name, ...}
Solo funciona para posts/páginas públicas.
"""

from scraper.adapters.oembed import oembed_get

FACEBOOK_OEMBED_URL = "https://graph.facebook.com/v18.0/oembed_post"


def facebook_oembed(url: str) -> dict | None:
    """Devuelve metadatos de un post público de Facebook, o `None` si falla."""
    return oembed_get(url, FACEBOOK_OEMBED_URL)


def facebook_thumbnail(url: str) -> str:
    """Extrae la URL de miniatura del oEmbed."""
    datos = facebook_oembed(url)
    return (datos or {}).get("thumbnail_url", "")


def facebook_embed_html(url: str) -> str:
    """Extrae el HTML del embed del oEmbed."""
    datos = facebook_oembed(url)
    return (datos or {}).get("html", "")