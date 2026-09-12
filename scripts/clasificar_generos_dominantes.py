"""Clasifica el `genero_dominante` de los artistas a partir de sus subgéneros.

Lee todos los artistas de la BD, calcula su género dominante con
`lib.helpers.clasificar_genero_dominante` y lo escribe en la columna
`genero_dominante`. Imprime un reporte de cuántos artistas quedan por género
y cuáles quedaron sin clasificar (su cadena de géneros no matcheó ningún
subgénero del diccionario).

Uso:
    .venv/bin/python scripts/clasificar_generos_dominantes.py
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.helpers import GENEROS_DOMINANTES, clasificar_genero_dominante
from lib.repository import ArtistRepository


def main() -> None:
    session = SessionLocal()
    repo = ArtistRepository(session)
    artistas = repo.todos(con_links=False)

    conteo: Counter = Counter()
    sin_clasificar: list[tuple[str, str]] = []

    for artista in artistas:
        nuevo = (
            artista.genero_dominante_manual
            or clasificar_genero_dominante(artista.slug, artista.generos)
        )
        if nuevo:
            conteo[nuevo] += 1
        else:
            sin_clasificar.append((artista.slug, artista.generos))
        artista.genero_dominante = nuevo

    session.commit()

    print("=== Géneros dominantes ===")
    total = sum(conteo.values())
    for genero in GENEROS_DOMINANTES:
        n = conteo.get(genero, 0)
        print(f"  {genero:<20} {n}")
    print(f"  {'TOTAL':<20} {total}")

    if sin_clasificar:
        print(f"\n=== Sin clasificar ({len(sin_clasificar)}) ===")
        for slug, generos in sorted(sin_clasificar):
            print(f"  {slug}: {generos}")
    else:
        print("\nTodos los artistas con géneros quedaron clasificados.")

    session.close()


if __name__ == "__main__":
    main()
