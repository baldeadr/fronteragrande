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
import base64
import binascii
import hashlib
import hmac
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Cookie, HTTPException, Header, Body
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

from db.database import SessionLocal
from db.models import Artist
from lib.cache import get_cache, invalidate_public_cache
from lib.repository import ArtistRepository

API_VERSION = os.getenv("META_API_VERSION", "v22.0")
APP_ID = os.getenv("META_APP_ID", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")
REDIRECT_URI = os.getenv(
    "META_REDIRECT_URI", "http://127.0.0.1:8000/api/feed/igfb/callback"
)
WEB_URL = os.getenv("WEB_URL", "http://127.0.0.1:3000")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
OWNER_COOKIE = "fg_meta_owner"
OWNER_COOKIE_MAX_AGE = 60 * 60 * 24 * 30

SCOPES = "pages_show_list,pages_read_engagement,instagram_basic"
# Permiso opcional para eventos: solo se pide de forma incremental cuando
# la app ya tiene aprobación de Meta; pedirlo sin aprobación bloquea a
# usuarios no-admin con "Invalid Scope: pages_events".
SCOPES_EVENTOS = f"{SCOPES},pages_events"
GRAF_API = f"https://graph.facebook.com/{API_VERSION}"
AUTH_URL = f"https://www.facebook.com/{API_VERSION}/dialog/oauth"

router = APIRouter(prefix="/api/feed/igfb", tags=["meta"])
logger = logging.getLogger(__name__)

# Ruta de archivo NO versionado donde se guarda el token permanente de la
# página FG cuando se obtiene vía `fg-login` (para cargarlo como secret).
FG_PAGE_TOKEN_FILE = os.getenv("FG_PAGE_TOKEN_FILE", "data/fg_page_token.txt")


def _owner_secret() -> bytes:
    """Clave estable para firmar las sesiones de propietarios de Meta."""
    return (APP_SECRET or ADMIN_PASSWORD).encode("utf-8")


def _crear_sesion_propietario(slug: str) -> str:
    """Crea un token firmado que vincula la sesión con un artista."""
    payload = f"{slug}:{int(time.time()) + OWNER_COOKIE_MAX_AGE}"
    firma = hmac.new(
        _owner_secret(), payload.encode("utf-8"), hashlib.sha256
    ).digest()
    return (
        base64.urlsafe_b64encode(payload.encode("utf-8")).decode().rstrip("=")
        + "."
        + base64.urlsafe_b64encode(firma).decode().rstrip("=")
    )


def _sesion_autoriza(token: str | None, slug: str) -> bool:
    """Comprueba que una sesión Meta vigente pertenece al perfil indicado."""
    if not token or not _owner_secret() or "." not in token:
        return False
    codificado, firma_codificada = token.split(".", 1)
    try:
        payload = base64.urlsafe_b64decode(codificado + "===").decode("utf-8")
        firma = base64.urlsafe_b64decode(firma_codificada + "===")
        token_slug, expira = payload.rsplit(":", 1)
        if token_slug != slug or int(expira) < int(time.time()):
            return False
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return False
    esperada = hmac.new(
        _owner_secret(), payload.encode("utf-8"), hashlib.sha256
    ).digest()
    return hmac.compare_digest(firma, esperada)


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


def _pagina_por_id(
    user_token: str,
    page_id: str | None,
    preferir_nombre: str | None = None,
) -> dict | None:
    """Devuelve la página administrada por la cuenta.

    Prioridad:
    1. Si `page_id` viene dado, devuelve la página cuyo id coincide (flujo de
       la página FG).
    2. Si `preferir_nombre` viene dado (p. ej. "Frontera Grande"), devuelve la
       página cuyo nombre la contiene (no distingue mayúsculas). Así el flujo
       FG no depende de que `FG_PAGE_ID` sea el Page ID real (a veces es el App
       ID, que no coincide con ninguna página).
    3. En último caso devuelve la primera página que administra la cuenta.
    """
    r = requests.get(
        f"{GRAF_API}/me/accounts",
        params={
            "access_token": user_token,
            "fields": "id,name,access_token",
        },
        timeout=20,
    )
    if not r.ok:
        logger.error("Error /me/accounts: %s %s", r.status_code, r.text[:400])
    r.raise_for_status()
    paginas = r.json().get("data", [])
    if preferir_nombre or page_id:
        logger.info(
            "Páginas administradas (%s): %s",
            len(paginas),
            [(p.get("id"), p.get("name")) for p in paginas],
        )
    if page_id:
        for p in paginas:
            if str(p.get("id")) == str(page_id):
                return p
    if preferir_nombre:
        objetivo = preferir_nombre.casefold()
        for p in paginas:
            if objetivo in (p.get("name") or "").casefold():
                return p
    return paginas[0] if paginas else None


def pagina_about(page_id: str, page_token: str) -> str:
    """Descripción de la página de Facebook.

    La "bio" visible vive en campos distintos según cómo la llenó el
    artista: se prueba `description`, `about`, `general_info` y `bio`.
    """
    datos = _grafo(
        page_id,
        {"access_token": page_token,
         "fields": "description,about,general_info,bio"},
    )
    for campo in ("description", "about", "general_info", "bio"):
        texto = (datos.get(campo) or "").strip()
        if texto:
            return texto
    return ""


def ig_bio(ig_user_id: str, page_token: str) -> str:
    """Bio de la cuenta de Instagram de negocio."""
    datos = _grafo(
        ig_user_id,
        {"access_token": page_token, "fields": "biography"},
    )
    return (datos.get("biography") or "").strip()


def _followers_count(datos: dict) -> int | None:
    """Lee `followers_count` de una respuesta de la Graph API sin inventar ceros."""
    valor = datos.get("followers_count")
    return valor if isinstance(valor, int) else None


def pagina_seguidores(page_id: str, page_token: str) -> int | None:
    """Seguidores de la página de Facebook (`followers_count`)."""
    datos = _grafo(
        page_id,
        {"access_token": page_token, "fields": "followers_count"},
    )
    return _followers_count(datos)


def ig_seguidores(ig_user_id: str, page_token: str) -> int | None:
    """Seguidores de la cuenta de Instagram de negocio (`followers_count`)."""
    datos = _grafo(
        ig_user_id,
        {"access_token": page_token, "fields": "followers_count"},
    )
    return _followers_count(datos)


def pagina_eventos(page_id: str, page_token: str, limite: int = 25) -> list[dict]:
    """Eventos de una página de Facebook (normalizados para el registro).

    Requiere el permiso `pages_events` en el token (permiso opcional: solo
    disponible tras aprobación de Meta; sin él `sync_eventos_meta.py` avisa
    y no falla). Devuelve `{id, nombre, fecha, lugar, descripcion}`; sin
    fecha se omite el evento.
    """
    datos = _grafo(
        f"{page_id}/events",
        {
            "access_token": page_token,
            "fields": "id,name,start_time,place,description",
            "limit": limite,
        },
    )
    items = []
    for e in datos.get("data", []):
        fecha = _fecha_meta(e.get("start_time"))
        if fecha is None:
            continue
        lugar = (e.get("place") or {}).get("name") or ""
        items.append(
            {
                "id": e.get("id", ""),
                "nombre": (e.get("name") or "").strip(),
                "fecha": fecha,
                "lugar": lugar,
                "descripcion": (e.get("description") or "").strip(),
            }
        )
    return items


@router.get("/login")
def login(slug: str, intencion: str = "conectar", con_eventos: bool = False):
    """Inicia el flujo OAuth: redirige al diálogo de Facebook.

    `con_eventos` pide además `pages_events` (solo tras aprobación de Meta);
    por defecto no se pide para no bloquear a usuarios no-admin con
    "Invalid Scope: pages_events".
    """
    if not meta_configurado():
        raise HTTPException(
            status_code=503,
            detail="Meta no configurado. Revisa META_APP_ID/META_APP_SECRET en .env",
        )
    _get(slug)
    if intencion not in ("conectar", "desconectar"):
        raise HTTPException(status_code=400, detail="Intención no válida")
    scope = SCOPES_EVENTOS if con_eventos else SCOPES
    params = urlencode(
        {
            "client_id": APP_ID,
            "redirect_uri": REDIRECT_URI,
            "state": f"{slug}:{intencion}",
            "scope": scope,
        }
    )
    return RedirectResponse(f"{AUTH_URL}?{params}")


@router.get("/fg-login")
def fg_login():
    """Inicia el OAuth para obtener el token permanente de la página FG.

    A diferencia del login de artistas (que guarda el token en la BD del
    artista), este flujo sirve para la **página de la marca** Frontera Grande:
    al autorizar, el callback guarda el token de página (permanente, no
    expira mientras no se revoque la app) en `data/fg_page_token.txt` para
    cargarlo como secret `FG_PAGE_TOKEN` en GitHub Actions.
    """
    if not meta_configurado():
        raise HTTPException(
            status_code=503,
            detail="Meta no configurado. Revisa META_APP_ID/META_APP_SECRET en .env",
        )
    scope = "pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic"
    params = urlencode(
        {
            "client_id": APP_ID,
            "redirect_uri": REDIRECT_URI,
            "state": "fg",
            "scope": scope,
            "auth_type": "rerequest",
        }
    )
    return RedirectResponse(f"{AUTH_URL}?{params}")


class FotoEntrada(BaseModel):
    """Entrada para actualizar foto de perfil (artista verificado)."""
    imagen_perfil: HttpUrl | str
    imagen_origen: str | None = None


class PerfilEntrada(BaseModel):
    """Entrada para editar la ficha del propio artista (verificado).

    El propietario solo puede tocar su información autodescrita: bio, ciudad,
    categoría, géneros, logros y sus enlaces. Campos curados (notas, estado_activo,
    estado_registro, imagen, ranking, métricas) quedan fuera; el nombre tampoco
    puede cambiarse aquí (la identidad la decide el administrador).
    """

    nombre: str | None = None
    ciudad: str | None = None
    categoria: str | None = None
    generos: str | None = None
    bio: str | None = None
    logros: str | None = None
    redes: list[dict] | None = None


def _urls_fb_artista(artista: Artist) -> set[str]:
    """URLs de Facebook (no-búsqueda) registradas del artista, normalizadas."""
    return {
        l.url.rstrip("/").lower()
        for l in artista.links
        if l.plataforma == "fb" and not l.es_busqueda and (l.url or "").strip()
    }


def _validar_redes_verificadas(artista: Artist, redes: list[dict]) -> None:
    """Ata la identidad del perfil a la página Meta que lo verificó.

    Al reemplazar sus URLs, el propietario debe conservar al menos uno de sus
    enlaces de Facebook (la página con la que reclamó el perfil). Evita que un
    perfil verificado cambie su puente hacia el proyecto de otro.
    """
    fb_previas = _urls_fb_artista(artista)
    if not fb_previas:
        return
    fb_nuevas: set[str] = set()
    for red in redes:
        url = (red.get("url") or "").strip()
        if not url:
            continue
        declarada = (red.get("plataforma") or "").strip().lower()
        from lib.plataformas import detectar_plataforma

        plataforma = detectar_plataforma(url) or declarada or "otro"
        if plataforma == "fb":
            fb_nuevas.add(url.rstrip("/").lower())
    if not fb_nuevas:
        raise HTTPException(
            status_code=400,
            detail=(
                "Debes conservar al menos un enlace a tu página de Facebook "
                "(la que usaste para verificar el perfil)"
            ),
        )
    if not fb_previas.intersection(fb_nuevas):
        raise HTTPException(
            status_code=400,
            detail=(
                "El enlace de Facebook que conserves debe ser el de la página "
                "con la que verificaste tu perfil"
            ),
        )


@router.put("/{slug}/photo")
def actualizar_foto_propia(
    slug: str,
    body: FotoEntrada,
    x_meta_owner: str = Header(default="", alias="X-Meta-Owner"),
    meta_owner: str | None = Cookie(default=None, alias=OWNER_COOKIE),
):
    """Actualiza foto de perfil del artista (solo el propietario verificado).

    Requiere la cookie `fg_meta_owner` o el header `X-Meta-Owner` con la
    sesión emitida al conectar Meta (la cookie Lax no viaja en fetch
    cross-origin, por eso la web usa el header).
    """
    if not _sesion_autoriza(x_meta_owner or meta_owner, slug):
        raise HTTPException(
            status_code=403,
            detail="No autorizado: sesión de propietario inválida o expirada",
        )
    session = SessionLocal()
    try:
        artista = ArtistRepository(session).por_slug(slug)
        if artista is None:
            raise HTTPException(status_code=404, detail="Artista no encontrado")
        artista.imagen_perfil = str(body.imagen_perfil)
        artista.imagen_origen = body.imagen_origen or "manual"
        artista.imagen_actualizada = datetime.utcnow()
        session.commit()
        return {"ok": True, "imagen_perfil": artista.imagen_perfil, "imagen_origen": artista.imagen_origen}
    finally:
        session.close()


@router.put("/{slug}/perfil")
def editar_perfil_propio(
    slug: str,
    body: PerfilEntrada,
    x_meta_owner: str = Header(default="", alias="X-Meta-Owner"),
    meta_owner: str | None = Cookie(default=None, alias=OWNER_COOKIE),
):
    """Edita la ficha del propio artista (solo el propietario verificado).

    Reutiliza la lógica de `lib.servicios.editar_artista` (validaciones de
    categoría, géneros y reemplazo de enlaces) pero autorizada por la sesión
    de propietario emitida por Meta, en vez del token de admin. Los campos
    curados (notas, estado_activo, estado_registro, imagen) quedan fuera, y el
    propietario debe conservar su página de Facebook verificada.
    """
    if not _sesion_autoriza(x_meta_owner or meta_owner, slug):
        raise HTTPException(
            status_code=403,
            detail="No autorizado: sesión de propietario inválida o expirada",
        )
    datos = body.model_dump(exclude_unset=True)
    if "nombre" in datos:
        raise HTTPException(
            status_code=403,
            detail=(
                "El nombre no puede cambiarse desde tu perfil; "
                "contacta al administrador"
            ),
        )
    from lib.servicios import editar_artista

    session = SessionLocal()
    try:
        artista = ArtistRepository(session).por_slug(slug)
        if artista is None:
            raise HTTPException(status_code=404, detail="Artista no encontrado")
        if "redes" in datos:
            _validar_redes_verificadas(artista, datos.get("redes") or [])
        try:
            editar_artista(session, slug, datos)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        session.commit()
        invalidate_public_cache(get_cache())
        return {"ok": True, "slug": slug}
    finally:
        session.close()


@router.post("/desconectar")
def desconectar(
    slug: str,
    x_admin_token: str = Header(default=""),
    x_meta_owner: str = Header(default="", alias="X-Meta-Owner"),
    meta_owner: str | None = Cookie(default=None, alias=OWNER_COOKIE),
):
    """Quita la conexión Meta del artista (token y ids).

    Requiere la sesión del propietario emitida por Meta o el `X-Admin-Token`
    como vía administrativa de emergencia. No borra los posts ya sincronizados.
    """
    es_admin = bool(ADMIN_PASSWORD and x_admin_token == ADMIN_PASSWORD)
    sesion_propietario = x_meta_owner or meta_owner
    if not es_admin and not _sesion_autoriza(sesion_propietario, slug):
        raise HTTPException(
            status_code=403,
            detail="Se requiere la sesión del propietario o del administrador",
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
        invalidate_public_cache(get_cache())
        return {"ok": True}
    finally:
        session.close()


def _callback_pagina_fg(code: str):
    """Callback del OAuth de la página FG: guarda el token permanente.

    Canjea el código, obtiene el token de la página (permanente, no expira
    mientras la cuenta no revoque la app) y lo escribe en `FG_PAGE_TOKEN_FILE`
    (por defecto `data/fg_page_token.txt`, NO versionado) para que se cargue
    como secret `FG_PAGE_TOKEN` en GitHub Actions.
    """
    page_id = os.getenv("FG_PAGE_ID", "") or None
    if not code:
        return RedirectResponse(f"{WEB_URL}?fg_token=error")
    try:
        corto = _intercambiar_code(code)
        largo = _token_larga_duracion(corto)
        pagina = _pagina_por_id(largo, page_id, preferir_nombre="Frontera Grande")
        if not pagina:
            logger.error(
                "La cuenta autorizada no administra ninguna página (¿FG_PAGE_ID=%s es admin?)",
                page_id,
            )
            return RedirectResponse(f"{WEB_URL}?fg_token=no_admin")
        token = pagina["access_token"]
        ruta = Path(FG_PAGE_TOKEN_FILE)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(token, encoding="utf-8")
        # Persistir también en la BD (PostgreSQL es persistente; el disco de
        # Render es efímero y se pierde en cada deploy). Clave fg_page_token.
        try:
            from db.database import SessionLocal
            from lib.repository import SettingsRepository

            session = SessionLocal()
            try:
                SettingsRepository(session).guardar("fg_page_token", token)
                session.commit()
            finally:
                session.close()
        except Exception as exc:
            logger.warning("No se pudo persistir fg_page_token en BD: %s", exc)
        logger.info("Token de la página FG %s guardado en %s", pagina.get("id"), ruta)
        return RedirectResponse(f"{WEB_URL}?fg_token=ok")
    except Exception as exc:
        logger.exception("Error al obtener token de la página FG: %s", exc)
        return RedirectResponse(f"{WEB_URL}?fg_token=error")


@router.get("/callback")
def callback(code: str, state: str):
    """Recibe el `code`, guarda el token de la página y redirige a selección de foto.

    Al conectar, el artista **reclama** el perfil: `estado_registro` pasa a
    `confirmado (artista, YYYY-MM-DD)`, la señal de que la cuenta autorizada
    administra la página registrada del artista. Luego redirige a elegir foto.
    """
    partes = state.split(":", 1)
    slug = partes[0]
    intencion = partes[1] if len(partes) == 2 else "conectar"
    if intencion not in ("conectar", "desconectar"):
        return RedirectResponse(f"{WEB_URL}/artistas/{slug}?igfb=error")

    if slug == "fg":
        return _callback_pagina_fg(code)

    session = SessionLocal()
    ok = False
    owner_cookie = None
    try:
        artista = ArtistRepository(session).por_slug(slug)
        if artista is not None and code:
            corto = _intercambiar_code(code)
            largo = _token_larga_duracion(corto)
            pagina = _pagina_artista(artista, largo)
            if intencion == "desconectar":
                artista.fb_page_id = None
                artista.fb_page_token = None
                artista.ig_user_id = None
            else:
                artista.fb_page_id = pagina["id"]
                artista.fb_page_token = pagina["access_token"]
                artista.ig_user_id = (
                    pagina.get("instagram_business_account") or {}
                ).get("id")
                artista.estado_registro = (
                    f"confirmado (artista, {date.today().isoformat()})"
                )
            session.commit()
            invalidate_public_cache(get_cache())
            ok = True
            if intencion == "conectar":
                owner_cookie = _crear_sesion_propietario(slug)
                from lib.notificaciones import notificar_verificacion_artista

                notificar_verificacion_artista(session, artista.nombre)
                from lib.promo_fg import publicar_bienvenida

                promo_resultado = publicar_bienvenida(artista)
                if not promo_resultado.get("ok"):
                    logger.warning("No se pudo publicar bienvenida para %s: %s",
                                   artista.nombre, promo_resultado.get("error"))
    except Exception as exc:
        session.rollback()
        logger.exception("Error al gestionar Meta para el artista %s: %s", slug, exc)
    finally:
        session.close()
    resultado = "desconectado" if intencion == "desconectar" and ok else "ok"
    if intencion == "conectar" and ok and owner_cookie:
        # Redirigir a página de selección de foto con cookie de propietario
        destino = f"{WEB_URL}/artistas/{slug}/seleccionar-foto?igfb=ok&owner={owner_cookie}"
    else:
        destino = f"{WEB_URL}/artistas/{slug}?igfb={resultado if ok else 'error'}"
    if owner_cookie:
        destino += f"&owner={owner_cookie}#meta_owner={owner_cookie}"
    respuesta = RedirectResponse(destino)
    if owner_cookie:
        respuesta.set_cookie(
            OWNER_COOKIE,
            owner_cookie,
            max_age=OWNER_COOKIE_MAX_AGE,
            httponly=True,
            secure=WEB_URL.startswith("https://"),
            samesite="lax",
            path="/",
        )
    return respuesta


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

