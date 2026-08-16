"""Adaptador SoundCloud: bio del perfil desde el JSON de hidratación.

SoundCloud sirve las páginas con el estado de la app en
`window.__sc_hydration` (JSON); la descripción real del perfil vive en el
objeto `hydratable == "user"` → `data.description`. El `og:description` de
SoundCloud es texto de marketing y no se usa como bio.
"""

import json
import re

import requests

from scraper.errors import ScraperError

TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126 Safari/537.36"
)
MARCA_HIDRATACION = "window.__sc_hydration"


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