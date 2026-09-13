"""Captura oyentes mensuales de perfiles públicos de Spotify.

Procesa únicamente artistas con un enlace oficial de Spotify registrado en la
BD (fuente de verdad). No consulta artistas sin URL ni intenta descubrir
perfiles ambiguos. Si un artista tiene varios perfiles oficiales (cuentas
duplicadas), se registran sus oyentes por separado y en el artista se guarda
la SUMA, que es la que alimenta el índice, el perfil y las stats.

Uso:
    .venv/bin/python scripts/actualizar_oyentes_spotify.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.repository import ArtistRepository, SpotifySnapshotRepository
from lib.servicios import registrar_snapshots
from scraper.adapters.spotify_public import SpotifyPublicError, obtener_oyentes


def _urls_spotify(artista) -> list[str]:
    """Todos los perfiles oficiales de Spotify del artista (fuente de verdad).

    Si hay varios (cuentas duplicadas por contratos, disputas o pérdida de
    acceso), sus oyentes mensuales se SUMAN: cada perfil sigue vigente y con
    reproducciones, así el metro refleja el alcance real combinado.
    """
    return [
        link.url
        for link in artista.links
        if link.plataforma == "spotify" and not link.es_busqueda and link.url
    ]


def main() -> int:
    session = SessionLocal()
    total = 0
    try:
        artistas = ArtistRepository(session).con_spotify()
        snapshots = SpotifySnapshotRepository(session)
        print(f"Artistas con Spotify oficial: {len(artistas)}")
        for artista in artistas:
            urls = _urls_spotify(artista)
            if not urls:
                continue
            suma = 0
            leidos = 0
            for url in urls:
                try:
                    oyentes = obtener_oyentes(url)
                    suma += oyentes or 0
                    leidos += 1
                    snapshots.crear(
                        artist_id=artista.id,
                        url_spotify=url,
                        oyentes_mensuales=oyentes,
                    )
                    print(f"  [ok] {artista.nombre} · {url}: {oyentes:,} oyentes")
                except (SpotifyPublicError, ValueError) as exc:
                    snapshots.crear(
                        artist_id=artista.id,
                        url_spotify=url,
                        oyentes_mensuales=None,
                        estado="error",
                        detalle=str(exc),
                    )
                    print(f"  [error] {artista.nombre} · {url}: {exc}")
            if leidos:
                artista.oyentes_mensuales_spotify = suma
                artista.fecha_oyentes_spotify = datetime.utcnow()
                artista.fuente_oyentes_spotify = "spotify_public_profile"
                registrar_snapshots(
                    session,
                    artista.id,
                    [
                        {
                            "plataforma": "spotify",
                            "metrica": "oyentes_mensuales",
                            "valor": suma,
                            "fuente": "spotify_public_profile",
                        },
                    ],
                )
                total += 1
                plural = "perfiles" if len(urls) > 1 else "perfil"
                print(
                    f"  => {artista.nombre}: {suma:,} oyentes mensuales "
                    f"({leidos} {plural} leído{'s' if len(urls) > 1 else ''})"
                )
            session.commit()
        print(f"Capturas correctas: {total}/{len(artistas)}")
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
