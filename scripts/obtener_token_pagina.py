#!/usr/bin/env python3
"""Obtiene el token permanente de la página FG de Frontera Grande.

El token de la página (página de la marca, no de un artista) no expira
mientras la cuenta no revoque la app. Este script:

1. Abre el flujo OAuth de la página FG en el navegador.
2. Al autorizar, la API guarda el token en `data/fg_page_token.txt` (NO
   versionado).
3. El script lee ese archivo y configura el secret `FG_PAGE_TOKEN`.

Uso:

    .venv/bin/python scripts/obtener_token_pagina.py
    .venv/bin/python scripts/obtener_token_pagina.py --api https://fronteragrande-api.onrender.com
    .venv/bin/python scripts/obtener_token_pagina.py --no-set-secret   # solo imprime el comando

Requisitos:
- API corriendo localmente (`./scripts/dev.sh`) con `META_APP_ID`,
  `META_APP_SECRET` y `FG_PAGE_ID` en `.env` (o pasas `--api` con la API de
  produccion si `META_REDIRECT_URI` apunta alli).
- La app de Facebook debe tener `http://127.0.0.1:8000/api/feed/igfb/callback`
  (o la URI de redireccion correspondiente) en sus "Valid OAuth Redirect URIs".
- `gh` autenticado (para el `--set-secret`).
"""

import argparse
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TOKEN_FILE = Path(os.getenv("FG_PAGE_TOKEN_FILE", BASE_DIR / "data" / "fg_page_token.txt"))


def load_env():
    """Carga variables desde .env de la raiz (fallback manual)."""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        for linea in env_path.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, _, valor = linea.partition("=")
                valor = valor.strip().strip('"').strip("'")
                if valor and valor != "[PENDIENTE]":
                    os.environ.setdefault(clave.strip(), valor)


def login_url(api_base: str) -> str:
    """URL del endpoint que inicia el OAuth de la pagina FG."""
    return f"{api_base.rstrip('/')}/api/feed/igfb/fg-login"


def main():
    parser = argparse.ArgumentParser(description="Obtiene el token permanente de la pagina FG")
    parser.add_argument(
        "--api",
        default=os.getenv("API_PUBLIC_URL", "http://127.0.0.1:8000"),
        help="Base de la API (local por defecto). Si usas produccion, que META_REDIRECT_URI apunte alli.",
    )
    parser.add_argument(
        "--no-set-secret",
        action="store_true",
        help="No ejecuta gh secret set; solo imprime el comando",
    )
    args = parser.parse_args()

    load_env()

    page_id = os.environ.get("FG_PAGE_ID", "")
    if not page_id:
        print("Falta FG_PAGE_ID en .env", file=sys.stderr)
        sys.exit(1)

    url = login_url(args.api)
    print("=" * 62)
    print("  Obten el token permanente de la pagina FG de Frontera Grande")
    print("=" * 62)
    print(f"  Pagina FG  : {page_id}")
    print(f"  API        : {args.api}")
    print(f"  Archivo    : {TOKEN_FILE}")
    print()
    print("1) Se abre el navegador. Autoriza con la cuenta que ADMINISTRA la")
    print(f"   pagina numero {page_id} (la de Frontera Grande).")
    print("2) Si todo va bien, al final la URL muestra `?fg_token=ok`.")
    print()
    print("Abriendo el navegador...")
    webbrowser.open(url)
    print(f"  Si no se abrio, pega esto en el navegador:\n  {url}\n")

    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
    print("Esperando autorizacion... (presiona Ctrl+C para cancelar)")
    deadline = time.time() + 300
    while not TOKEN_FILE.exists() and time.time() < deadline:
        time.sleep(2)
    if not TOKEN_FILE.exists():
        print("\nTiempo de espera agotado (5 min). Vuelve a intentarlo.", file=sys.stderr)
        sys.exit(1)

    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    print("\nToken obtenido correctamente.")
    print(f"  (primeros 12 chars): {token[:12]}...")
    cmd = ['gh', 'secret', 'set', 'FG_PAGE_TOKEN', '--body', token]
    print(f"Comando a ejecutar:\n  {' '.join(c[:-1])} <token-oculto>")
    if args.no_set_secret:
        print("\n[--no-set-secret] No se ejecuto. Copia el comando anterior.")
    else:
        print("Configurando el secret FG_PAGE_TOKEN en GitHub Actions...")
        resp = subprocess.run(cmd, capture_output=True, text=True)
        if resp.returncode == 0:
            print("  OK: FG_PAGE_TOKEN guardado.")
        else:
            print("  ERROR al ejecutar gh:", resp.stderr.strip(), file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()