"""Adaptador SoundCloud: bio del perfil desde el JSON de hidratación.

SoundCloud sirve las páginas con el estado de la app en
`window.__sc_hydration` (JSON); la descripción real del perfil vive en el
objeto `hydratable == "user"` → `data.description`. El `og:description` de
SoundCloud es texto de marketing y no se usa como bio.
"""

import json
import re
from datetime import datetime

import requests

from scraper.errors import ScraperError

TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126 Safari/537.36"
)
MARCA_HIDRATACION = "window.__sc_hydration"
API_V2 = "https://api-v2.soundcloud.com"
RE_SCRIPT_BUNDLE = re.compile(
    r'<script[^>]+src="(https://a-v2\.sndcdn\.com/[^"]+\.js)"'
)
RE_CLIENT_ID = re.compile(r'client_id["\':\s=]+["\']([A-Za-z0-9]{15,})["\']')


class SoundCloudError(ScraperError):
    pass


def _get(url: str) -> str | None:
    try:
        respuesta = requests.get(
            url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}
        )
        if respuesta.ok:
            return respuesta.text
    except requests.RequestException:
        return None
    return None


def _json_balanceado(html: str, inicio: int) -> str | None:
    """Extrae el JSON `[...]` balanceado (respetando strings y escapes)."""
    apertura = html.find("[", inicio)
    if apertura < 0:
        return None
    profundidad = 0
    en_string = False
    escape = False
    for pos in range(apertura, len(html)):
        c = html[pos]
        if en_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                en_string = False
            continue
        if c == '"':
            en_string = True
        elif c == "[":
            profundidad += 1
        elif c == "]":
            profundidad -= 1
            if profundidad == 0:
                return html[apertura : pos + 1]
    return None


def _parse_bio(html: str) -> str:
    """Bio del perfil desde el JSON `__sc_hydration`."""
    inicio = (html or "").find(MARCA_HIDRATACION)
    if inicio < 0:
        return ""
    raw = _json_balanceado(html, inicio)
    if not raw:
        return ""
    try:
        datos = json.loads(raw)
    except ValueError:
        return ""
    for objeto in datos:
        if isinstance(objeto, dict) and objeto.get("hydratable") == "user":
            descripcion = (objeto.get("data") or {}).get("description") or ""
            return descripcion.strip()
    return ""


def soundcloud_bio(url: str) -> str:
    """Bio/descripción del perfil del artista en SoundCloud."""
    html = _get(url)
    if html is None:
        raise SoundCloudError(f"No se pudo leer el perfil de SoundCloud: {url}")
    return _parse_bio(html)


_CLIENT_ID_CACHE: dict = {}


def _client_id(url: str) -> str:
    """client_id de la api-v2 de SoundCloud (leído de su bundle JS).

    SoundCloud no documenta una API pública; el `client_id` que usa su propia
    web se extrae del bundle de scripts (patrón frágil, se cachea por
    proceso). Si no aparece, devuelve "" y el llamador omite la fuente.
    """
    if _CLIENT_ID_CACHE.get("id"):
        return _CLIENT_ID_CACHE["id"]
    html = _get(url) or ""
    for src in RE_SCRIPT_BUNDLE.findall(html):
        cuerpo = _get(src)
        if not cuerpo:
            continue
        m = RE_CLIENT_ID.search(cuerpo)
        if m:
            _CLIENT_ID_CACHE["id"] = m.group(1)
            return m.group(1)
    return ""


def _user_id(url: str) -> int | None:
    """ID interno del usuario desde la hidratación del perfil."""
    html = _get(url)
    if not html:
        return None
    inicio = html.find(MARCA_HIDRATACION)
    if inicio < 0:
        return None
    raw = _json_balanceado(html, inicio)
    if not raw:
        return None
    try:
        datos = json.loads(raw)
    except ValueError:
        return None
    for objeto in datos:
        if isinstance(objeto, dict) and objeto.get("hydratable") == "user":
            return (objeto.get("data") or {}).get("id")
    return None


def _fecha_iso(valor: str | None) -> datetime | None:
    """Convierte `created_at` ISO (ej. 2026-08-01T12:00:00Z) en datetime."""
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def ultimas_pistas(url: str, limite: int = 6) -> list[dict]:
    """Últimas pistas subidas por el artista vía api-v2.

    Requiere el `client_id` del bundle (ver `_client_id`). Devuelve el
    formato normalizado de feed (`titulo`, `url`, `fecha`, `imagen`); si la
    fuente no responde, devuelve una lista vacía (fuente opcional).
    """
    user_id = _user_id(url)
    client_id = _client_id(url)
    if not user_id or not client_id:
        return []
    try:
        respuesta = requests.get(
            f"{API_V2}/users/{user_id}/tracks",
            params={"client_id": client_id, "limit": limite, "filter.format": "mp3"},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
    except requests.RequestException:
        return []
    if not respuesta.ok:
        return []
    items = []
    for t in respuesta.json().get("collection", []):
        if t.get("kind") != "track":
            continue
        url_track = t.get("permalink_url") or ""
        if not url_track:
            continue
        items.append(
            {
                "titulo": t.get("title") or "",
                "url": url_track,
                "fecha": _fecha_iso(t.get("created_at")),
                "imagen": t.get("artwork_url")
                or (t.get("user") or {}).get("avatar_url")
                or "",
            }
        )
    return items[:limite]


def reproducciones(url: str) -> int:
    """Reproducciones acumuladas del artista (suma de plays de sus pistas).

    Recorre todas las pistas públicas vía api-v2 (`/users/{id}/tracks`,
    paginado con `next_href`) y suma su `playback_count`. Si la fuente no se
    puede leer (sin `client_id` o error de red/HTTP), lanza `SoundCloudError`
    para que el llamador conserve el valor anterior y no invente un cero.
    """
    user_id = _user_id(url)
    client_id = _client_id(url)
    if not user_id or not client_id:
        raise SoundCloudError(f"No se pudo resolver el perfil de SoundCloud: {url}")
    total = 0
    siguiente = f"{API_V2}/users/{user_id}/tracks?client_id={client_id}&limit=200"
    for _ in range(25):
        try:
            respuesta = requests.get(
                siguiente, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
            )
        except requests.RequestException as exc:
            raise SoundCloudError(
                f"Error de red con SoundCloud: {url}"
            ) from exc
        if not respuesta.ok:
            raise SoundCloudError(
                f"SoundCloud respondió HTTP {respuesta.status_code}: {url}"
            )
        try:
            datos = respuesta.json()
        except ValueError as exc:
            raise SoundCloudError(
                f"SoundCloud devolvió JSON inválido: {url}"
            ) from exc
        for t in datos.get("collection", []):
            if t.get("kind") != "track":
                continue
            try:
                total += int(t.get("playback_count") or 0)
            except (TypeError, ValueError):
                continue
        siguiente = datos.get("next_href")
        if not siguiente:
            break
        if "client_id" not in siguiente:
            siguiente += ("&" if "?" in siguiente else "?") + f"client_id={client_id}"
    return total


def seguidores(url: str) -> int:
    """Seguidores del perfil del artista vía api-v2 (`/users/{id}`).

    Una sola llamada al perfil (sin paginar). Si la fuente no se puede leer
    (sin `client_id` o error de red/HTTP), lanza `SoundCloudError` para que el
    llamador conserve el valor anterior y no invente un cero.
    """
    user_id = _user_id(url)
    client_id = _client_id(url)
    if not user_id or not client_id:
        raise SoundCloudError(f"No se pudo resolver el perfil de SoundCloud: {url}")
    try:
        respuesta = requests.get(
            f"{API_V2}/users/{user_id}",
            params={"client_id": client_id},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise SoundCloudError(f"Error de red con SoundCloud: {url}") from exc
    if not respuesta.ok:
        raise SoundCloudError(
            f"SoundCloud respondió HTTP {respuesta.status_code}: {url}"
        )
    try:
        datos = respuesta.json()
    except ValueError as exc:
        raise SoundCloudError(
            f"SoundCloud devolvió JSON inválido: {url}"
        ) from exc
    try:
        return int(datos.get("followers_count") or 0)
    except (TypeError, ValueError):
        return 0