"""Conexión con la API de TikTok (Business API) para artistas que administran su cuenta.

Fase C del plan TikTok (ver `docs/tiktok.md`): OAuth del creador +
`user.info.basic` (seguidores → `followers_tt`) y `video.list` (videos
recientes → feed, fuente `tt`). Flujo:

1. `GET /api/feed/tiktok/login?slug={slug}` → redirige a la autorización de TikTok.
2. `GET /api/feed/tiktok/callback?code=...&state={slug}` → canjea el código por
   access + refresh token y lo guarda en el artista.

Solo se guardan el `open_id` (`tt_user_id`) y el `tt_refresh_token`; el access
token (24 h) se obtiene al sincronizar y el refresh token se **rota** en cada
uso (TikTok lo regenera). Los tokens nunca se exponen en la API. Requiere
`TIKTOK_CLIENT_KEY`/`TIKTOK_CLIENT_SECRET` en `.env`; sin ellas la conexión
queda desactivada.

Nota: `video.list` requiere aprobación manual de TikTok; `user.info.basic` es
estándar. Hasta que `video.list` esté aprobado (añadirlo a `TIKTOK_SCOPES`),
el sync registra solo seguidores y el feed llega por cross-post a FB/IG/YT.
"""

import base64
import hashlib
import os
import logging
import secrets
from datetime import date, datetime
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import RedirectResponse

from db.database import SessionLocal
from db.models import Artist
from lib.repository import ArtistRepository

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv(
    "TIKTOK_REDIRECT_URI", "http://127.0.0.1:8000/api/feed/tiktok/callback"
)
WEB_URL = os.getenv("WEB_URL", "http://127.0.0.1:3000")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SCOPES = os.getenv("TIKTOK_SCOPES", "user.info.basic")

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
API_URL = "https://open.tiktokapis.com/v2"

router = APIRouter(prefix="/api/feed/tiktok", tags=["tiktok"])
logger = logging.getLogger(__name__)


def tiktok_configurado() -> bool:
    """True si la app tiene credenciales de TikTok en `.env`."""
    return bool(CLIENT_KEY and CLIENT_SECRET)


def _nuevo_verifier() -> str:
    """Verificador aleatorio para PKCE (secreto efímero de un solo uso)."""
    return secrets.token_urlsafe(64)


def _code_challenge(verifier: str) -> str:
    """`code_challenge` (SHA-256) para el parámetro S256 de PKCE."""
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _encode_state(slug: str, verifier: str) -> str:
    """Empaqueta slug + verifier en el `state` para recuperarlos en el callback."""
    payload = f"{slug}\x1f{verifier}"
    return base64.urlsafe_b64encode(payload.encode("utf-8")).rstrip(b"=").decode("ascii")


def _decode_state(state: str) -> tuple[str, str]:
    """Recupera (slug, verifier) del `state`. Sin verifier si no aplica."""
    try:
        padded = state + "=" * (-len(state) % 4)
        payload = base64.urlsafe_b64decode(padded).decode("utf-8")
        slug, _, verifier = payload.partition("\x1f")
        return slug, verifier
    except Exception:
        return state, ""


def _get(slug: str) -> Artist:
    session = SessionLocal()
    try:
        artista = ArtistRepository(session).por_slug(slug)
        if artista is None:
            raise HTTPException(status_code=404, detail="Artista no encontrado")
        return artista
    finally:
        session.close()


def _post_token(params: dict) -> dict:
    """POST al endpoint de tokens (form-urlencoded)."""
    respuesta = requests.post(
        TOKEN_URL,
        data={**params, "client_key": CLIENT_KEY, "client_secret": CLIENT_SECRET},
        timeout=20,
    )
    datos = respuesta.json()
    if "error" in datos or not datos.get("access_token"):
        mensaje = datos.get("error_description") or datos.get("error") or "Error de TikTok"
        raise RuntimeError(mensaje)
    return datos


@router.get("/login")
def login(slug: str):
    """Inicia el flujo OAuth: redirige a la autorización de TikTok."""
    if not tiktok_configurado():
        raise HTTPException(
            status_code=503,
            detail="TikTok no configurado. Revisa TIKTOK_CLIENT_KEY/TIKTOK_CLIENT_SECRET en .env",
        )
    _get(slug)
    verifier = _nuevo_verifier()
    params = urlencode(
        {
            "client_key": CLIENT_KEY,
            "scope": SCOPES,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "state": _encode_state(slug, verifier),
            "code_challenge": _code_challenge(verifier),
            "code_challenge_method": "S256",
        }
    )
    return RedirectResponse(f"{AUTH_URL}?{params}")


@router.get("/callback")
def callback(code: str, state: str):
    """Recibe el `code`, guarda el refresh token y redirige al perfil.

    Al conectar, el artista **reclama** el perfil: `estado_registro` pasa a
    `confirmado (artista, YYYY-MM-DD)`.
    """
    session = SessionLocal()
    ok = False
    try:
        slug, verifier = _decode_state(state)
        artista = ArtistRepository(session).por_slug(slug)
        if artista is not None and code:
            datos = _post_token(
                {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "code_verifier": verifier,
                }
            )
            artista.tt_user_id = datos.get("open_id") or None
            artista.tt_refresh_token = datos.get("refresh_token") or None
            artista.estado_registro = (
                f"confirmado (artista, {date.today().isoformat()})"
            )
            session.commit()
            ok = bool(artista.tt_refresh_token)
    except Exception as exc:
        session.rollback()
        logger.exception("Error al conectar TikTok para el artista %s: %s", slug, exc)
    finally:
        session.close()
    return RedirectResponse(f"{WEB_URL}/artistas/{slug}?tiktok={'ok' if ok else 'error'}")


@router.post("/desconectar")
def desconectar(slug: str, x_admin_token: str = Header(default="")):
    """Quita la conexión TikTok del artista (refresh token e id).

    Requiere el `X-Admin-Token` (ADMIN_PASSWORD de `.env`). No borra los
    videos ya sincronizados del feed.
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
        artista.tt_user_id = None
        artista.tt_refresh_token = None
        session.commit()
        return {"ok": True}
    finally:
        session.close()


def _api(ruta: str, method: str, access_token: str, params: dict = None, body: dict = None) -> dict:
    """Llamada a la API de TikTok con manejo de errores estándar."""
    url = f"{API_URL}/{ruta}"
    headers = {"Authorization": f"Bearer {access_token}"}
    if method == "GET":
        respuesta = requests.get(url, params=params, headers=headers, timeout=20)
    else:
        respuesta = requests.post(
            url, params=params, headers=headers, json=body or {}, timeout=20
        )
    respuesta.raise_for_status()
    datos = respuesta.json()
    codigo = (datos.get("error", {}) or {}).get("code") or ""
    if codigo and codigo != "ok":
        raise RuntimeError(
            datos["error"].get("message") or f"Error de TikTok: {codigo}"
        )
    return datos


def refrescar(refresh_token: str) -> dict:
    """Obtiene un access token nuevo y rota el refresh token.

    Devuelve `{access_token, refresh_token, open_id}`. TikTok entrega un
    refresh token nuevo (de un solo uso) en cada respuesta.
    """
    datos = _post_token(
        {"grant_type": "refresh_token", "refresh_token": refresh_token}
    )
    return {
        "access_token": datos["access_token"],
        "refresh_token": datos.get("refresh_token") or refresh_token,
        "open_id": datos.get("open_id") or "",
    }


def user_info(access_token: str) -> dict:
    """Datos públicos del usuario autorizado (nombre, avatar, seguidores).

    En modo desarrollo/sandbox TikTok entrega `open_id`/`display_name`/
    `avatar_url`, pero **deniega** `follower_count` (y `video.list`) con
    `scope_not_authorized` hasta aprobar la app (igual que el límite 2026 de
    Spotify). El contador se intenta por separado y queda `None` si no está
    autorizado.
    """
    datos = _api(
        "user/info/",
        "GET",
        access_token,
        params={"fields": "open_id,display_name,avatar_url"},
    )
    usuario = datos.get("data", {}).get("user", {}) or {}
    seguidores = None
    try:
        extra = _api(
            "user/info/",
            "GET",
            access_token,
            params={"fields": "follower_count"},
        )
        seguidores = int(
            extra.get("data", {}).get("user", {}).get("follower_count") or 0
        )
    except Exception:
        pass
    return {
        "open_id": usuario.get("open_id") or "",
        "display_name": usuario.get("display_name") or "",
        "follower_count": seguidores,
        "avatar_url": usuario.get("avatar_url") or "",
    }


def video_list(access_token: str, limite: int = 20) -> list[dict]:
    """Videos recientes del usuario autorizado (normalizados para el feed)."""
    datos = _api(
        "video/list/",
        "POST",
        access_token,
        params={"fields": "id,title,cover_image_url,create_time,share_url"},
        body={"max_count": limite, "cursor": 0},
    )
    items = []
    for v in datos.get("data", {}).get("videos", []) or []:
        creado = v.get("create_time")
        fecha = None
        if creado:
            try:
                fecha = datetime.fromtimestamp(int(creado))
            except (TypeError, ValueError, OSError):
                fecha = None
        url = v.get("share_url") or ""
        video_id = v.get("id") or ""
        if not url and video_id:
            url = f"https://www.tiktok.com/@user/video/{video_id}"
        if not url:
            continue
        items.append(
            {
                "url": url,
                "titulo": (v.get("title") or "").strip()[:200],
                "fecha": fecha,
                "imagen": v.get("cover_image_url") or "",
                "video_id": video_id,
            }
        )
    return items