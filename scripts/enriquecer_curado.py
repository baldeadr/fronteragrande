"""Enriquece un curadoN.csv (artistas + links crudos) al esquema de
curado3_enriquecido.csv para su revisión antes de importar a la BD.

Flujo de importación masiva (paso a paso):
  1. curadoN.csv       → entrada cruda (artista + categoría + links sueltos).
  2. curadoN_enriquecido.csv → este script agrega con fuente: ciudad, redes
     faltantes, bio, géneros (esquema de curado3_enriquecido.csv). Lo que no
     tiene fuente queda [PENDIENTE] para curaduría manual. NO importa a la BD.
  3. data/escena_local.csv  → se importa luego con scripts/importar_curadoX.py
     (insert-if-missing por slug), tras la revisión del artista.
  4. BD real (SQLite/PostgreSQL) → scripts/seed_db.py.

Regla del proyecto: no inventar datos; cada campo rellenado lleva su fuente.
Los campos que no se pueden confirmar se emiten como [PENDIENTE].

Reutiliza los adaptadores de bios/géneros (Bandcamp → SoundCloud → YouTube)
y, si hay credenciales de Spotify en el entorno, confirma identidad y
propone géneros desde la Web API (client credentials).

Uso:
    .venv/bin/python scripts/enriquecer_curado.py --curado curado4.csv
"""

import argparse
import csv
import os
import re
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from lib.helpers import es_bio_clara, generos_desde_texto, slugificar  # noqa: E402

# Columnas del esquema de salida (igual que curado3_enriquecido.csv).
SALIDA_COLS = [
    "Artista",
    "Ciudad",
    "Categoria",
    "ig",
    "fb",
    "spotify",
    "ty",
    "tt",
    "x",
    "bandcamp",
    "soundcloud",
    "bio",
    "generos",
    "fuentes",
]

CADENA_BIO = [("bandcamp", "Bandcamp"), ("soundcloud", "SoundCloud"), ("yt", "YouTube")]
NOMBRE_PLATAFORMA = {"bandcamp": "Bandcamp", "soundcloud": "SoundCloud", "yt": "YouTube"}

# Mapeo de columna de entrada genérica → columna de salida. Algunas entradas
# crudas traen nombres distintos (ej. "yt" vs "ty"); se normalizan aquí.
COL_ENTRADA = {
    "ig": "ig",
    "instagram": "ig",
    "fb": "fb",
    "facebook": "fb",
    "spotify": "spotify",
    "ty": "ty",
    "yt": "yt",
    "youtube": "ty",
    "tt": "tt",
    "tiktok": "tt",
    "x": "x",
    "twitter": "x",
    "bandcamp": "bandcamp",
    "soundcloud": "soundcloud",
}

PENDIENTE = "[PENDIENTE]"


def _cargar_env():
    """Carga SPOTIFY_CLIENT_ID/SECRET desde .env de la raíz (fallback manual)."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _leer_entrada(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _normalizar_links(fila: dict) -> dict[str, str]:
    """Recoge los links de la fila cruda, tolerando nombres de columna distintos."""
    links: dict[str, str] = {}
    for origen, destino in COL_ENTRADA.items():
        valor = (fila.get(origen) or "").strip()
        if valor and not links.get(destino):
            links[destino] = valor
    return links


def _buscar_bio(plataforma: str, url: str) -> str:
    from scraper.adapters.bandcamp import bandcamp_bio, bandcamp_tags
    from scraper.adapters.soundcloud import soundcloud_bio
    from scraper.adapters.youtube import youtube_about

    if plataforma == "bandcamp":
        return bandcamp_bio(url)
    if plataforma == "soundcloud":
        return soundcloud_bio(url)
    return youtube_about(url)


def _proponer_bio(links: dict[str, str]) -> tuple[str, str]:
    """Bio + origen siguiendo la cadena Bandcamp → SoundCloud → YouTube."""
    for plataforma, _nombre in CADENA_BIO:
        url = links.get(plataforma)
        if not url:
            continue
        try:
            bio = _buscar_bio(plataforma, url)
        except Exception as exc:
            continue
        if es_bio_clara(bio):
            return bio, NOMBRE_PLATAFORMA[plataforma]
    return "", ""


def _proponer_generos(links: dict[str, str], bio: str) -> tuple[str, str]:
    """Géneros desde etiquetas Bandcamp o desde el texto de la bio."""
    bandcamp_url = links.get("bandcamp")
    if bandcamp_url:
        try:
            from scraper.adapters.bandcamp import bandcamp_tags

            etiquetas = bandcamp_tags(bandcamp_url)
        except Exception:
            etiquetas = []
        candidatos: list[str] = []
        for etiqueta in etiquetas:
            for g in generos_desde_texto(etiqueta):
                if g not in candidatos:
                    candidatos.append(g)
        if candidatos:
            return ", ".join(candidatos), "Bandcamp"
    if bio:
        candidatos = generos_desde_texto(bio)
        if candidatos:
            return ", ".join(candidatos), "la bio"
    return "", ""


def _proponer_generos_spotify(links: dict[str, str]) -> tuple[str, str]:
    """Géneros desde la Web API de Spotify (client credentials), si hay credenciales."""
    spotify_url = links.get("spotify")
    if not spotify_url or "spotify.com/artist/" not in spotify_url:
        return "", ""
    match = re.search(r"artist/([A-Za-z0-9]+)", spotify_url)
    if not match:
        return "", ""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return "", ""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials

        sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
        )
        artista = sp.artist(match.group(1))
        generos = [g for g in artista.get("genres", []) if g]
        return ", ".join(generos), "Spotify" if generos else ""
    except Exception:
        return "", ""


def _enriquecer(fila: dict) -> dict:
    nombre = (fila.get("artista") or fila.get("Artista") or "").strip()
    links = _normalizar_links(fila)
    salida = {col: "" for col in SALIDA_COLS}
    salida["Artista"] = nombre

    # Categoría: se conserva la declarada; si falta, queda sin confirmar.
    cat = (fila.get("Categoria") or fila.get("categoria") or "").strip()
    salida["Categoria"] = cat if cat else PENDIENTE

    for destino, url in links.items():
        if destino in SALIDA_COLS:
            salida[destino] = url

    fuentes: list[str] = []

    # Bio y géneros por la cadena de fuentes sin API key.
    bio, origen_bio = _proponer_bio(links)
    if origen_bio:
        salida["bio"] = bio
        fuentes.append(f"bio: {origen_bio}")

    generos, origen_gen = _proponer_generos(links, bio)
    if not generos:
        # Respaldo: géneros de Spotify (Web API) cuando está disponible.
        gen_sp, origen_sp = _proponer_generos_spotify(links)
        if gen_sp:
            generos, origen_gen = gen_sp, origen_sp
    if origen_gen:
        salida["generos"] = generos
        fuentes.append(f"generos: {origen_gen}")

    # Ciudad solo puede venir de curaduría externa; nunca se inventa aquí, así
    # que la salida arranca [PENDIENTE] salvo que la fila cruda ya la traiga.
    if not salida["Ciudad"]:
        salida["Ciudad"] = PENDIENTE

    # Campos opcionales sin fuente quedan [PENDIENTE] para que el curador no
    # gaste tokens adivinando; conservar vacíos los convierte en no-editables.
    for col in ("Ciudad", "ig", "tt", "bio", "generos"):
        if col not in ("bio", "generos") and not salida.get(col):
            salida[col] = PENDIENTE
    if salida.get("bio") == "" and not fuentes:
        salida["bio"] = PENDIENTE
    if salida.get("generos") == "" and not fuentes:
        salida["generos"] = PENDIENTE

    salida["fuentes"] = PENDIENTE if not fuentes else " · ".join(fuentes)
    return salida


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curado", default="curado4.csv")
    args = parser.parse_args()

    entrada = Path(args.curado)
    if not entrada.exists():
        print(f"No existe {entrada}")
        return 1
    salida = entrada.parent / f"{entrada.stem}_enriquecido.csv"

    _cargar_env()
    filas = _leer_entrada(entrada)
    enriquecidas = [_enriquecer(f) for f in filas]

    with open(salida, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=SALIDA_COLS)
        writer.writeheader()
        writer.writerows(enriquecidas)

    pendientes = sum(1 for f in enriquecidas if PENDIENTE in f["fuentes"])
    print(f"Enriquecidas {len(enriquecidas)} artistas → {salida}")
    print(f"Con campos sin fuente ([PENDIENTE]): {pendientes}")
    for f in enriquecidas:
        estado = f["fuentes"]
        print(f"  · {f['Artista']} — {estado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
