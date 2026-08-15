"""Extrae oyentes mensuales del perfil público de Spotify.

No usa la API de Spotify: lee los metadatos públicos de la página del artista.
El resultado siempre debe conservar la fecha y la fuente porque el HTML puede
cambiar y la métrica es una captura, no un valor en vivo.
"""

import re
from urllib.parse import urlparse

import requests

from scraper.errors import ScraperError

TIMEOUT = 15
FUENTE = "spotify_public_profile"


class SpotifyPublicError(ScraperError):
    """Error al consultar o interpretar el perfil público de Spotify."""


def artist_id_from_url(url: str) -> str | None:
    """Extrae el ID de artista y tolera parámetros `?si=` de Spotify."""
    path = urlparse(url or "").path.rstrip("/")
    match = re.search(r"/artist/([A-Za-z0-9]+)$", path)
    return match.group(1) if match else None


def _numero(valor: str, sufijo: str) -> int:
    """Convierte formatos como `645`, `1.2K` o `2M` a entero."""
    limpio = valor.replace(",", "").strip()
    numero = float(limpio)
    multiplicadores = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    return int(numero * multiplicadores.get(sufijo.lower(), 1))


def extraer_oyentes_html(html: str) -> int | None:
    """Extrae oyentes desde metadatos o el elemento visible de Spotify."""
    patrones = (
        r"([\d.,]+)\s*([KMB])?\s+(?:monthly listeners|oyentes mensuales)",
    )
    for patron in patrones:
        match = re.search(patron, html, re.I)
        if match:
            return _numero(match.group(1), match.group(2) or "")
    return None


def obtener_oyentes(url: str) -> int | None:
    """Consulta una página pública de Spotify y devuelve sus oyentes mensuales."""
    artist_id = artist_id_from_url(url)
    if not artist_id:
        raise SpotifyPublicError("URL de Spotify sin un ID de artista válido")
    respuesta = requests.get(
        f"https://open.spotify.com/artist/{artist_id}",
        timeout=TIMEOUT,
    )
    if respuesta.status_code != 200:
        raise SpotifyPublicError(
            f"Spotify respondió con HTTP {respuesta.status_code}"
        )
    oyentes = extraer_oyentes_html(respuesta.text)
    if oyentes is None:
        raise SpotifyPublicError("Spotify no mostró oyentes mensuales en el perfil")
    return oyentes
