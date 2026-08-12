"""Cliente oEmbed común con caché compartida.

Instagram, Facebook y TikTok comparten el mismo patrón de consulta a un
endpoint oEmbed público; aquí vive el request + la caché, para que cada
adaptador sea solo una declaración de endpoint.
"""

import time

import requests

_CACHE: dict[tuple[str, str], tuple[float, dict | None]] = {}
_TTL = 3600  # 1 hora
DEFAULT_TIMEOUT = 10


def oembed_get(url: str, endpoint: str) -> dict | None:
    """Consulta un oEmbed por `url` en `endpoint`. Devuelve dict o `None`.

    Cachea por (endpoint, url) durante `_TTL`. Si el endpoint responde 404
    (post privado/inexistente) o falla la red, devuelve `None`.
    """
    clave = (endpoint, url)
    cacheado = _CACHE.get(clave)
    if cacheado and time.time() - cacheado[0] < _TTL:
        return cacheado[1]

    datos = _fetch(endpoint, {"url": url, "omitscript": "true"})
    _CACHE[clave] = (time.time(), datos)
    return datos


def _fetch(endpoint: str, params: dict) -> dict | None:
    try:
        respuesta = requests.get(endpoint, params=params, timeout=DEFAULT_TIMEOUT)
        if respuesta.status_code == 200:
            return respuesta.json()
    except requests.RequestException:
        return None
    return None