#!/usr/bin/env python3
"""Servidor MCP local de Spotify (clonado desde architecting-a-band).

Expone tools de lectura sobre la cuenta del artista para usarlas en la
conversación con opencode: lo que suena ahora, últimas reproducidas, top
personal, búsquedas y stats de artistas.

Configuración en opencode.json y autorización única del artista con el flujo
OAuth de Spotify (abre el navegador):

    python scripts/spotify_mcp_server.py --auth

Requiere SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET (entorno o .env de la raíz,
ver .env.example). El token se guarda en scripts/.spotify_cache.json (NO se
versiona).
"""

import csv
import os
import sys
from datetime import datetime

from mcp.server.fastmcp import FastMCP

REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".spotify_cache.json")
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
STATS_CSV = os.path.join(BASE_DIR, "data", "escena_local_stats.csv")

SCOPE = (
    "user-read-currently-playing "
    "user-read-recently-played "
    "user-top-read "
    "user-library-read "
    "playlist-read-private "
    "playlist-read-collaborative"
)

mcp = FastMCP("spotify")


def load_env():
    """Carga SPOTIFY_CLIENT_ID/SECRET desde .env de la raíz (fallback manual)."""
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def get_sp():
    """Cliente lazy de Spotify (autentica solo en el primer uso)."""
    load_env()
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Faltan SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET (entorno o .env). "
            "Ver .env.example y el plan/SPOTIFY_CONEXION.md."
        )
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=CACHE_PATH,
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def _fmt_track(track):
    if not track:
        return "—"
    artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
    return f"{track.get('name', '?')} — {artists} ({track.get('album', {}).get('name', '?')})"


def _require(sp_call):
    """Ejecuta una llamada a la API; devuelve el error como texto si falla."""
    try:
        return sp_call()
    except Exception as exc:
        return f"[error] {exc}"


@mcp.tool()
def currently_playing() -> str:
    """Lo que suena ahora en la cuenta del artista (o el mensaje si no hay reproducción activa)."""
    def _call():
        data = get_sp().current_user_playing_track()
        if not data or not data.get("is_playing") or not data.get("item"):
            return "No hay reproducción activa ahora mismo."
        item = data["item"]
        parts = [_fmt_track(item)]
        progress = data.get("progress_ms")
        duration = item.get("duration_ms")
        if progress and duration:
            parts.append(f"min {int(progress / 60000)}:{int(progress % 60000) / 1000:04.1f} / {int(duration / 60000)}:{int(duration % 60000) / 1000:04.1f}")
        return " · ".join(parts)

    return _require(_call)


@mcp.tool()
def recently_played(limit: int = 10) -> str:
    """Últimas canciones reproducidas (el API expone hasta 50). Devuelve lista con hora local."""
    def _call():
        data = get_sp().current_user_recently_played(limit=min(max(limit, 1), 50))
        items = data.get("items", [])
        if not items:
            return "Sin reproducciones recientes."
        lines = []
        for i, it in enumerate(items, 1):
            played = datetime.fromisoformat(it["played_at"].replace("Z", "+00:00")).astimezone()
            lines.append(f"{i}. {_fmt_track(it.get('track'))} — {played:%Y-%m-%d %H:%M}")
        return "\n".join(lines)

    return _require(_call)


@mcp.tool()
def top_items(item_type: str = "tracks", time_range: str = "short_term", limit: int = 10) -> str:
    """Top personal del artista (tracks o artists) por período: short_term (4 semanas), medium_term (6 meses) o long_term (años)."""
    def _call():
        if item_type not in ("tracks", "artists"):
            return "[error] item_type debe ser 'tracks' o 'artists'."
        if time_range not in ("short_term", "medium_term", "long_term"):
            return "[error] time_range debe ser short_term, medium_term o long_term."
        data = get_sp().current_user_top_items(item_type, time_range=time_range, limit=min(max(limit, 1), 50))
        items = data.get("items", [])
        if not items:
            return "Sin datos en ese período."
        lines = []
        for i, it in enumerate(items, 1):
            if item_type == "tracks":
                lines.append(f"{i}. {_fmt_track(it)}")
            else:
                lines.append(f"{i}. {it.get('name')} — seguidores {it.get('followers', {}).get('total', '?')}")
        return "\n".join(lines)

    return _require(_call)


@mcp.tool()
def search(query: str, search_type: str = "artist", limit: int = 5) -> str:
    """Busca en Spotify (artist, track o album) y devuelve los resultados con ID para consultar stats."""
    def _call():
        if search_type not in ("artist", "track", "album"):
            return "[error] search_type debe ser artist, track o album."
        data = get_sp().search(query, type=search_type, limit=min(max(limit, 1), 20))
        items = data.get(search_type + "s", {}).get("items", [])
        if not items:
            return f"Sin resultados para '{query}'."
        lines = []
        for it in items:
            if search_type == "artist":
                lines.append(f"{it.get('name')} · {it.get('id')} · seguidores {it.get('followers', {}).get('total', '?')} · popularity {it.get('popularity', '?')}")
            elif search_type == "track":
                artists = ", ".join(a.get("name", "") for a in it.get("artists", []))
                lines.append(f"{it.get('name')} — {artists} · {it.get('id')}")
            else:
                lines.append(f"{it.get('name')} · {it.get('id')}")
        return "\n".join(lines)

    return _require(_call)


@mcp.tool()
def artist_stats(artist_id: str) -> str:
    """Stats públicos de un artista por su ID de Spotify: seguidores, popularity, géneros y top tracks.

    Nota: desde 2026 el API entrega estos campos en 0/None para apps en modo
    desarrollo (403 en top-tracks); la presencia (nombre/id) sí se confirma.
    """
    def _call():
        sp = get_sp()
        artist = sp.artist(artist_id)
        try:
            top = sp.artist_top_tracks(artist_id, country="MX").get("tracks", [])
        except Exception:
            top = []
        lines = [
            f"{artist.get('name')}",
            f"seguidores: {artist.get('followers', {}).get('total', '?')}",
            f"popularity (0-100): {artist.get('popularity', '?')}",
            f"géneros: {', '.join(artist.get('genres', [])) or '—'}",
            f"top tracks: {', '.join(t.get('name', '') for t in top[:3]) or '—'}",
        ]
        return "\n".join(lines)

    return _require(_call)


@mcp.tool()
def escena_local_snapshot() -> str:
    """Lee el último snapshot guardado de la escena local (data/escena_local_stats.csv)."""
    if not os.path.exists(STATS_CSV):
        return "Aún no hay snapshots. Correr antes scripts/escena_local_snapshot.py con credenciales."
    latest = {}
    with open(STATS_CSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = row.get("id", "")
            if key not in latest or row.get("fecha_captura", "") > latest[key].get("fecha_captura", ""):
                latest[key] = row
    rows = sorted(latest.values(), key=lambda r: r.get("nombre", ""))
    if not rows:
        return "El CSV de snapshots está vacío."
    lines = []
    for r in rows:
        lines.append(
            f"{r.get('nombre')} [{r.get('segmento')}] · {r.get('fecha_captura')} · "
            f"seguidores {r.get('followers')} · popularity {r.get('popularity')} · "
            f"top: {r.get('top_track_1') or '—'}"
        )
    return "\n".join(lines)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--auth":
        load_env()
        print("Autenticando con Spotify (abre el navegador)...")
        try:
            sp = get_sp()
            print(f"Conectado: {sp.current_user().get('display_name', '?')}")
        except Exception as exc:
            print(f"[error] {exc}")
            return 1
        return 0
    mcp.run()


if __name__ == "__main__":
    main()
