#!/usr/bin/env python3
"""Genera la tarjeta promocional con marca FG para un artista.

Envoltorio de `lib.promo_fg.generar_imagen_promo` para pruebas manuales:

    .venv/bin/python scripts/generar_promo_imagen.py --slug oxte

La imagen (1080×1080) se guarda en `instance/promos/{slug}.png`, la misma
que publica el post de bienvenida y sirve `GET /api/promos/{slug}.png`.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal
from lib.promo_fg import generar_imagen_promo, PROMOS_DIR
from lib.repository import ArtistRepository


def main():
    parser = argparse.ArgumentParser(description="Genera tarjeta promocional FG")
    parser.add_argument("--slug", required=True, help="Slug del artista")
    parser.add_argument("--output", help="Ruta de salida opcional")
    parser.add_argument(
        "--variante",
        default="auto",
        help="'auto' (por slug) o número 0-2 para forzar una variante",
    )
    args = parser.parse_args()

    session = SessionLocal()
    try:
        artista = ArtistRepository(session).por_slug(args.slug)
    finally:
        session.close()
    if artista is None:
        print(f"Artista no encontrado: {args.slug}", file=sys.stderr)
        sys.exit(1)

    variante = None
    if args.variante != "auto":
        try:
            variante = int(args.variante)
        except ValueError:
            print("--variante debe ser 'auto' o un número", file=sys.stderr)
            sys.exit(1)

    ruta = generar_imagen_promo(artista, variante)
    if ruta is None:
        print(f"Sin foto de perfil para {artista.nombre}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        destino = Path(args.output)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(ruta.read_bytes())
        ruta = destino

    print(f"✅ Tarjeta generada: {ruta}")


if __name__ == "__main__":
    main()