"""Adaptador Beatport: lanzamientos de un artista desde su página.

Beatport no ofrece API pública (la de socios es de pago). Sus páginas de
artista son una app Next.js con el estado serializado en `__NEXT_DATA__`
(JSON); de ahí se lee la query de lanzamientos (`state.data.results`).

Es una fuente frágil (el JSON embebido puede cambiar): ante cualquier
estructura inesperada se devuelve lista vacía, sin romper el resto del sync.
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
RE_NEXT_DATA = re.compile(r'__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL)
RE_FECHA = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


class BeatportError(ScraperError):
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


def _fecha(valor: str | None) -> datetime | None:
    """Fecha ISO (o fecha parcial) de `publish_date`/`new_release_date`."""
    if not valor:
        return None
    m = RE_FECHA.search(valor)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _pagina_releases(url: str) -> str:
    """Normaliza la URL de un artista a su pestaña de lanzamientos."""
    if "/releases" in url:
        return url
    return url.rstrip("/") + "/releases"


def ultimos_lanzamientos(url: str, limite: int = 6) -> list[dict]:
    """Últimos lanzamientos del artista desde `__NEXT_DATA__` de su página.

    Devuelve el formato normalizado de feed (`titulo`, `url`, `fecha`,
    `imagen`). La URL pública es `beatport.com/release/{slug}/{id}`.
    """
    html = _get(_pagina_releases(url))
    if html is None:
        raise BeatportError(f"No se pudo leer la página de Beatport: {url}")
    m = RE_NEXT_DATA.search(html)
    if not m:
        return []
    try:
        datos = json.loads(m.group(1))
    except ValueError:
        return []
    queries = (
        datos.get("props", {})
        .get("pageProps", {})
        .get("dehydratedState", {})
        .get("queries", [])
    )
    for q in queries:
        data = q.get("state", {}).get("data")
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            continue
        items = []
        for r in data["results"]:
            slug, rid = r.get("slug"), r.get("id")
            items.append(
                {
                    "titulo": r.get("name") or "",
                    "url": (
                        f"https://www.beatport.com/release/{slug}/{rid}"
                        if slug and rid
                        else r.get("url") or ""
                    ),
                    "fecha": _fecha(r.get("publish_date") or r.get("new_release_date")),
                    "imagen": (r.get("image") or {}).get("uri") or "",
                }
            )
            if len(items) >= limite:
                break
        if items:
            return items
    return []