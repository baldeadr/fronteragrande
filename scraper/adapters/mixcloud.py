"""Adaptador de Mixcloud (oEmbed público + API REST, sin API key).

Mixcloud expone un endpoint oEmbed público para sus páginas (set, usuario,
live), útil para previsualizar contenido en el feed con miniatura y embed
oficial, y una API REST pública (`api.mixcloud.com`) para listar los
cloudcasts (sets subidos) de un usuario. Comparte la caché y la lógica de red
de `scraper/adapters/oembed.py`.
"""

import re
from datetime import datetime

import requests

from scraper.adapters.oembed import oembed_get
from scraper.errors import ScraperError

OEMBED_ENDPOINT = "https://www.mixcloud.com/oembed/"
API_REST = "https://api.mixcloud.com"
TIMEOUT = 15


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


def _usuario(url: str) -> str:
    """Nombre de usuario desde una URL de Mixcloud (`/usuario/...`)."""
    m = re.search(r"mixcloud\.com/([^/?#]+)", url or "")
    return m.group(1) if m else ""


def _fecha_iso(valor: str | None) -> datetime | None:
    """Convierte `created_time` ISO de la API de Mixcloud en datetime."""
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def ultimos_sets(url: str, limite: int = 6) -> list[dict]:
    """Últimos cloudcasts (sets) subidos por el usuario vía API REST pública.

    Devuelve el formato normalizado de feed (`titulo`, `url`, `fecha`,
    `imagen`); si la API no responde o el usuario no existe, lista vacía.
    """
    usuario = _usuario(url)
    if not usuario:
        return []
    try:
        respuesta = requests.get(
            f"{API_REST}/{usuario}/cloudcasts/",
            params={"limit": limite},
            timeout=TIMEOUT,
        )
    except requests.RequestException:
        return []
    if not respuesta.ok:
        return []
    items = []
    for c in respuesta.json().get("data", []):
        url_set = c.get("url") or ""
        if not url_set:
            continue
        items.append(
            {
                "titulo": c.get("name") or "",
                "url": url_set,
                "fecha": _fecha_iso(c.get("created_time")),
                "imagen": (c.get("pictures") or {}).get("large") or "",
            }
        )
    return items


def seguidores(url: str) -> int:
    """Seguidores del usuario vía API REST pública (`/usuario/`).

    Una sola llamada al perfil (sin lógica de oEmbed). Si la API no responde
    o el usuario no existe, lanza `ScraperError` para que el llamador
    conserve el valor anterior y no invente un cero.
    """
    usuario = _usuario(url)
    if not usuario:
        raise ScraperError(f"No se pudo extraer el usuario de Mixcloud: {url}")
    try:
        respuesta = requests.get(f"{API_REST}/{usuario}/", timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise ScraperError(f"Error de red con Mixcloud: {url}") from exc
    if not respuesta.ok:
        raise ScraperError(f"Mixcloud respondió HTTP {respuesta.status_code}: {url}")
    try:
        datos = respuesta.json()
    except ValueError as exc:
        raise ScraperError(f"Mixcloud devolvió JSON inválido: {url}") from exc
    try:
        return int(datos.get("follower_count") or 0)
    except (TypeError, ValueError):
        return 0