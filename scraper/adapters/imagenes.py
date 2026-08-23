"""Adaptador de imágenes de perfil de artistas (sin API key).

No descarga imágenes: obtiene la **URL** pública de la foto de perfil desde la
página del artista en cada plataforma y la guarda. La web carga la imagen
directamente desde la URL remota.

Fuentes probadas:
- Spotify: la página *embed* del artista incluye su foto (image-cdn-ak.spotifycdn.com).
- Bandcamp, SoundCloud, YouTube, Instagram, Facebook, TikTok, X: se intenta `og:image` de la página.
- Instagram/Facebook/TikTok suelen bloquear scrapers (se omite si fallan).
"""

import os
import re

import requests

from scraper.jerarquias import PRIORIDAD_FOTO_DE_PERFIL as PRIORIDAD

TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126 Safari/537.36"
)
META_GRAPH = f"https://graph.facebook.com/{os.getenv('META_API_VERSION', 'v22.0')}"


def _get(url: str) -> requests.Response | None:
    try:
        return requests.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
    except requests.RequestException:
        return None


def _get_con_params(url: str, params: dict) -> requests.Response | None:
    try:
        return requests.get(
            url,
            params=params,
            timeout=TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
    except requests.RequestException:
        return None


def _og_image(html: str) -> str:
    """Extrae la URL de `og:image` de un HTML (independiente del orden de atributos)."""
    m = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html
    )
    if not m:
        m = re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            html,
        )
    return m.group(1) if m else ""


def _spotify(url: str) -> str:
    """Foto del artista desde la página embed de Spotify.

    Prefiere la foto de perfil (`ab676161`); si el artista no tiene, usa su
    imagen de cabecera (`ab67616d0000b273`, recorte grande).
    """
    m = re.search(r"artist/([0-9A-Za-z]+)", url or "")
    if not m:
        return ""
    respuesta = _get(f"https://open.spotify.com/embed/artist/{m.group(1)}")
    if respuesta is None or respuesta.status_code != 200:
        return ""
    foto = re.search(
        r"https://image-cdn-ak\.spotifycdn\.com/image/ab676161[0-9a-f]+",
        respuesta.text,
    )
    if foto:
        return foto.group(0)
    cabecera = re.search(
        r"https://image-cdn-ak\.spotifycdn\.com/image/ab67616d0000b273[0-9a-f]+",
        respuesta.text,
    )
    return cabecera.group(0) if cabecera else ""


def _og(url: str) -> str:
    """Imagen de perfil vía `og:image` de la página pública."""
    respuesta = _get(url)
    if respuesta is None or respuesta.status_code != 200:
        return ""
    return _og_image(respuesta.text)


def meta_picture(page_id: str, page_token: str) -> str:
    """Foto de la página de Facebook vía Graph API (`picture` redirige al CDN).

    Requiere el token de la página (artistas conectados). Devuelve la URL
    final tras el redirect de Meta.
    """
    respuesta = _get_con_params(
        f"{META_GRAPH}/{page_id}/picture",
        {"access_token": page_token, "type": "large"},
    )
    if respuesta is None or respuesta.status_code != 200:
        return ""
    return respuesta.url or ""


def ig_picture(ig_user_id: str, page_token: str) -> str:
    """Foto de la cuenta de Instagram de negocio (`profile_picture_url`)."""
    respuesta = _get_con_params(
        f"{META_GRAPH}/{ig_user_id}",
        {"access_token": page_token, "fields": "profile_picture_url"},
    )
    if respuesta is None or respuesta.status_code != 200:
        return ""
    try:
        return (respuesta.json().get("profile_picture_url") or "").strip()
    except ValueError:
        return ""


def youtube_thumbnail_de_canal(links, api_key: str) -> str:
    """Miniatura del canal vía YouTube Data API (requiere `YOUTUBE_API_KEY`).

    `links` es la colección de enlaces del artista; usa el primer canal
    registrado (no de búsqueda).
    """
    from scraper.adapters.youtube import channel_id_from_url

    for l in links:
        if l.plataforma != "yt" or l.es_busqueda:
            continue
        channel_id = channel_id_from_url(l.url)
        if not channel_id:
            continue
        respuesta = _get_con_params(
            "https://www.googleapis.com/youtube/v3/channels",
            {
                "part": "snippet",
                "id": channel_id,
                "fields": "items/snippet/thumbnails/high/url",
                "key": api_key,
            },
        )
        if respuesta is None or respuesta.status_code != 200:
            continue
        try:
            items = respuesta.json().get("items") or []
        except ValueError:
            continue
        if not items:
            continue
        url = (
            (items[0].get("snippet", {}).get("thumbnails", {}).get("high", {}) or {})
            .get("url", "")
            .strip()
        )
        if url:
            return url
    return ""


# Cada plataforma usa su propio extractor.
EXTRACTORES = {
    "spotify": _spotify,
    "yt": _og,
    "bandcamp": _og,
    "soundcloud": _og,
    "beatport": _og,
    "mixcloud": _og,
    "ig": _og,
    "fb": _og,
    "tt": _og,
    "x": _og,
}


def imagen_de_artista(links) -> tuple[str, str]:
    """Prueba las plataformas del artista en orden y devuelve (url, plataforma).

    `links` es una colección con atributos `plataforma`, `url` y `es_busqueda`.
    Devuelve ("", "") si ninguna plataforma expuso una imagen.
    """
    disponibles = {
        l.plataforma: l.url
        for l in links
        if not l.es_busqueda and l.url and l.plataforma in EXTRACTORES
    }
    for plataforma in PRIORIDAD:
        if plataforma not in disponibles:
            continue
        url = EXTRACTORES[plataforma](disponibles[plataforma])
        if url:
            return url, plataforma
    return "", ""


def extraer_todas_imagenes(links) -> dict[str, str]:
    """Extrae imagen de perfil de TODAS las plataformas disponibles del artista.

    Devuelve dict {plataforma: url} solo con las que devolvieron resultado.
    No hace short-circuit: prueba todas para que el admin pueda elegir.
    """
    disponibles = {
        l.plataforma: l.url
        for l in links
        if not l.es_busqueda and l.url and l.plataforma in EXTRACTORES
    }
    resultado: dict[str, str] = {}
    for plataforma, url in disponibles.items():
        img = EXTRACTORES[plataforma](url)
        if img:
            resultado[plataforma] = img
    return resultado


# Plataformas cuya URL de foto caduca (CDN firmado de Meta): no sirve
# arrastrarlas de corridas anteriores porque pueden dejar de resolver.
URL_CADUCA = {"fb", "ig"}


def fusionar_candidatas(
    previas: dict[str, str] | None,
    nuevas: dict[str, str],
    vigentes: set[str],
) -> dict[str, str]:
    """Conserva candidatas estables de corridas previas ante fallos de red.

    El scraping es intermitente: una plataforma que respondió en una corrida
    puede no responder en la siguiente. Si la URL no caduca y el enlace de esa
    plataforma sigue registrado, se arrastra la foto anterior para que la
    selección (`PRIORIDAD_FOTO_DE_PERFIL`) no degrade entre corridas.
    """
    fusion = dict(nuevas)
    for plataforma, url in (previas or {}).items():
        if (
            url
            and plataforma not in fusion
            and plataforma not in URL_CADUCA
            and plataforma in vigentes
        ):
            fusion[plataforma] = url
    return fusion
