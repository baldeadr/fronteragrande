#!/usr/bin/env python3
"""Genera y actualiza la playlist semanal "Frontera Grande: Descubrimiento Semanal".

Lee de la BD (fuente de verdad) los artistas con enlace oficial de Spotify,
toma el top track de cada uno vía la Web API (client credentials) y arma una
selección aleatoria para rellenar la playlist pública. Cada corrida cambia el
contenido (rotación semanal).

Selección: cada artista entra al menos con una canción y la lista se rellena
hasta `PLAYLIST_TAMANIO` (por defecto 24) con una segunda canción de algunos
artistas. `PLAYLIST_CANCIONES_POR_ARTISTA` (por defecto 2) limita cuántas
canciones por artista pueden entrar.

La playlist es estable entre corridas: se guarda su ID en
`data/playlist_semanal.json` (versionado) para actualizar la misma lista cada
semana. Si existe la variable `SPOTIFY_PLAYLIST_ID`, esa gana sobre el archivo.

Autorización:
- Datos públicos de artistas: `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET`
  (entorno o .env, ver .env.example).
- Crear/actualizar la playlist (cuenta de usuario): autorización única del
  artista para obtener un refresh token con scope `playlist-modify-public`:

      python scripts/generar_playlist_semanal.py --auth

  El refresh token se guarda como secreto `SPOTIFY_PLAYLIST_REFRESH_TOKEN`
  (GitHub Actions) y se reutiliza en cada corrida.

Uso:
    python scripts/generar_playlist_semanal.py --auth
    python scripts/generar_playlist_semanal.py --dry-run
    python scripts/generar_playlist_semanal.py
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import sys
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

PLAYLIST_FILE = BASE_DIR / "data" / "playlist_semanal.json"
CACHE_PATH = str(BASE_DIR / "scripts" / ".spotify_playlist_cache.json")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

NOMBRE_DEFAULT = "Frontera Grande: Descubrimiento Semanal"
DESCRIPCION_DEFAULT = (
    "Rotación semanal de la escena de la frontera grande de Tamaulipas. "
    "Una selección aleatoria de canciones de los proyectos de la escena."
)


def load_env():
    """Carga las variables SPOTIFY_* desde .env de la raíz (fallback manual)."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _env_int(nombre, default):
    try:
        return max(1, int(os.getenv(nombre, str(default))))
    except ValueError:
        return default


def _url_spotify(artista):
    for link in artista.links:
        if link.plataforma == "spotify" and not link.es_busqueda and link.url:
            return link.url
    return None


def artistas_con_spotify():
    """Artistas con perfil de Spotify desde la BD (fuente de verdad)."""
    from db.database import SessionLocal
    from lib.repository import ArtistRepository

    session = SessionLocal()
    try:
        for artista in ArtistRepository(session).con_spotify():
            yield artista, _url_spotify(artista)
    finally:
        session.close()


def _token_cliente() -> str:
    from scraper.adapters.spotify import _token

    return _token()


def _pedir(funcion, *args, **kwargs):
    """Ejecuta una petición GET re-intentando ante límite de tasa (429)."""
    import time

    for intento in range(2):
        respuesta = funcion(*args, **kwargs)
        if respuesta.status_code != 429:
            return respuesta
        time.sleep(3 * (intento + 1))
    return respuesta


def _top_tracks(access_token: str, artist_id: str, limite: int) -> list[dict]:
    """Canciones más escuchadas del artista (mercado MX), normalizadas."""
    respuesta = _pedir(
        requests.get,
        f"{API_BASE}/artists/{artist_id}/top-tracks",
        params={"market": "MX"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    respuesta.raise_for_status()
    tracks = respuesta.json().get("tracks", [])
    items = []
    for t in tracks:
        items.append(
            {
                "uri": t.get("uri"),
                "titulo": t.get("name", ""),
                "artistas": ", ".join(a.get("name", "") for a in t.get("artists", [])),
            }
        )
        if len(items) >= limite:
            break
    return items


def _primeros_temas_lanzamientos(access_token: str, artist_id: str, limite: int) -> list[dict]:
    """Primer tema de los lanzamientos recientes del artista.

    Fallback al endpoint `top-tracks` (que apps en modo desarrollo no reciben,
    403): los lanzamientos propios sí llegan con client credentials.
    """
    albumes = _pedir(
        requests.get,
        f"{API_BASE}/artists/{artist_id}/albums",
        params={"include_groups": "album,single", "limit": limite * 2},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    albumes.raise_for_status()
    items = []
    for album in albumes.json().get("items", []):
        if len(items) >= limite:
            break
        tracklist = _pedir(
            requests.get,
            f"{API_BASE}/albums/{album['id']}/tracks",
            params={"limit": 1},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        if tracklist.status_code != 200:
            continue
        tema = (tracklist.json().get("items") or [None])[0]
        if not tema:
            continue
        items.append(
            {
                "uri": tema.get("uri"),
                "titulo": tema.get("name", ""),
                "artistas": ", ".join(a.get("name", "") for a in tema.get("artists", [])),
                "album": album.get("name", ""),
            }
        )
    return items


def _buscar_por_nombre(access_token: str, nombre: str, artist_id: str, limite: int) -> list[dict]:
    """Canciones del artista buscadas por nombre y filtradas por ID exacto.

    Último recurso para apps en modo desarrollo (donde top-tracks y álbumes
    están limitados): la búsqueda sí responde, y filtrar por el ID del artista
    evita los homónimos.
    """
    respuesta = _pedir(
        requests.get,
        f"{API_BASE}/search",
        params={"q": f'"{nombre}"', "type": "track", "limit": 10},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    respuesta.raise_for_status()
    items = respuesta.json().get("tracks", {}).get("items", [])
    matches = [
        t
        for t in items
        if any(a.get("id") == artist_id for a in t.get("artists", []))
    ]
    result = []
    for t in matches:
        result.append(
            {
                "uri": t.get("uri"),
                "titulo": t.get("name", ""),
                "artistas": ", ".join(a.get("name", "") for a in t.get("artists", [])),
                "album": (t.get("album") or {}).get("name", ""),
            }
        )
        if len(result) >= limite:
            break
    return result


def _canciones_artista(
    access_token: str, artist_id: str, nombre: str, limite: int
) -> tuple[list[dict], list[str]]:
    """Canciones candidatas del artista y errores de cada fuente intentada.

    Cadena de fuentes: top-tracks → primer tema por lanzamiento → búsqueda.
    """
    errores = []
    try:
        top = _top_tracks(access_token, artist_id, limite)
        if top:
            return top, errores
    except Exception as exc:
        errores.append(f"top-tracks: {exc}")
    try:
        lanzamientos = _primeros_temas_lanzamientos(access_token, artist_id, limite)
        if lanzamientos:
            return lanzamientos, errores
    except Exception as exc:
        errores.append(f"lanzamientos: {exc}")
    try:
        buscadas = _buscar_por_nombre(access_token, nombre, artist_id, limite)
        if buscadas:
            return buscadas, errores
    except Exception as exc:
        errores.append(f"búsqueda: {exc}")
    return [], errores


def seleccionar(canciones_por_artista, tamanio, por_artista) -> list[dict]:
    """Selección aleatoria: una canción por artista primero, luego rellena."""
    nombres = [n for n, canciones in canciones_por_artista.items() if canciones]
    random.shuffle(nombres)
    seleccion = []
    for nombre in nombres:
        if len(seleccion) >= tamanio:
            break
        seleccion.append(canciones_por_artista[nombre][0])
    if len(seleccion) < tamanio:
        random.shuffle(nombres)
        for nombre in nombres:
            extras = canciones_por_artista[nombre][1:por_artista]
            for cancion in extras:
                if len(seleccion) >= tamanio:
                    break
                seleccion.append(cancion)
            if len(seleccion) >= tamanio:
                break
    return seleccion


def _usuario_token() -> str:
    """Token de usuario vía refresh token (scope playlist-modify-public)."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    refresh = os.environ.get("SPOTIFY_PLAYLIST_REFRESH_TOKEN")
    if not client_id or not client_secret or not refresh:
        raise RuntimeError(
            "Faltan SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET / "
            "SPOTIFY_PLAYLIST_REFRESH_TOKEN (entorno o .env). "
            "Corre primero con --auth para obtener el refresh token."
        )
    credenciales = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    respuesta = requests.post(
        TOKEN_URL,
        data={"grant_type": "refresh_token", "refresh_token": refresh},
        headers={
            "Authorization": f"Basic {credenciales}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=15,
    )
    if respuesta.status_code != 200:
        cuerpo = respuesta.text[:300]
        raise RuntimeError(
            f"Spotify rechazó el refresh token (HTTP {respuesta.status_code}): {cuerpo}. "
            "El token debe generarse con las MISMAS credenciales "
            "(SPOTIFY_CLIENT_ID/SECRET) que se usan aquí (GitHub)."
        )
    return respuesta.json()["access_token"]


def _playlist_id(token_usuario: str) -> str:
    """ID de la playlist: variable → archivo → crea una nueva."""
    import requests

    fija = os.environ.get("SPOTIFY_PLAYLIST_ID", "").strip()
    if fija:
        return fija
    if PLAYLIST_FILE.exists():
        guardado = json.loads(PLAYLIST_FILE.read_text(encoding="utf-8"))
        if guardado.get("playlist_id"):
            return guardado["playlist_id"]

    usuario = requests.get(
        f"{API_BASE}/me",
        headers={"Authorization": f"Bearer {token_usuario}"},
        timeout=15,
    )
    usuario.raise_for_status()
    user_id = usuario.json()["id"]

    nombre = os.getenv("PLAYLIST_NOMBRE", NOMBRE_DEFAULT)
    descripcion = os.getenv("PLAYLIST_DESCRIPCION", DESCRIPCION_DEFAULT)
    creada = requests.post(
        f"{API_BASE}/users/{user_id}/playlists",
        headers={
            "Authorization": f"Bearer {token_usuario}",
            "Content-Type": "application/json",
        },
        json={"name": nombre, "description": descripcion, "public": True},
        timeout=15,
    )
    if creada.status_code == 403:
        raise SystemExit(
            "Spotify bloquea crear playlists en apps en modo desarrollo (403). "
            "Crea la playlist manualmente en Spotify (con el nombre que prefieras) "
            "y define la variable SPOTIFY_PLAYLIST_ID con su ID, que el script "
            "solo la rellenará."
        )
    creada.raise_for_status()
    playlist_id = creada.json()["id"]
    PLAYLIST_FILE.write_text(
        json.dumps({"playlist_id": playlist_id, "nombre": nombre}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Playlist creada: {nombre} (ID {playlist_id}) — guardado en data/playlist_semanal.json")
    return playlist_id


def _rellenar(token_usuario: str, playlist_id: str, uris: list[str]) -> None:
    """Reemplaza el contenido de la playlist con las canciones seleccionadas."""
    import requests

    if not uris:
        print("Sin canciones que poner en la playlist.")
        return
    respuesta = requests.put(
        f"{API_BASE}/playlists/{playlist_id}/items",
        headers={
            "Authorization": f"Bearer {token_usuario}",
            "Content-Type": "application/json",
        },
        json={"uris": uris},
        timeout=15,
    )
    respuesta.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auth", action="store_true", help="autorización única para obtener el refresh token")
    parser.add_argument("--dry-run", action="store_true", help="muestra la selección sin tocar la playlist")
    args = parser.parse_args()

    load_env()

    if args.auth:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth

        client_id = os.environ.get("SPOTIFY_CLIENT_ID")
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
        if not client_id or not client_secret:
            print("Faltan SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET (entorno o .env).")
            return 1
        print("Autenticando con Spotify (abre el navegador)...")
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=REDIRECT_URI,
            scope="playlist-modify-public playlist-modify-private",
            cache_path=CACHE_PATH,
            open_browser=True,
        )
        token = auth_manager.get_access_token(as_dict=True)
        refresh = token.get("refresh_token") or auth_manager.refresh_token
        if not refresh:
            print("[error] No se obtuvo refresh token; revisa los scopes y reintenta.")
            return 1
        usuario = spotipy.Spotify(auth_manager=auth_manager).current_user()
        print(f"Conectado: {usuario.get('display_name', '?')}")
        print("Refresh token (guárdalo como SPOTIFY_PLAYLIST_REFRESH_TOKEN en GitHub Actions):")
        print(refresh)
        return 0

    por_artista = _env_int("PLAYLIST_CANCIONES_POR_ARTISTA", 2)
    tamanio = _env_int("PLAYLIST_TAMANIO", 24)

    escena = [(a, url) for a, url in artistas_con_spotify() if url]
    if not escena:
        print("No hay artistas con perfil de Spotify en la base de datos.")
        return 1

    try:
        token_cliente = _token_cliente()
    except Exception as exc:
        if not args.dry_run:
            print(f"[error] {exc}")
            print("Corre con --dry-run o configura SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET.")
            return 1
        token_cliente = None

    from scraper.adapters.spotify import artist_id_from_url

    print("Canciones top por artista (mercado MX):")
    canciones_por_artista = {}
    for artista, url in escena:
        artist_id = artist_id_from_url(url)
        if not artist_id:
            print(f"  [skip] {artista.nombre}: URL sin ID de artista")
            continue
        try:
            if token_cliente:
                canciones, errores = _canciones_artista(
                    token_cliente, artist_id, artista.nombre, por_artista
                )
            else:
                print(f"  [--] {artista.nombre}: sin credenciales (dry-run sin top tracks)")
                canciones, errores = [], []
            canciones_por_artista[artista.nombre] = canciones
            if canciones:
                print(f"  [ok] {artista.nombre}: {', '.join(c['titulo'] for c in canciones)}")
            else:
                motivo = " | ".join(errores) if errores else "sin canciones disponibles"
                print(f"  [warn] {artista.nombre}: {motivo}")
        except Exception as exc:
            print(f"  [warn] {artista.nombre}: {exc}")
            canciones_por_artista[artista.nombre] = []

    canciones_por_artista = {n: c for n, c in canciones_por_artista.items() if c}
    seleccion = seleccionar(canciones_por_artista, tamanio, por_artista)

    print(f"\nSelección ({len(seleccion)} canciones):")
    for i, cancion in enumerate(seleccion, 1):
        print(f"  {i}. {cancion['titulo']} — {cancion['artistas']}")

    if not seleccion:
        print("No se pudo armar una selección (sin top tracks disponibles).")
        return 1

    if args.dry_run:
        print("\nDry-run: no se modificó ninguna playlist.")
        return 0

    token_usuario = _usuario_token()
    playlist_id = _playlist_id(token_usuario)
    _rellenar(token_usuario, playlist_id, [c["uri"] for c in seleccion])
    print(f"\nPlaylist actualizada: {os.getenv('PLAYLIST_NOMBRE', NOMBRE_DEFAULT)} "
          f"(ID {playlist_id}, {len(seleccion)} canciones).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
