"""Importa curado4_enriquecido.csv al formato escena_local.csv y lo mergea.

Reutiliza la misma lógica que importar_curado3.py (mapeo de categorías y de
URLs por slug insert-if-missing). La columna extra "fuentes" del curado
enriquecido se ignora (sirvió para la revisión manual).

Uso:
    .venv/bin/python scripts/importar_curado4.py [--curado PATH] [--escena PATH]
"""
import argparse
import csv
import re
import unicodedata


def slugificar(nombre: str) -> str:
    nombre = unicodedata.normalize("NFKD", nombre.lower()).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", nombre).strip("_")


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
    parser = argparse.ArgumentParser(description="Importar curado4 enriquecido a escena_local")
    parser.add_argument("--curado", default="curado4_enriquecido.csv")
    parser.add_argument("--escena", default="data/escena_local.csv")
    args = parser.parse_args()

    with open(args.curado, "r", encoding="utf-8-sig") as f:
        curado_rows = list(csv.DictReader(f))

    with open(args.escena, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        escena_header = list(reader.fieldnames)
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
            if val and val != "[PENDIENTE]":
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
