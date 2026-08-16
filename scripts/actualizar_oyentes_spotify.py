"""Captura oyentes mensuales de perfiles públicos de Spotify.

Procesa únicamente artistas con un enlace oficial de Spotify registrado en la
BD (fuente de verdad). No consulta artistas sin URL ni intenta descubrir
perfiles ambiguos.

Uso:
    .venv/bin/python scripts/actualizar_oyentes_spotify.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository, SpotifySnapshotRepository
from scraper.adapters.spotify_public import SpotifyPublicError, obtener_oyentes


def _url_spotify(artista):
    for link in artista.links:
        if link.plataforma == "spotify" and not link.es_busqueda and link.url:
            return link.url
    return None


def main() -> int:
    session = SessionLocal()
    total = 0
    try:
        artistas = ArtistRepository(session).con_spotify()
        snapshots = SpotifySnapshotRepository(session)
        print(f"Artistas con Spotify oficial: {len(artistas)}")
        for artista in artistas:
            url = _url_spotify(artista)
            if not url:
                continue
            try:
                oyentes = obtener_oyentes(url)
                artista.oyentes_mensuales_spotify = oyentes
                artista.fecha_oyentes_spotify = datetime.utcnow()
                artista.fuente_oyentes_spotify = "spotify_public_profile"
                snapshots.crear(
                    artist_id=artista.id,
                    url_spotify=url,
                    oyentes_mensuales=oyentes,
                )
                session.commit()
                total += 1
                print(f"  [ok] {artista.nombre}: {oyentes:,} oyentes mensuales")
            except (SpotifyPublicError, ValueError) as exc:
                session.rollback()
                snapshots.crear(
                    artist_id=artista.id,
                    url_spotify=url,
                    oyentes_mensuales=None,
                    estado="error",
                    detalle=str(exc),
                )
                session.commit()
                print(f"  [error] {artista.nombre}: {exc}")
        print(f"Capturas correctas: {total}/{len(artistas)}")
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
