#!/usr/bin/env python3
"""Snapshot de la escena local en Spotify (clonado desde architecting-a-band).

Toma un snapshot de los artistas de data/escena_local.csv que tienen perfil de
artista en Spotify (followers, popularity, géneros, top tracks) y lo agrega a
data/escena_local_stats.csv como serie temporal (una fila por artista y fecha).

Modo normal (requiere credenciales):
    python scripts/escena_local_snapshot.py

Modo dry-run (sin credenciales; solo lista qué se consultaría):
    python scripts/escena_local_snapshot.py --dry-run

Credenciales: variables SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET en el entorno
o en un archivo .env en la raíz del repo (ver .env.example). Usa el flujo
"Client Credentials" de la Web API: datos públicos de artistas, sin tocar la
cuenta de usuario del artista.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import date

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_BASE = os.path.join(BASE_DIR, "data", "escena_local.csv")
CSV_OUT = os.path.join(BASE_DIR, "data", "escena_local_stats.csv")

ARTIST_ID_RE = re.compile(r"artist/([A-Za-z0-9]+)")
TOP_TRACKS_COUNT = 3

SNAPSHOT_FIELDS = [
    "fecha_captura",
    "id",
    "nombre",
    "segmento",
    "ciudad",
    "spotify_id",
    "followers",
    "popularity",
    "genres",
    "top_track_1",
    "top_track_2",
    "top_track_3",
    "url_artista",
]


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


def extract_artist_id(url):
    """Extrae el ID de artista de una URL open.spotify.com/artist/<id>."""
    if not url:
        return None
    match = ARTIST_ID_RE.search(url)
    return match.group(1) if match else None


def load_escena():
    """Lee data/escena_local.csv y devuelve las filas con perfil de Spotify."""
    rows = []
    with open(CSV_BASE, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            spotify_id = extract_artist_id(row.get("url_spotify"))
            if not spotify_id:
                continue
            rows.append(
                {
                    "id": row.get("id", ""),
                    "nombre": row.get("nombre", ""),
                    "segmento": row.get("segmento", ""),
                    "ciudad": row.get("ciudad", ""),
                    "spotify_id": spotify_id,
                    "url_artista": row.get("url_spotify", ""),
                }
            )
    return rows


def existing_snapshots():
    """Devuelve el conjunto de (fecha_captura, id) ya registrados."""
    if not os.path.exists(CSV_OUT):
        return set()
    seen = set()
    with open(CSV_OUT, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            seen.add((row.get("fecha_captura", ""), row.get("id", "")))
    return seen


def write_rows(rows):
    """Agrega filas al CSV de snapshots (crea el archivo si no existe)."""
    new_file = not os.path.exists(CSV_OUT)
    with open(CSV_OUT, "a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=SNAPSHOT_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)


def build_row(escena_row, artist, top_tracks):
    return {
        "fecha_captura": date.today().isoformat(),
        "id": escena_row["id"],
        "nombre": escena_row["nombre"],
        "segmento": escena_row["segmento"],
        "ciudad": escena_row["ciudad"],
        "spotify_id": escena_row["spotify_id"],
        "followers": artist.get("followers", {}).get("total", 0),
        "popularity": artist.get("popularity", 0),
        "genres": ", ".join(artist.get("genres", [])),
        "top_track_1": top_tracks[0] if len(top_tracks) > 0 else "",
        "top_track_2": top_tracks[1] if len(top_tracks) > 1 else "",
        "top_track_3": top_tracks[2] if len(top_tracks) > 2 else "",
        "url_artista": escena_row["url_artista"],
    }


def top_track_names(sp, spotify_id):
    """Nombres de las N canciones más escuchadas del artista (MX)."""
    try:
        result = sp.artist_top_tracks(spotify_id, country="MX")
        return [t.get("name", "") for t in result.get("tracks", [])][:TOP_TRACKS_COUNT]
    except Exception as exc:
        print(f"  [warn] top tracks de {spotify_id}: {exc}")
        return []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="sin credenciales: solo lista los artistas a consultar")
    args = parser.parse_args()

    load_env()
    escena_rows = load_escena()

    if not escena_rows:
        print("No hay artistas con URL de Spotify en data/escena_local.csv.")
        return 1

    fecha = date.today().isoformat()
    seen = existing_snapshots()

    if args.dry_run:
        print(f"Dry-run ({fecha}) — artistas de la escena con perfil de Spotify:")
        for row in escena_rows:
            marca = " (ya capturado hoy)" if (fecha, row["id"]) in seen else ""
            print(f"  - {row['nombre']} [{row['segmento']}] {row['url_artista']}{marca}")
        print(f"\nTotal: {len(escena_rows)} artistas.")
        return 0

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Faltan SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET (entorno o .env).")
        print("Úsalas del dashboard de Spotify for Developers, o corre con --dry-run.")
        return 1

    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
    )

    new_rows = []
    for row in escena_rows:
        if (fecha, row["id"]) in seen:
            print(f"  [skip] {row['nombre']} (ya capturado hoy)")
            continue
        try:
            artist = sp.artist(row["spotify_id"])
            top_tracks = top_track_names(sp, row["spotify_id"])
            new_rows.append(build_row(row, artist, top_tracks))
            print(f"  [ok] {row['nombre']} — {artist.get('followers', {}).get('total', 0)} seguidores, popularity {artist.get('popularity', 0)}")
        except Exception as exc:
            print(f"  [error] {row['nombre']}: {exc}")

    if not new_rows:
        print("Nada nuevo que agregar.")
        return 0

    write_rows(new_rows)
    print(f"\nSnapshot guardado en data/escena_local_stats.csv ({len(new_rows)} filas).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
