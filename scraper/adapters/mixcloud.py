"""Adaptador de Mixcloud (oEmbed público, sin API key).

Mixcloud expone un endpoint oEmbed público para sus páginas (set, usuario,
live), útil para previsualizar contenido en el feed con miniatura y embed
oficial. Comparte la caché y la lógica de red de `scraper/adapters/oembed.py`.
"""

from scraper.adapters.oembed import oembed_get

OEMBED_ENDPOINT = "https://www.mixcloud.com/oembed/"


def mixcloud_oembed(url: str) -> dict | None:
    """Metadatos oEmbed de una URL de Mixcloud (o `None` si no aplica).

    Devuelve el dict completo del oEmbed (title, author_name,
    thumbnail_url, html...) para que el caller decida qué usar.
    """
    return oembed_get(url, OEMBED_ENDPOINT)


def mixcloud_embed_url(url: str) -> str:
    """URL embebible de un set de Mixcloud (widget oficial).

    Cae al widget de perfil cuando el oEmbed no entrega uno concreto.
    """
    datos = mixcloud_oembed(url)
    if not datos:
        return ""
    m = str(datos.get("html") or "")
    inicio = m.find("src=\"")
    if inicio == -1:
        return ""
    fin = m.find("\"", inicio + 5)
    if fin == -1:
        return ""
    return m[inicio + 5:fin]