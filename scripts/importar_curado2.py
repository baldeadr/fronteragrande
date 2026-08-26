"""Importa curado2_enriquecido.csv al formato escena_local.csv y lo mergea.

Uso:
    .venv/bin/python scripts/importar_curado2.py [--curado PATH] [--escena PATH]
"""
import argparse
import csv
import re
import unicodedata
from pathlib import Path


def slugificar(nombre: str) -> str:
    nombre = nombre.lower().strip()
    nombre = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    nombre = re.sub(r"[^a-z0-9]+", "_", nombre)
    return nombre.strip("_")


CAT_MAP = {
    "banda": "Banda",
    "solista": "Solista",
    "dj/productor": "DJ",
    "dj": "DJ",
    "colectivo": "Colectivo",
    "covers": "Covers",
    "tributo": "Tributo",
}

URL_MAP = {
    "ig": "url_ig",
    "fb": "url_fb",
    "spotify": "url_spotify",
    "ty": "url_yt",
    "tt": "url_tt",
    "x": "url_x",
    "bandcamp": "url_bandcamp",
    "soundcloud": "url_soundcloud",
}


def main():
    parser = argparse.ArgumentParser(description="Importar curado2 enriquecido a escena_local")
    parser.add_argument("--curado", default="curado2_enriquecido.csv")
    parser.add_argument("--escena", default="data/escena_local.csv")
    args = parser.parse_args()

    with open(args.curado, "r", encoding="utf-8-sig") as f:
        curado_rows = list(csv.DictReader(f))

    with open(args.escena, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        escena_header = reader.fieldnames
        escena_rows = list(reader)

    existing = {r["id"] for r in escena_rows}
    added, skipped = 0, 0

    for row in curado_rows:
        nombre = row["Artista"].strip()
        slug = slugificar(nombre)

        if slug in existing:
            skipped += 1
            continue

        cat_raw = row.get("Categoria", "").strip().lower()
        new_row = {col: "" for col in escena_header}
        new_row["id"] = slug
        new_row["nombre"] = nombre
        new_row["segmento"] = CAT_MAP.get(cat_raw, "Sin confirmar")
        new_row["ciudad"] = row.get("Ciudad", "").strip()
        new_row["generos"] = row.get("generos", "").strip()
        new_row["bio"] = row.get("bio", "").strip()
        new_row["estado_registro"] = "investigado (web)"

        for src, dst in URL_MAP.items():
            val = row.get(src, "").strip()
            if val:
                new_row[dst] = val

        escena_rows.append(new_row)
        existing.add(slug)
        added += 1
        print(f"  + {nombre} ({slug})")

    with open(args.escena, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=escena_header)
        writer.writeheader()
        writer.writerows(escena_rows)

    print(f"\nResultado: {added} nuevos, {skipped} omitidos, {len(escena_rows)} total")


if __name__ == "__main__":
    main()
