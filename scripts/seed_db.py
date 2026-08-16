"""Reconstruye la base de datos desde los CSV semilla.

Uso:
    python scripts/seed_db.py            # insert-if-missing (no pisa la BD)
    python scripts/seed_db.py --reescribir   # pisa filas existentes (reconstruir)

La BD es la fuente de verdad operativa: por defecto el seed solo crea los
slugs que faltan y NO toca las filas existentes. `--reescribir` es solo para
reconstruir una BD desde cero. Borrar `instance/local_scene.db` si se quiere
partir de cero.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.seed import seed  # noqa: E402


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reescribir",
        action="store_true",
        help="pisa las filas existentes con los valores del CSV (reconstrucción)",
    )
    args = parser.parse_args()

    resultado = seed(sobrescribir=args.reescribir)
    print(
        f"Seed completado: {resultado['artistas']} artistas, "
        f"{resultado['eventos']} eventos."
    )
    if resultado["omitidos"]:
        print(
            f"  {resultado['omitidos']} artistas ya existían (se omitieron, "
            "la BD no se pisa)."
        )