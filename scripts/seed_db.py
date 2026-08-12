"""Reconstruye la base de datos desde los CSV semilla.

Uso:
    python scripts/seed_db.py

Borrar `instance/local_scene.db` primero si se quiere partir de cero.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.seed import seed  # noqa: E402


if __name__ == "__main__":
    resultado = seed()
    print(
        f"Seed completado: {resultado['artistas']} artistas, "
        f"{resultado['eventos']} eventos."
    )
