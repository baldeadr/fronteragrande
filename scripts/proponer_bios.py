"""Propone y escribe bios y géneros de los artistas desde sus plataformas.

Cadena de fuentes (de más confiable a menos, ver docs):
1. Bandcamp (`scraper/adapters/bandcamp.py`)
2. SoundCloud (`scraper/adapters/soundcloud.py`)
3. YouTube "Acerca de" (`scraper/adapters/youtube.py`)
   (Spotify no expone bio pública; Facebook/Instagram se cubren para artistas
   conectados a Meta en la Fase 2.)

Si la fuente está clara (filtro `es_bio_clara`), la bio se escribe directo en
la BD con nota `Bio de <Plataforma> (YYYY-MM-DD)` en `notas`; los géneros se
proponen desde las etiquetas de Bandcamp y desde el texto de la bio (solo
vocabulario del proyecto). Lo que no supera el filtro o queda ambiguo va al
reporte `data/bios_pendientes.md` para revisión del artista. Al final se
regenera el CSV semilla (la BD es la fuente de verdad operativa).

Uso:
    .venv/bin/python scripts/proponer_bios.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from db.export import exportar
from lib.helpers import es_bio_clara, generos_desde_texto
from lib.repository import ArtistRepository
from scraper.adapters.bandcamp import BandcampError, bandcamp_bio, bandcamp_tags
from scraper.adapters.soundcloud import SoundCloudError, soundcloud_bio
from scraper.adapters.youtube import YouTubeError, youtube_about

REPORTE = str(Path(__file__).resolve().parent.parent / "data" / "bios_pendientes.md")

# Orden de la cadena de fuentes para la bio.
CADENA_BIO = [("bandcamp", "Bandcamp"), ("soundcloud", "SoundCloud"), ("yt", "YouTube")]

NOMBRE_PLATAFORMA = {"bandcamp": "Bandcamp", "soundcloud": "SoundCloud", "yt": "YouTube"}

# Artistas con conflicto de homónimo confirmado por curaduría: la bio de la
# plataforma corresponde a otro proyecto; no autoescribir.
CONFLICTOS_CONOCIDOS = {
    "don_bravo": "bio de YouTube contradictoria con curaduría (Grupo Norteño, Monterrey)",
}


def _enlaces_por_plataforma(artista) -> dict[str, str]:
    return {
        l.plataforma: l.url
        for l in artista.links
        if not l.es_busqueda and l.url
    }


def _agregar_nota(artista, nota: str) -> None:
    """Añade una nota con fuente separada por ' · ' (no duplica si ya existe)."""
    if not artista.notas or nota not in artista.notas:
        artista.notas = (artista.notas + " · " + nota).strip(" · ")


def _buscar_bio(plataforma: str, url: str) -> str:
    if plataforma == "bandcamp":
        return bandcamp_bio(url)
    if plataforma == "soundcloud":
        return soundcloud_bio(url)
    return youtube_about(url)


def main():
    session = SessionLocal()
    pendientes: list[dict] = []
    escritas = 0
    generos_escritos = 0
    hoy = date.today().isoformat()
    try:
        for artista in ArtistRepository(session).todos():
            enlaces = _enlaces_por_plataforma(artista)
            razones = []

            if not artista.bio:
                bio = ""
                origen = ""
                homonimo = "homónim" in (artista.notas or "").lower()
                for plataforma, _nombre in CADENA_BIO:
                    if plataforma not in enlaces:
                        continue
                    try:
                        bio = _buscar_bio(plataforma, enlaces[plataforma])
                    except (BandcampError, SoundCloudError, YouTubeError) as exc:
                        razones.append(f"{NOMBRE_PLATAFORMA[plataforma]}: {exc}")
                        continue
                    if es_bio_clara(bio):
                        origen = plataforma
                        break
                if origen and homonimo:
                    # La fuente puede ser de un homónimo no local: no autoescribir.
                    origen = ""
                    razones.append(
                        "homónimos advertidos en notas (revisar fuente)"
                    )
                if origen and artista.slug in CONFLICTOS_CONOCIDOS:
                    origen = ""
                    razones.append(CONFLICTOS_CONOCIDOS[artista.slug])
                if origen:
                    artista.bio = bio
                    _agregar_nota(
                        artista,
                        f"Bio de {NOMBRE_PLATAFORMA[origen]} ({hoy}).",
                    )
                    escritas += 1
                    print(f"Bio escrita: {artista.nombre} (desde {NOMBRE_PLATAFORMA[origen]})")
                else:
                    disponibles = [p for p, _ in CADENA_BIO if p in enlaces]
                    if not disponibles:
                        razones.append("sin plataformas de bio (solo curaduría)")
                    elif bio:
                        razones.append(
                            "bio no clara en "
                            + ", ".join(NOMBRE_PLATAFORMA[p] for p in disponibles)
                        )
                    else:
                        razones.append(
                            "sin bio recuperable en "
                            + ", ".join(NOMBRE_PLATAFORMA[p] for p in disponibles)
                        )
                    pendientes.append(
                        {"slug": artista.slug, "nombre": artista.nombre,
                         "razon": "; ".join(razones)}
                    )

            if artista.generos == "[PENDIENTE]":
                candidatos: list[str] = []
                origen_genero = ""
                if "bandcamp" in enlaces:
                    try:
                        etiquetas = bandcamp_tags(enlaces["bandcamp"])
                    except BandcampError:
                        etiquetas = []
                    for etiqueta in etiquetas:
                        detectados = generos_desde_texto(etiqueta)
                        for g in detectados:
                            if g not in candidatos:
                                candidatos.append(g)
                    if candidatos:
                        origen_genero = "Bandcamp"
                if not candidatos and artista.bio:
                    candidatos = generos_desde_texto(artista.bio)
                    if candidatos:
                        origen_genero = "la bio"

                if candidatos:
                    artista.generos = ", ".join(candidatos)
                    _agregar_nota(
                        artista,
                        f"Géneros de {origen_genero} ({hoy}).",
                    )
                    generos_escritos += 1
                    print(f"Géneros escritos: {artista.nombre} ({', '.join(candidatos)})")
                else:
                    pendientes.append(
                        {"slug": artista.slug, "nombre": artista.nombre,
                         "razon": "géneros [PENDIENTE] sin fuente clara"}
                    )
        session.commit()
    finally:
        session.close()

    _escribir_reporte(pendientes)
    print(f"\nBios escritas: {escritas} · géneros escritos: {generos_escritos}")
    print(f"Pendientes para revisión: {len(pendientes)} → {REPORTE}")

    if escritas or generos_escritos:
        sesion = SessionLocal()
        try:
            conteos = exportar(sesion)
            print(f"CSV semilla regenerado: {conteos}")
        finally:
            sesion.close()


def _escribir_reporte(pendientes: list[dict]) -> None:
    """Regenera el reporte de bios/géneros que requieren curaduría."""
    lineas = [
        "# Bios y géneros pendientes de revisión",
        "",
        f"Generado el {date.today().isoformat()} por `scripts/proponer_bios.py`.",
        "",
        "Cada fila necesita curaduría con fuente (regla: no inventar datos). "
        "Editar en el panel de admin (`/admin`).",
        "",
        "| Proyecto | Razón |",
        "|----------|-------|",
    ]
    for p in pendientes:
        lineas.append(f"| {p['nombre']} | {p['razon']} |")
    Path(REPORTE).write_text("\n".join(lineas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()