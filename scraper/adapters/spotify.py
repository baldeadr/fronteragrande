"""Adaptador Spotify: stats de artistas (oyentes/seguidores) desde la API.

Requiere credenciales en `.env` (SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET).
Si no están configuradas, las funciones lanzan `SpotifyNoConfigurado`.
"""

import base64
import os
import re
from datetime import date

import requests

from scraper.errors import ScraperError

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"


class SpotifyNoConfigurado(ScraperError):
    pass


def _token() -> str:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SpotifyNoConfigurado(
            "SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET no configurados en .env"
        )
    credenciales = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()
    respuesta = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        headers={
            "Authorization": f"Basic {credenciales}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=15,
    )
    respuesta.raise_for_status()
    return respuesta.json()["access_token"]


def artist_id_from_url(url: str) -> str | None:
    match = re.search(r"/artist/([A-Za-z0-9]+)", url or "")
    return match.group(1) if match else None


def get_artist(artist_id: str) -> dict:
    """Trae nombre, seguidores, popularidad y géneros de un artista."""
    token = _token()
    respuesta = requests.get(
        f"{API_BASE}/artists/{artist_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    respuesta.raise_for_status()
    datos = respuesta.json()
    return {
        "spotify_id": datos.get("id"),
        "nombre": datos.get("name"),
        "followers": (datos.get("followers") or {}).get("total"),
        "popularity": datos.get("popularity"),
        "genres": datos.get("genres", []),
        "url_artista": datos.get("external_urls", {}).get("spotify"),
    }


def _fecha_lanzamiento(valor: str | None) -> date | None:
    """Convierte el `release_date` de Spotify (YYYY, YYYY-MM o YYYY-MM-DD)."""
    if not valor:
        return None
    try:
        partes = [int(p) for p in valor.split("-")]
    except ValueError:
        return None
    if not 1 <= len(partes) <= 3:
        return None
    while len(partes) < 3:
        partes.append(1)
    try:
        return date(partes[0], partes[1], partes[2])
    except ValueError:
        return None


def get_artist_releases(artist_id: str, limite: int = 10) -> list[dict]:
    """Últimos lanzamientos propios del artista (álbumes y sencillos).

    Devuelve el formato normalizado de feed (`titulo`, `url`, `fecha`,
    `imagen`) más `tipo_lanzamiento` ("album"/"single"). No incluye
    apariciones ni compilaciones (`include_groups=album,single`).
    """
    token = _token()
    respuesta = requests.get(
        f"{API_BASE}/artists/{artist_id}/albums",
        params={"include_groups": "album,single", "limit": limite},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    respuesta.raise_for_status()
    items = []
    for a in respuesta.json().get("items", []):
        items.append(
            {
                "titulo": a.get("name") or "",
                "url": (a.get("external_urls") or {}).get("spotify") or "",
                "fecha": _fecha_lanzamiento(a.get("release_date")),
                "imagen": (a.get("images") or [{}])[0].get("url", ""),
                "tipo_lanzamiento": a.get("album_type") or "",
            }
        )
    return items
