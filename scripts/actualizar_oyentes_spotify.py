"""Captura oyentes mensuales de perfiles públicos de Spotify.

Procesa únicamente artistas con un enlace oficial de Spotify registrado. No
consulta artistas sin URL ni intenta descubrir perfiles ambiguos.

Uso:
    .venv/bin/python scripts/actualizar_oyentes_spotify.py
"""

import sys
import csv
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository, LinkRepository, SpotifySnapshotRepository
from scraper.adapters.spotify_public import SpotifyPublicError, obtener_oyentes


def _url_spotify(artista):
    for link in artista.links:
        if link.plataforma == "spotify" and not link.es_busqueda and link.url:
            return link.url
    return None


def _urls_semilla() -> dict[str, str]:
    """Lee URLs de Spotify confirmadas del CSV sin tocar otros campos."""
    ruta = Path(__file__).resolve().parent.parent / "data/escena_local.csv"
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return {
            fila["id"]: fila["url_spotify"].strip()
            for fila in csv.DictReader(archivo)
            if fila.get("url_spotify", "").strip()
        }


def _completar_urls_desde_csv(session) -> int:
    """Añade solo URLs de Spotify ausentes en la BD de producción."""
    urls = _urls_semilla()
    links = LinkRepository(session)
    agregadas = 0
    for artista in ArtistRepository(session).todos():
        if _url_spotify(artista) or not urls.get(artista.slug):
            continue
        links.crear_para_artista(
            artista,
            plataforma="spotify",
            url=urls[artista.slug],
        )
        agregadas += 1
    if agregadas:
        session.commit()
    return agregadas


def main() -> int:
    session = SessionLocal()
    total = 0
    try:
        agregadas = _completar_urls_desde_csv(session)
        if agregadas:
            print(f"URLs de Spotify agregadas desde el CSV: {agregadas}")
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
