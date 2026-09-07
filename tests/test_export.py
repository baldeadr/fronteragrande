"""Contrato del CSV semilla: round-trip exportar → seed en BD vacía.

La BD es la fuente de verdad; el CSV es bootstrap + export. Este test protege
que el exportador (`db.export`) produzca un CSV que el seed (`db.seed`) pueda
volver a cargar y re-exportar de forma idéntica (sin perder datos ni mutar el
esquema documental).
"""

import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from db.database import SessionLocal
from db.export import exportar_artistas, exportar_eventos
from db.models import Base
from db.seed import cargar_artistas, cargar_eventos


def _iguales(ruta_a: str, ruta_b: str) -> bool:
    return Path(ruta_a).read_text(encoding="utf-8") == Path(ruta_b).read_text(
        encoding="utf-8"
    )


def test_round_trip_export_seed_export():
    with tempfile.TemporaryDirectory() as tmp:
        csv_1 = str(Path(tmp) / "escena_local.csv")
        csv_2 = str(Path(tmp) / "escena_local_2.csv")
        eventos_1 = str(Path(tmp) / "eventos.csv")
        eventos_2 = str(Path(tmp) / "eventos_2.csv")

        # Export 1 desde la BD sembrada por el conftest.
        s1 = SessionLocal()
        try:
            n_artistas = exportar_artistas(s1, csv_path=csv_1, respaldo=False)
            n_eventos = exportar_eventos(s1, csv_path=eventos_1, respaldo=False)
        finally:
            s1.close()
        assert n_artistas > 0
        assert n_eventos > 0

        # BD vacía nueva, re-sembrada desde el CSV exportado.
        engine = create_engine(f"sqlite:///{tmp}/roundtrip.db")
        Base.metadata.create_all(engine)
        Sesion = sessionmaker(bind=engine)
        s2 = Sesion()
        try:
            cargar_artistas(s2, csv_path=csv_1)
            cargar_eventos(s2, csv_path=eventos_1)
        finally:
            s2.close()

        # Export 2 desde la BD re-sembrada: debe ser idéntico al primero.
        s3 = Sesion()
        try:
            n_artistas_2 = exportar_artistas(s3, csv_path=csv_2, respaldo=False)
            n_eventos_2 = exportar_eventos(s3, csv_path=eventos_2, respaldo=False)
        finally:
            s3.close()

        assert n_artistas_2 == n_artistas
        assert n_eventos_2 == n_eventos
        assert _iguales(csv_1, csv_2)
        assert _iguales(eventos_1, eventos_2)


def test_round_trip_preserva_varias_urls_de_una_plataforma():
    """Si un artista tiene dos perfiles oficiales de la misma plataforma (ej.
    cuentas duplicadas de Spotify/YouTube), el export no pisa el secundario: la
    celda los une con ` | ` y el seed vuelve a separarlos en dos enlaces."""
    from db.models import Artist, ArtistLink

    with tempfile.TemporaryDirectory() as tmp:
        engine = create_engine(f"sqlite:///{tmp}/multi.db")
        Base.metadata.create_all(engine)
        Sesion = sessionmaker(bind=engine)

        s = Sesion()
        artista = Artist(
            slug="doble_spotify",
            nombre="Doble Spotify",
            segmento="Solista",
            ciudad="Reynosa TM",
        )
        artista.links = [
            ArtistLink(plataforma="spotify", url="https://open.spotify.com/artist/abc"),
            ArtistLink(plataforma="spotify", url="https://open.spotify.com/artist/leg"),
            ArtistLink(plataforma="yt", url="https://www.youtube.com/@canal-a"),
            ArtistLink(plataforma="yt", url="https://www.youtube.com/@canal-b"),
        ]
        s.add(artista)
        s.commit()
        s.close()

        csv_1 = str(Path(tmp) / "escena_local.csv")
        s = Sesion()
        exportar_artistas(s, csv_path=csv_1, respaldo=False)
        s.close()

        # Re-seed en una BD nueva y re-export: nada debe perderse.
        engine2 = create_engine(f"sqlite:///{tmp}/multi2.db")
        Base.metadata.create_all(engine2)
        Sesion2 = sessionmaker(bind=engine2)
        s2 = Sesion2()
        cargar_artistas(s2, csv_path=csv_1)
        s2.close()

        csv_2 = str(Path(tmp) / "escena_local_2.csv")
        s3 = Sesion2()
        exportar_artistas(s3, csv_path=csv_2, respaldo=False)
        s3.close()
        assert _iguales(csv_1, csv_2)

        # La BD re-sembrada conserva los dos enlaces de cada plataforma.
        s4 = Sesion2()
        try:
            fila = s4.execute(
                select(Artist).where(Artist.slug == "doble_spotify")
            ).scalar_one()
            urls = sorted(l.url for l in fila.links)
            assert urls == [
                "https://open.spotify.com/artist/abc",
                "https://open.spotify.com/artist/leg",
                "https://www.youtube.com/@canal-a",
                "https://www.youtube.com/@canal-b",
            ]
        finally:
            s4.close()


def test_export_artistas_respeta_esquema():
    """El exportador escribe exactamente las columnas del seed."""
    import csv as _csv

    with tempfile.TemporaryDirectory() as tmp:
        ruta = str(Path(tmp) / "escena_local.csv")
        s = SessionLocal()
        try:
            exportar_artistas(s, csv_path=ruta, respaldo=False)
        finally:
            s.close()
        with open(ruta, encoding="utf-8") as fh:
            lector = _csv.DictReader(fh)
            columnas = lector.fieldnames
        from db.export import COLUMNAS_ARTISTA

        assert columnas == COLUMNAS_ARTISTA