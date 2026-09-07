"""Diagnóstico y captura del token de la página Frontera Grande (producción).

El flujo normal (`obtener_token_pagina.py`) guarda el token de la **primera**
página de `/me/accounts` cuando la página FG no aparece, por lo que siempre
cae a Apex Ultra. Este script hace el OAuth completo localmente y:

1. Lista TODAS las páginas de `/me/accounts` (para ver por qué FG no aparece).
2. Si FG (id 1310637315463189) está, toma su token de página y lo sube a la
   BD de producción vía `POST /api/admin/fg-token`.
3. Muestra en pantalla el resultado.

Requiere un redirect URI local registrado en la app de Facebook:
  http://127.0.0.1:9000/callback
Si Facebook lo rechaza, añade esa URL en developers → tu app → Ajustes →
Avanzado → "URI de redireccionamiento de OAuth válidos".
"""

import argparse
import os
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode

import requests

REDIRECT_URI = "http://127.0.0.1:9000/callback"
PORT = 9000
PAGE_ID_FG = os.getenv("FG_PAGE_ID", "1310637315463189")
API_VERSION = os.getenv("META_API_VERSION", "v22.0")
GRAF_API = f"https://graph.facebook.com/{API_VERSION}"
AUTH_URL = f"https://www.facebook.com/{API_VERSION}/dialog/oauth"
SCOPES = (
    "pages_show_list,pages_read_engagement,pages_manage_posts,"
    "instagram_basic,instagram_content_publish"
)


def load_env():
    from pathlib import Path

    env = Path(".env")
    if env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            k, _, v = linea.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def main():
    parser = argparse.ArgumentParser(description="Diagnóstico del OAuth de la página FG")
    parser.add_argument(
        "--api",
        default=os.getenv("API_PUBLIC_URL", "https://fronteragrande-api.onrender.com"),
        help="Base de la API de producción para subir el token",
    )
    parser.add_argument(
        "--no-subir",
        action="store_true",
        help="Solo diagnóstico, no sube el token a la BD",
    )
    args = parser.parse_args()

    load_env()
    app_id = os.getenv("META_APP_ID", "")
    app_secret = os.getenv("META_APP_SECRET", "")
    if not app_id or not app_secret:
        print("Faltan META_APP_ID / META_APP_SECRET en .env", file=os.sys.stderr)
        return

    capturado: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            q = parse_qs(self.path.split("?", 1)[-1])
            if "code" in q:
                capturado["code"] = q["code"][0]
            if "error" in q:
                capturado["error"] = q["error"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            body = (
                f"<h2>Token capturado: {capturado.get('code', capturado.get('error', '?')[:20])}</h2>"
                "<p>Vuelve a la terminal.</p>"
            ).encode("utf-8")
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    serv = HTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=serv.serve_forever, daemon=True).start()

    params = urlencode(
        {
            "client_id": app_id,
            "redirect_uri": REDIRECT_URI,
            "state": "fg",
            "scope": SCOPES,
            "auth_type": "rerequest",
        }
    )
    url = f"{AUTH_URL}?{params}"
    print("=" * 62)
    print("  Diagnóstico OAuth página Frontera Grande")
    print("=" * 62)
    print(f"  App ID       : {app_id}")
    print(f"  Página FG id : {PAGE_ID_FG}")
    print(f"  Redirect     : {REDIRECT_URI}")
    print(f"  API subida   : {args.api}")
    print()
    print("Se abre el navegador. Autoriza como Adrián Balderas y acepta los permisos.")
    print("Si Facebook rechaza el redirect, agrega en developers:")
    print("  Ajustes → Avanzado → 'URI de redireccionamiento de OAuth válidos':")
    print(f"  {REDIRECT_URI}")
    print()
    webbrowser.open(url)
    print("Esperando callback local... (Ctrl+C para cancelar)")
    alterna = 0
    while "code" not in capturado and "error" not in capturado:
        import time

        time.sleep(1)
        alterna += 1
        if alterna == 5:
            print(f"No llegó el callback. Si no se abrió, pega esto:\n  {url}\n")
            alterna = 0
    serv.shutdown()
    if "error" in capturado:
        print("FACEBOOK ERROR:", capturado["error"])
        return
    code = capturado["code"]
    print("\nCode capturado. Intercambiando por token de usuario...")

    r = requests.get(
        f"{GRAF_API}/oauth/access_token",
        params={
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
        timeout=20,
    )
    if not r.ok or "error" in r.json():
        print("Error al intercambiar code:", r.text[:400])
        return
    user_token = r.json()["access_token"]
    print("Token de usuario OK. Leyendo /me/accounts...")

    r = requests.get(
        f"{GRAF_API}/me/accounts",
        params={
            "access_token": user_token,
            "fields": "id,name,access_token",
        },
        timeout=20,
    )
    if not r.ok:
        print("Error /me/accounts:", r.status_code, r.text[:400])
        return
    paginas = r.json().get("data", [])
    print(f"\nPáginas administradas por la cuenta ({len(paginas)}):")
    for p in paginas:
        marca = "  <-- FG" if str(p.get("id")) == str(PAGE_ID_FG) else ""
        print(f"  id={p.get('id')}  nombre={p.get('name')}{marca}")

    # Buscar la página FG por id o por nombre
    fg = None
    objetivo_nombre = "Frontera Grande"
    for p in paginas:
        if str(p.get("id")) == str(PAGE_ID_FG):
            fg = p
            break
    if fg is None:
        for p in paginas:
            if objetivo_nombre.casefold() in (p.get("name") or "").casefold():
                fg = p
                break
    if fg is None:
        print(
            "\n[ERROR] La página FG no aparece en /me/accounts de esta cuenta/token."
            "\nEsto confirma que la app no tiene la página FG vinculada."
            "\nRevisar en developers: app → 'Iniciar sesión con Facebook' → 'Páginas'."
        )
        return

    page_token = fg["access_token"]
    print(f"\nToken de página FG ({fg.get('name')}, id {fg.get('id')}) obtenido.")
    print(f"  (primeros 12 chars): {page_token[:12]}...")

    if args.no_subir:
        print("\n[--no-subir] No se subió el token. Cópialo manualmente si quieres.")
        return

    admin_password = os.getenv("ADMIN_PASSWORD", "")
    if not admin_password:
        print("\n[ERROR] Falta ADMIN_PASSWORD en .env para subir el token vía API.")
        return
    resp = requests.post(
        f"{args.api.rstrip('/')}/api/admin/fg-token",
        json={"token": page_token},
        headers={"X-Admin-Token": admin_password},
        timeout=30,
    )
    print("\nSubiendo token a la BD de producción:", resp.status_code, resp.text[:300])
    if resp.ok:
        print("\n✅ Token de la página FG guardado en producción.")


if __name__ == "__main__":
    main()
