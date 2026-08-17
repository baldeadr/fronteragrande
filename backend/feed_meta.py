"""Conexión con la Graph API de Meta (Facebook/Instagram).

Fase 3: automatización para artistas que administran su página. El flujo:

1. `GET /api/feed/igfb/login?slug={slug}` → redirige al diálogo de Facebook.
2. `GET /api/feed/igfb/callback?code=...&state={slug}` → canjea el código,
   obtiene el token de la página (larga duración) y lo guarda en el artista.

La app solo guarda el token de la **página** (no expira mientras el usuario
no revoque la app) y el id de la cuenta IG de negocio. Los tokens nunca se
exponen en la API. Requiere credenciales de app en `.env` (`META_APP_ID`,
`META_APP_SECRET`); si no están, la conexión queda desactivada.
"""

import os
import logging
from datetime import date, datetime
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import RedirectResponse

from db.database import SessionLocal
from db.models import Artist
from lib.repository import ArtistRepository

API_VERSION = os.getenv("META_API_VERSION", "v22.0")
APP_ID = os.getenv("META_APP_ID", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")
REDIRECT_URI = os.getenv(
    "META_REDIRECT_URI", "http://127.0.0.1:8000/api/feed/igfb/callback"
)
WEB_URL = os.getenv("WEB_URL", "http://127.0.0.1:3000")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

SCOPES = "pages_show_list,pages_read_engagement,instagram_basic"
GRAF_API = f"https://graph.facebook.com/{API_VERSION}"
AUTH_URL = f"https://www.facebook.com/{API_VERSION}/dialog/oauth"

router = APIRouter(prefix="/api/feed/igfb", tags=["meta"])
logger = logging.getLogger(__name__)


def _fecha_meta(valor: str | None) -> datetime | None:
    """Convierte el formato de fecha de la Graph API (ej. 2026-04-28T02:18:10+0000)."""
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
    except ValueError:
        return None


def meta_configurado() -> bool:
    """True si la app tiene credenciales de Meta en `.env`."""
    return bool(APP_ID and APP_SECRET)


def _get(slug: str) -> Artist:
    session = SessionLocal()
    try:
        artista = ArtistRepository(session).por_slug(slug)
        if artista is None:
            raise HTTPException(status_code=404, detail="Artista no encontrado")
        return artista
    finally:
        session.close()


def _intercambiar_code(code: str) -> str:
    """Canjea el `code` del diálogo por un token de usuario (corta duración)."""
    r = requests.get(
        f"{GRAF_API}/oauth/access_token",
        params={
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
        timeout=20,
    )
    r.raise_for_status()
    datos = r.json()
    if "error" in datos:
        raise RuntimeError(datos["error"].get("message", "Error de Meta"))
    return datos["access_token"]


def _token_larga_duracion(short: str) -> str:
    """Convierte el token de usuario en uno de larga duración (60 días)."""
    r = requests.get(
        f"{GRAF_API}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "fb_exchange_token": short,
        },
        timeout=20,
    )
    r.raise_for_status()
    datos = r.json()
    if "error" in datos:
        raise RuntimeError(datos["error"].get("message", "Error de Meta"))
    return datos["access_token"]


def _pagina_artista(artista: Artist, user_token: str) -> dict:
    """Devuelve la página administrada que coincide con la URL de FB del
    artista (o la primera si no hay coincidencia).

    El flujo OAuth solo puede vincular páginas que administra la cuenta
    autorizada; comparar la URL de FB registrada evita conectar la página
    equivocada cuando la cuenta administra varias.
    """
    r = requests.get(
        f"{GRAF_API}/me/accounts",
        params={
            "access_token": user_token,
            "fields": "id,name,link,access_token,instagram_business_account",
        },
        timeout=20,
    )
    r.raise_for_status()
    datos = r.json()
    paginas = datos.get("data", [])
    if not paginas:
        raise RuntimeError("El usuario no administra ninguna página")

    url_fb = ""
    for link in artista.links:
        if link.plataforma == "fb":
            url_fb = (link.url or "").strip()
            break
    if url_fb:
        base = url_fb.rstrip("/")
        if "profile.php" in base:
            id_fb = base.split("id=")[-1].strip()
            for p in paginas:
                if p.get("id") == id_fb:
                    return p
        else:
            usuario = base.rsplit("/", 1)[-1].lower()
            for p in paginas:
                link_pagina = (p.get("link") or "").rstrip("/").lower()
                nombre_pagina = (p.get("name") or "").strip().casefold()
                nombre_artista = (artista.nombre or "").strip().casefold()
                if (
                    link_pagina.endswith(f"/{usuario}")
                    or nombre_pagina == usuario
                    or nombre_pagina == nombre_artista
                ):
                    return p
        if len(paginas) == 1:
            logger.warning(
                "Meta devolvió una sola página con enlace distinto para %s; "
                "se usará esa página: %s",
                url_fb,
                paginas[0].get("id"),
            )
            return paginas[0]
        raise RuntimeError(
            "La cuenta autorizada no administra la página de Facebook registrada "
            f"para este artista ({url_fb})"
        )
    return paginas[0]


def _grafo(ruta: str, params: dict) -> dict:
    """GET a la Graph API con manejo de errores estándar."""
    r = requests.get(f"{GRAF_API}/{ruta}", params=params, timeout=20)
    r.raise_for_status()
    datos = r.json()
    if "error" in datos:
        raise RuntimeError(datos["error"].get("message", "Error de Meta"))
    return datos


def pagina_about(page_id: str, page_token: str) -> str:
    """Descripción de la página de Facebook (`description`/`about`)."""
    datos = _grafo(
        page_id,
        {"access_token": page_token, "fields": "about,description"},
    )
    descripcion = (datos.get("description") or "").strip()
    if not descripcion:
        descripcion = (datos.get("about") or "").strip()
    return descripcion


def ig_bio(ig_user_id: str, page_token: str) -> str:
    """Bio de la cuenta de Instagram de negocio."""
    datos = _grafo(
        ig_user_id,
        {"access_token": page_token, "fields": "biography"},
    )
    return (datos.get("biography") or "").strip()


@router.get("/login")
def login(slug: str):
    """Inicia el flujo OAuth: redirige al diálogo de Facebook."""
    if not meta_configurado():
        raise HTTPException(
            status_code=503,
            detail="Meta no configurado. Revisa META_APP_ID/META_APP_SECRET en .env",
        )
    _get(slug)
    params = urlencode(
        {
            "client_id": APP_ID,
            "redirect_uri": REDIRECT_URI,
            "state": slug,
            "scope": SCOPES,
        }
    )
    return RedirectResponse(f"{AUTH_URL}?{params}")


@router.post("/desconectar")
def desconectar(slug: str, x_admin_token: str = Header(default="")):
    """Quita la conexión Meta del artista (token y ids).

    Requiere el `X-Admin-Token` (ADMIN_PASSWORD de `.env`): una acción de
    administración no debe poder ejecutarla cualquiera que conozca el slug.
    Permite volver a conectar con otra cuenta o revocar el acceso. No borra
    los posts ya sincronizados del feed.
    """
    if not ADMIN_PASSWORD or x_admin_token != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=403, detail="Acción restringida al administrador"
        )
    session = SessionLocal()
    try:
        artista = ArtistRepository(session).por_slug(slug)
        if artista is None:
            raise HTTPException(status_code=404, detail="Artista no encontrado")
        artista.fb_page_id = None
        artista.fb_page_token = None
        artista.ig_user_id = None
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@router.get("/callback")
def callback(code: str, state: str):
    """Recibe el `code`, guarda el token de la página y redirige al perfil.

    Al conectar, el artista **reclama** el perfil: `estado_registro` pasa a
    `confirmado (artista, YYYY-MM-DD)`, la señal de que la cuenta autorizada
    administra la página registrada del artista.
    """
    session = SessionLocal()
    ok = False
    try:
        artista = ArtistRepository(session).por_slug(state)
        if artista is not None and code:
            corto = _intercambiar_code(code)
            largo = _token_larga_duracion(corto)
            pagina = _pagina_artista(artista, largo)
            artista.fb_page_id = pagina["id"]
            artista.fb_page_token = pagina["access_token"]
            artista.ig_user_id = (
                pagina.get("instagram_business_account") or {}
            ).get("id")
            artista.estado_registro = (
                f"confirmado (artista, {date.today().isoformat()})"
            )
            session.commit()
            ok = True
            _notificar_verificacion(session, artista.nombre)
    except Exception as exc:
        session.rollback()
        logger.exception("Error al conectar Meta para el artista %s: %s", state, exc)
    finally:
        session.close()
    return RedirectResponse(f"{WEB_URL}/artistas/{state}?igfb={'ok' if ok else 'error'}")


def pagina_posts(page_id: str, page_token: str, limite: int = 10) -> list[dict]:
    """Últimos posts de una página de Facebook (normalizados para el feed)."""
    datos = _grafo(
        f"{page_id}/posts",
        {
            "access_token": page_token,
            "fields": "id,message,created_time,permalink_url,full_picture",
            "limit": limite,
        },
    )
    items = []
    for p in datos.get("data", []):
        url = p.get("permalink_url") or ""
        if not url:
            continue
        items.append(
            {
                "url": url,
                "titulo": (p.get("message") or "").strip().splitlines()[0][:200]
                if (p.get("message") or "").strip()
                else "",
                "fecha": _fecha_meta(p.get("created_time")),
                "imagen": p.get("full_picture") or "",
            }
        )
    return items


def ig_media(ig_user_id: str, page_token: str, limite: int = 10) -> list[dict]:
    """Últimos media de una cuenta IG de negocio (normalizados para el feed)."""
    datos = _grafo(
        f"{ig_user_id}/media",
        {
            "access_token": page_token,
            "fields": "id,permalink,caption,timestamp,media_type,thumbnail_url,media_url",
            "limit": limite,
        },
    )
    items = []
    for m in datos.get("data", []):
        url = m.get("permalink") or ""
        if not url:
            continue
        imagen = m.get("thumbnail_url") or ""
        if not imagen and m.get("media_type") == "IMAGE":
            imagen = m.get("media_url") or ""
        caption = (m.get("caption") or "").strip()
        items.append(
            {
                "url": url,
                "titulo": caption.splitlines()[0][:200] if caption else "",
                "fecha": _fecha_meta(m.get("timestamp")),
                "imagen": imagen,
            }
        )
    return items


def _notificar_verificacion(session, nombre_artista: str) -> None:
    """Envía notificación push si hay artista verificado y el toggle está activo."""
    try:
        from lib.notificaciones import notificar_todos
        from lib.repository import PushSubscriptionRepository, SettingsRepository

        if not SettingsRepository(session).obtener_bool("notificar_auto_verificacion"):
            return
        enviadas = notificar_todos(
            PushSubscriptionRepository(session),
            f"{nombre_artista} se verificó",
            "Un nuevo artista se conectó en Frontera Grande.",
            "/",
        )
        session.commit()
        if enviadas:
            print(f"Aviso de verificación enviado a {enviadas} suscriptores")
    except Exception as exc:
        logger.warning("No se pudo notificar verificación: %s", exc)
