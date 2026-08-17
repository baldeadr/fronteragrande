"""Adaptador YouTube: últimos videos de un canal vía RSS público.

No requiere API key: se resuelve el `channel_id` desde la URL del canal
(handle/@user o /channel/) y se lee el feed de videos.
"""

import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

from scraper.errors import ScraperError

DEFAULT_TIMEOUT = 12
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Cookie": (
        "CONSENT=YES+cb.20210328-08-p0.en+FX+000; "
        "SOCS=CAISNQgQEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjMwODI5"
    ),
}
RSS_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
CHANNELS_API = "https://www.googleapis.com/youtube/v3/channels"
RE_CHANNEL_ID = re.compile(r'["\']channelId["\']\s*:\s*["\'](UC[0-9A-Za-z_-]{22})["\']')
RE_BROWSE_ID = re.compile(r'["\']browseId["\']\s*:\s*["\'](UC[0-9A-Za-z_-]{22})["\']')
RE_YT_INITIAL = re.compile(r"var ytInitialData\s*=\s*(\{.*?\});</script>", re.DOTALL)
RE_OG_DESCRIPTION = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)'
)
RE_OG_DESCRIPTION_INV = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']'
)


class YouTubeError(ScraperError):
    pass


def channel_id_from_url(url: str) -> str | None:
    """Resuelve el channel_id de una URL de canal de YouTube."""
    url = (url or "").strip()
    m = re.search(r"/channel/(UC[0-9A-Za-z_-]{22})", url)
    if m:
        return m.group(1)

    pagina = _fetch_pagina(url)
    if pagina:
        m = RE_CHANNEL_ID.search(pagina) or RE_BROWSE_ID.search(pagina)
        if m:
            return m.group(1)
    return None


def _fetch_pagina(url: str) -> str | None:
    try:
        respuesta = requests.get(url, timeout=DEFAULT_TIMEOUT, headers=HEADERS)
        if respuesta.ok:
            return respuesta.text
    except requests.RequestException:
        return None
    return None


def _parse_rss(xml_text: str, max_videos: int) -> list[dict]:
    raiz = ET.fromstring(xml_text)
    ns = {
        "a": "http://www.w3.org/2005/Atom",
        "m": "http://search.yahoo.com/mrss/",
    }
    items = []
    for entrada in raiz.findall("a:entry", ns)[:max_videos]:
        titulo = entrada.findtext("a:title", "", ns)
        enlace = entrada.find("a:link", ns)
        url = enlace.get("href") if enlace is not None else ""
        publicado = entrada.findtext("a:published", "", ns)
        fecha = None
        if publicado:
            try:
                fecha = datetime.fromisoformat(
                    publicado.replace("Z", "+00:00")
                ).replace(tzinfo=None)
            except ValueError:
                fecha = None
        media = entrada.find("m:group/m:description", ns)
        descripcion = (media.text or "")[:300] if media is not None else ""
        miniatura = entrada.find("m:group/m:thumbnail", ns)
        imagen = miniatura.get("url") if miniatura is not None else ""
        items.append(
            {
                "titulo": titulo,
                "url": url,
                "fecha": fecha,
                "descripcion": descripcion,
                "imagen": imagen,
            }
        )
    return items


def _parse_about(html: str) -> str:
    """Descripción "Acerca de" del canal desde `ytInitialData` (o `og:description`)."""
    html = html or ""
    m = RE_YT_INITIAL.search(html)
    if m:
        try:
            datos = json.loads(m.group(1))
        except ValueError:
            datos = None
        if datos:
            metadata = datos.get("metadata", {}).get("channelMetadataRenderer", {})
            descripcion = metadata.get("description") or ""
            if not descripcion:
                micro = datos.get("microformat", {}).get(
                    "microformatDataRenderer", {}
                )
                descripcion = micro.get("description") or ""
            if descripcion:
                return descripcion.strip()
    og = RE_OG_DESCRIPTION.search(html) or RE_OG_DESCRIPTION_INV.search(html)
    if og:
        return og.group(1).strip()
    return ""


def youtube_about(url: str) -> str:
    """Descripción "Acerca de" de un canal de YouTube (sin API key)."""
    pagina = _fetch_pagina(url)
    if pagina is None:
        raise YouTubeError("No se pudo leer la página del canal: " + url)
    return _parse_about(pagina)


def latest_videos(channel_url: str, max_videos: int = 5) -> list[dict]:
    """Devuelve los últimos videos publicados de un canal."""
    channel_id = channel_id_from_url(channel_url)
    if not channel_id:
        raise YouTubeError("No se pudo resolver el channel_id de: " + channel_url)

    try:
        respuesta = requests.get(
            RSS_FEED.format(channel_id=channel_id),
            timeout=DEFAULT_TIMEOUT,
            headers=HEADERS,
        )
    except requests.RequestException as exc:
        raise YouTubeError(f"Fallo de red al leer el feed de {channel_url}: {exc}")
    if not respuesta.ok:
        raise YouTubeError(
            f"El feed del canal respondió HTTP {respuesta.status_code}"
        )
    return _parse_rss(respuesta.text, max_videos)


def channel_statistics(channel_id: str, api_key: str) -> dict:
    """Obtiene estadísticas públicas de un canal mediante YouTube Data API."""
    if not channel_id or not api_key:
        raise YouTubeError("Faltan el channel_id o la clave de YouTube Data API")
    try:
        respuesta = requests.get(
            CHANNELS_API,
            params={"part": "statistics", "id": channel_id, "key": api_key},
            timeout=DEFAULT_TIMEOUT,
            headers=HEADERS,
        )
    except requests.RequestException as exc:
        raise YouTubeError(f"Fallo de red al consultar estadísticas: {exc}") from exc
    if not respuesta.ok:
        raise YouTubeError(
            f"YouTube Data API respondió HTTP {respuesta.status_code}"
        )
    try:
        datos = respuesta.json()
    except ValueError as exc:
        raise YouTubeError("Respuesta inválida de YouTube Data API") from exc
    elementos = datos.get("items") or []
    if not elementos:
        raise YouTubeError("YouTube no devolvió estadísticas para el canal")
    estadisticas = elementos[0].get("statistics") or {}

    def entero(clave: str) -> int | None:
        valor = estadisticas.get(clave)
        try:
            return int(valor) if valor is not None else None
        except (TypeError, ValueError):
            return None

    return {
        "suscriptores": None
        if estadisticas.get("hiddenSubscriberCount")
        else entero("subscriberCount"),
        "vistas": entero("viewCount"),
        "videos": entero("videoCount"),
    }
