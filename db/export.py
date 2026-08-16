"""Exportación de la base de datos a los CSV semilla.

Invierte el flujo del seed: lee la BD (que es la fuente de verdad operativa)
y regenera `data/escena_local.csv` y `data/eventos.csv` con el mismo esquema
que `db/seed.py` entiende, para que el round-trip export → seed sea limpio.

No exporta estado que vive solo en la BD: tokens de Meta, feed, chequeos,
snapshots ni imágenes.
"""

import csv
from pathlib import Path

from sqlalchemy.orm import Session

from db.models import Artist, Event

_RAIZ = Path(__file__).resolve().parent.parent

EXPORT_ARTISTAS = str(_RAIZ / "data/escena_local.csv")
EXPORT_EVENTOS = str(_RAIZ / "data/eventos.csv")

COLUMNAS_ARTISTA = [
    "id",
    "nombre",
    "segmento",
    "ciudad",
    "generos",
    "estado_registro",
    "url_ig",
    "url_fb",
    "url_yt",
    "url_tt",
    "url_spotify",
    "url_bandcamp",
    "url_soundcloud",
    "url_beatport",
    "url_mixcloud",
    "url_apple",
    "url_linktree",
    "followers_ig",
    "bio",
    "followers_fb",
    "followers_yt",
    "followers_tt",
    "followers_spotify",
    "followers_beatport",
    "followers_mixcloud",
    "fecha_captura",
    "ultimo_lanzamiento",
    "ultimo_evento",
    "estado_activo",
    "metodo_actividad",
    "logros",
    "notas",
    "fecha_registro",
    "url_x",
    "vistas_yt",
    "vistas_tt",
    "reproducciones_spotify",
    "reproducciones_bandcamp",
    "reproducciones_soundcloud",
    "es_propio",
]

COLUMNAS_EVENTO = [
    "nombre",
    "fecha",
    "lugar",
    "ciudad",
    "artistas",
    "que_demuestra",
    "fuente",
]

LINK_A_COLUMNA = {
    "ig": "url_ig",
    "fb": "url_fb",
    "yt": "url_yt",
    "tt": "url_tt",
    "spotify": "url_spotify",
    "bandcamp": "url_bandcamp",
    "soundcloud": "url_soundcloud",
    "beatport": "url_beatport",
    "mixcloud": "url_mixcloud",
    "apple": "url_apple",
    "linktree": "url_linktree",
    "x": "url_x",
}


def _fecha(valor) -> str:
    return valor.isoformat() if valor else ""


def _int(valor) -> str:
    return str(valor) if valor is not None else ""


def _links_artista(artista: Artist) -> dict[str, str]:
    urls = {col: "" for col in LINK_A_COLUMNA.values()}
    for link in artista.links:
        columna = LINK_A_COLUMNA.get(link.plataforma)
        if columna:
            urls[columna] = link.url or ""
    return urls


def _fila_artista(artista: Artist) -> dict[str, str]:
    links = _links_artista(artista)
    return {
        "id": artista.slug,
        "nombre": artista.nombre,
        "segmento": artista.segmento,
        "ciudad": artista.ciudad,
        "generos": artista.generos,
        "estado_registro": artista.estado_registro,
        "url_ig": links["url_ig"],
        "url_fb": links["url_fb"],
        "url_yt": links["url_yt"],
        "url_tt": links["url_tt"],
        "url_spotify": links["url_spotify"],
        "url_bandcamp": links["url_bandcamp"],
        "url_soundcloud": links["url_soundcloud"],
        "url_beatport": links["url_beatport"],
        "url_mixcloud": links["url_mixcloud"],
        "url_apple": links["url_apple"],
        "url_linktree": links["url_linktree"],
        "followers_ig": _int(artista.followers_ig),
        "bio": artista.bio or "",
        "followers_fb": _int(artista.followers_fb),
        "followers_yt": _int(artista.followers_yt),
        "followers_tt": _int(artista.followers_tt),
        "followers_spotify": _int(artista.followers_spotify),
        "followers_beatport": _int(artista.followers_beatport),
        "followers_mixcloud": _int(artista.followers_mixcloud),
        "fecha_captura": _fecha(artista.fecha_captura),
        "ultimo_lanzamiento": _fecha(artista.ultimo_lanzamiento),
        "ultimo_evento": _fecha(artista.ultimo_evento),
        "estado_activo": artista.estado_activo,
        "metodo_actividad": artista.metodo_actividad,
        "logros": artista.logros or "",
        "notas": artista.notas or "",
        "fecha_registro": _fecha(artista.fecha_registro),
        "url_x": links["url_x"],
        "vistas_yt": _int(artista.vistas_yt),
        "vistas_tt": _int(artista.vistas_tt),
        "reproducciones_spotify": _int(artista.reproducciones_spotify),
        "reproducciones_bandcamp": _int(artista.reproducciones_bandcamp),
        "reproducciones_soundcloud": _int(artista.reproducciones_soundcloud),
        "es_propio": "TRUE" if artista.es_propio else "",
    }


def _fila_evento(evento: Event) -> dict[str, str]:
    return {
        "nombre": evento.nombre,
        "fecha": _fecha(evento.fecha),
        "lugar": evento.lugar or "",
        "ciudad": evento.ciudad or "",
        "artistas": evento.artistas or "",
        "que_demuestra": evento.que_demuestra or "",
        "fuente": evento.fuente or "",
    }


def _respaldo(ruta: str) -> None:
    """Copia el CSV previo a `*.bak` antes de sobrescribirlo."""
    origen = Path(ruta)
    if origen.exists():
        destino = origen.with_suffix(".bak")
        if destino.exists():
            destino.unlink()
        origen.replace(destino)


def exportar_artistas(
    session: Session,
    csv_path: str = EXPORT_ARTISTAS,
    respaldo: bool = True,
) -> int:
    from lib.repository import ArtistRepository

    if respaldo:
        _respaldo(csv_path)
    artistas = ArtistRepository(session).todos()
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=COLUMNAS_ARTISTA,
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        writer.writeheader()
        for artista in artistas:
            writer.writerow(_fila_artista(artista))
    return len(artistas)


def exportar_eventos(
    session: Session,
    csv_path: str = EXPORT_EVENTOS,
    respaldo: bool = True,
) -> int:
    from lib.repository import EventRepository

    if respaldo:
        _respaldo(csv_path)
    eventos = EventRepository(session).todos_fecha_asc()
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNAS_EVENTO, lineterminator="\n")
        writer.writeheader()
        for evento in eventos:
            writer.writerow(_fila_evento(evento))
    return len(eventos)


def exportar(session: Session, respaldo: bool = True) -> dict:
    """Regenera ambos CSV desde la BD. Devuelve conteos."""
    artistas = exportar_artistas(session, respaldo=respaldo)
    eventos = exportar_eventos(session, respaldo=respaldo)
    return {"artistas": artistas, "eventos": eventos}