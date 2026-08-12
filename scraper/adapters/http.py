"""Adaptador HTTP: comprueba si una URL responde (salud básica del enlace).

Nota: redes como Instagram/Facebook bloquean scrapers; el chequeo HTTP solo
confirma que la URL sigue viva/responde, no el contenido.
"""

import requests

DEFAULT_TIMEOUT = 10
USER_AGENT = "FronteraGrande/0.1 (monitoreo de escena local)"


def check_url(url: str, timeout: int | None = None) -> dict:
    """Hace GET a la URL y devuelve resultado de salud.

    Devuelve: ok, status, latencia_ms y opcional error.
    """
    timeout = timeout or DEFAULT_TIMEOUT
    try:
        respuesta = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        return {
            "ok": respuesta.status_code < 400,
            "status": respuesta.status_code,
            "latencia_ms": round(respuesta.elapsed.total_seconds() * 1000, 1),
            "error": "",
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "status": None,
            "latencia_ms": None,
            "error": str(exc)[:200],
        }
