"""Carga (seed) de la base de datos desde los CSV.

Fuente de verdad: `data/escena_local.csv` y `data/eventos.csv`, que se
mantienen en sincronía con `architecting-a-band` (ESCENA_LOCAL.md).
"""

from datetime import date, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import SessionLocal, engine
from db.models import Artist, ArtistLink, Base, Event

_RAIZ = Path(__file__).resolve().parent.parent

SEED_ARTISTS = str(_RAIZ / "data/escena_local.csv")
SEED_EVENTS = str(_RAIZ / "data/eventos.csv")

COLUMNAS_LINKS = {
    "url_ig": "ig",
    "url_fb": "fb",
    "url_yt": "yt",
    "url_tt": "tt",
    "url_spotify": "spotify",
    "url_bandcamp": "bandcamp",
    "url_soundcloud": "soundcloud",
    "url_apple": "apple",
    "url_linktree": "linktree",
    "url_x": "x",
}

COLUMNAS_FOLLOWERS = {
    "followers_ig": "followers_ig",
    "followers_fb": "followers_fb",
    "followers_yt": "followers_yt",
    "followers_tt": "followers_tt",
    "followers_spotify": "followers_spotify",
}

COLUMNAS_METRICAS = {
    "vistas_yt": "vistas_yt",
    "vistas_tt": "vistas_tt",
    "reproducciones_spotify": "reproducciones_spotify",
    "reproducciones_bandcamp": "reproducciones_bandcamp",
    "reproducciones_soundcloud": "reproducciones_soundcloud",
}

FECHA_COLUMNAS = [
    "fecha_captura",
    "ultimo_lanzamiento",
    "ultimo_evento",
    "fecha_registro",
]


def _normalizar(valor):
    """Devuelve el valor limpio o la cadena vacía."""
    if pd.isna(valor):
        return ""
    valor = str(valor).strip()
    if valor in ("[PENDIENTE]", "nan", "None"):
        return ""
    return valor


def _parse_fecha(valor) -> date | None:
    """Parsea fechas en formato YYYY-MM-DD o YYYY-MM (día=1)."""
    valor = _normalizar(valor)
    if not valor:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(valor, fmt).date()
        except ValueError:
            continue
    return None


def _parse_int(valor) -> int | None:
    valor = _normalizar(valor)
    if not valor:
        return None
    try:
        return int(float(valor))
    except ValueError:
        return None


def _crear_links(artist: Artist, fila: pd.Series) -> list[ArtistLink]:
    links = []
    for columna, plataforma in COLUMNAS_LINKS.items():
        url = _normalizar(fila.get(columna))
        if not url:
            continue
        es_busqueda = "/results?" in url or "/search?" in url
        links.append(
            ArtistLink(
                artist=artist,
                plataforma=plataforma,
                url=url,
                es_busqueda=es_busqueda,
            )
        )
    return links


def cargar_artistas(
    session: Session,
    csv_path: str = SEED_ARTISTS,
    sobrescribir: bool = False,
) -> dict:
    """Carga artistas desde el CSV semilla.

    Por defecto (`sobrescribir=False`) la BD es la fuente de verdad: solo
    crea los slugs que no existen y NO toca las filas existentes (la BD ya
    tiene estado vivo: imágenes, verificación, actividad, métricas). Con
    `sobrescribir=True` se conserva el comportamiento antiguo de upsert
    (útil solo para reconstruir una BD desde el CSV).
    """
    df = pd.read_csv(csv_path, dtype=str)
    contados = 0
    omitidos = 0

    for _, fila in df.iterrows():
        slug = _normalizar(fila.get("id"))
        if not slug:
            continue

        artista = session.execute(
            select(Artist).where(Artist.slug == slug)
        ).scalar_one_or_none()

        if artista is None:
            artista = Artist(slug=slug)
            session.add(artista)
        elif not sobrescribir:
            omitidos += 1
            continue

        artista.nombre = _normalizar(fila.get("nombre")) or slug
        artista.segmento = _normalizar(fila.get("segmento")) or "Sin confirmar"
        artista.ciudad = _normalizar(fila.get("ciudad")) or "[PENDIENTE]"
        artista.generos = _normalizar(fila.get("generos")) or "[PENDIENTE]"
        artista.estado_registro = _normalizar(fila.get("estado_registro")) or "investigado (web)"
        artista.es_propio = _normalizar(fila.get("es_propio")).lower() in (
            "1", "true", "x", "si", "verdadero",
        )
        artista.estado_activo = _normalizar(fila.get("estado_activo")) or "en_duda"
        artista.metodo_actividad = _normalizar(fila.get("metodo_actividad")) or "sin datos"
        artista.logros = _normalizar(fila.get("logros"))
        artista.bio = _normalizar(fila.get("bio"))
        artista.notas = _normalizar(fila.get("notas"))

        for columna, campo in COLUMNAS_FOLLOWERS.items():
            setattr(artista, campo, _parse_int(fila.get(columna)))

        for columna, campo in COLUMNAS_METRICAS.items():
            setattr(artista, campo, _parse_int(fila.get(columna)))

        for columna in FECHA_COLUMNAS:
            setattr(artista, columna, _parse_fecha(fila.get(columna)))

        # Links: se reconstruyen completos (evita duplicados en re-seeds).
        for link in list(artista.links):
            session.delete(link)
        artista.links = _crear_links(artista, fila)

        contados += 1

    session.commit()
    return {"cargados": contados, "omitidos": omitidos}


def cargar_eventos(session: Session, csv_path: str = SEED_EVENTS) -> int:
    df = pd.read_csv(csv_path, dtype=str)
    contados = 0

    for _, fila in df.iterrows():
        nombre = _normalizar(fila.get("nombre"))
        if not nombre:
            continue
        existe = session.execute(
            select(Event).where(Event.nombre == nombre)
        ).scalar_one_or_none()
        if existe is not None:
            continue

        evento = Event(
            nombre=nombre,
            fecha=_parse_fecha(fila.get("fecha")),
            lugar=_normalizar(fila.get("lugar")),
            ciudad=_normalizar(fila.get("ciudad")),
            artistas=_normalizar(fila.get("artistas")),
            que_demuestra=_normalizar(fila.get("que_demuestra")),
            fuente=_normalizar(fila.get("fuente")),
        )
        session.add(evento)
        contados += 1

    session.commit()
    return contados


def seed(session: Session | None = None, sobrescribir: bool = False) -> dict:
    """Crea las tablas y carga los datos semilla. Devuelve conteos.

    Por defecto solo crea lo que no existe (insert-if-missing); con
    `sobrescribir=True` pisa las filas existentes con los valores del CSV
    (solo para reconstruir una BD desde cero).
    """
    Base.metadata.create_all(engine)
    propia = session or SessionLocal()
    try:
        artistas = cargar_artistas(propia, sobrescribir=sobrescribir)
        eventos = cargar_eventos(propia)
    finally:
        if session is None:
            propia.close()
    return {
        "artistas": artistas["cargados"],
        "eventos": eventos,
        "omitidos": artistas["omitidos"],
    }


if __name__ == "__main__":
    print(seed())
