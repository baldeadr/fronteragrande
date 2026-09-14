#!/usr/bin/env python3
"""Prueba el post de bienvenida en la página FG SIN publicarlo.

Sube la tarjeta como foto no publicada (`published=false`) con su caption:
aparece en Meta Business Suite → Contenido → Publicaciones archivadas, donde
se puede ver cómo quedaría y borrar. Nada es visible para el público.

    .venv/bin/python scripts/prueba_promo_meta.py --slug oxte
    .venv/bin/python scripts/prueba_promo_meta.py --slug oxte --variante 2
    .venv/bin/python scripts/prueba_promo_meta.py --publicar   # publica de verdad
    .venv/bin/python scripts/prueba_promo_meta.py --borrar <id>  # borra una prueba

Requiere FG_PAGE_ID y FG_PAGE_TOKEN en .env.
"""

import argparse
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_DIR = Path(__file__).resolve().parent.parent
API_VERSION = "v21.0"
GRAF_API = f"https://graph.facebook.com/{API_VERSION}"


def load_env():
    """Carga variables desde .env de la raíz (fallback manual)."""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        for linea in env_path.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, _, valor = linea.partition("=")
                valor = valor.strip().strip('"').strip("'")
                if valor and valor != "[PENDIENTE]":
                    os.environ.setdefault(clave.strip(), valor)


def main():
    parser = argparse.ArgumentParser(description="Prueba el promo FG en Meta")
    parser.add_argument("--slug", help="Slug del artista (requerido salvo --borrar)")
    parser.add_argument("--variante", default="auto",
                        help="'auto' (por slug) o número 0-3 para forzar")
    parser.add_argument("--publicar", action="store_true",
                        help="Publica de verdad (por defecto: no publicada)")
    parser.add_argument("--borrar", metavar="ID",
                        help="Elimina el post/foto de prueba con ese ID")
    args = parser.parse_args()

    load_env()
    page_id = os.environ.get("FG_PAGE_ID", "")
    token = os.environ.get("FG_PAGE_TOKEN", "")
    if not page_id or not token:
        print("Faltan FG_PAGE_ID o FG_PAGE_TOKEN en .env", file=sys.stderr)
        sys.exit(1)

    if args.borrar:
        r = requests.delete(
            f"{GRAF_API}/{args.borrar}",
            params={"access_token": token},
            timeout=30,
        )
        if r.ok:
            print(f"🗑️  Eliminado: {args.borrar}")
        else:
            print(f"Error al borrar: {r.text}", file=sys.stderr)
        return

    if not args.slug:
        parser.error("se requiere --slug (o --borrar ID)")

    from db.database import SessionLocal
    from lib.promo_fg import (
        _construir_mensaje,
        _error_pagina_fg,
        _obtener_enlaces_artista,
        generar_imagen_promo,
    )
    from lib.repository import ArtistRepository

    error_fg = _error_pagina_fg()
    if error_fg:
        print(f"[error] {error_fg}", file=sys.stderr)
        sys.exit(1)

    variante = None
    if args.variante != "auto":
        variante = int(args.variante)

    session = SessionLocal()
    try:
        artista = ArtistRepository(session).por_slug(args.slug)
        if artista is None:
            print(f"Artista no encontrado: {args.slug}", file=sys.stderr)
            sys.exit(1)
        ruta = generar_imagen_promo(artista, variante)
        mensaje = _construir_mensaje(
            artista, _obtener_enlaces_artista(artista)
        )
    finally:
        session.close()
    if ruta is None:
        print(f"Sin foto de perfil para {artista.nombre}", file=sys.stderr)
        sys.exit(1)
    publicada = bool(args.publicar)

    with open(ruta, "rb") as archivo:
        r = requests.post(
            f"{GRAF_API}/{page_id}/photos",
            data={
                "access_token": token,
                "caption": mensaje,
                "published": "true" if publicada else "false",
            },
            files={"source": (ruta.name, archivo, "image/png")},
            timeout=120,
        )

    if not r.ok:
        print(f"Error de Meta:\n{r.text}", file=sys.stderr)
        sys.exit(1)

    resp = r.json()
    photo_id = resp.get("post_id") or resp.get("id")
    modo = "PUBLICADA" if publicada else "NO PUBLICADA (prueba)"
    print(f"✅ Foto {modo}")
    print(f"   id: {photo_id}")
    print(f"   tarjeta local: {ruta}")
    if publicada:
        print(f"   visible en: https://facebook.com/{photo_id}")
    else:
        print("   revísala en: Meta Business Suite → Contenido → "
              "Publicaciones archivadas")
        print(f"   para borrarla: .venv/bin/python {Path(__file__).name} "
              f"--borrar {photo_id}")


if __name__ == "__main__":
    main()
