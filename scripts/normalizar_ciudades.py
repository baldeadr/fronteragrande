"""Normaliza las ciudades a base única (sin sufijo de estado incrustado).

La región cubre solo Tamaulipas (MX) y el Valle del Río Grande (TX); las
ciudades texanas quedaron en el semilla con el texto ", Texas" incrustado
("Roma, Texas", "Laredo, Texas", …) y otras sin él ("McAllen"), lo que rompe
agrupaciones. Este script pasa todas a la base única; la bandera (🇲🇽/🇺🇸) se
decide en display vía `web/lib/ciudades.ts` (PAIS_CIUDAD), no con una columna.

Idempotente: los valores ya en base no se tocan.

Uso:
    .venv/bin/python scripts/normalizar_ciudades.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from db.models import Artist, Event

# {proviene: base}. Solo apertura para las ciudades texanas del semilla.
CIUDADES_NORMALIZAR: dict[str, str] = {
    "roma, texas": "Roma",
    "laredo, texas": "Laredo",
    "edinburg, texas": "Edinburg",
    "brownsville, texas": "Brownsville",
    "south padre island, texas": "South Padre Island",
}


def _base(nombre: str | None) -> str | None:
    if not nombre:
        return None
    return CIUDADES_NORMALIZAR.get(nombre.strip().lower(), nombre.strip())


def main() -> int:
    session = SessionLocal()
    cambiados = 0
    try:
        for modelo in (Artist, Event):
            for registro in session.query(modelo).all():
                base = _base(getattr(registro, "ciudad", None))
                if base is not None and base != registro.ciudad:
                    print(f"[OK] {modelo.__name__}: '{registro.ciudad}' → '{base}'")
                    registro.ciudad = base
                    cambiados += 1
        session.commit()
    finally:
        session.close()
    print(f"\nCiudades normalizadas: {cambiados}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())