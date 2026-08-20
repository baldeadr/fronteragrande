"""Adaptador Bandcamp: bio y etiquetas de género desde la página del artista.

Las páginas de Bandcamp se sirven como HTML sin ejecutar JS e incluyen la bio
del artista en `#bio-text` (y como respaldo en `og:description`). Las
etiquetas de género aparecen como enlaces con clase `tag`.
"""

import re
from datetime import date
from urllib.parse import urlparse

import requests

from scraper.errors import ScraperError

TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126 Safari/537.36"
)

RE_BIO_TEXT = re.compile(r'<div[^>]*id=["\']bio-text["\']')
RE_TAG = re.compile(r'<a[^>]*class=["\'][^"\']*\btag\b[^"\']*["\'][^>]*>([^<]+)</a>')
RE_OG_DESCRIPTION = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)'
)
RE_OG_DESCRIPTION_INV = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']'
)
RE_ITEM_GRID = re.compile(
    r'<li[^>]*class="[^"]*music-grid-item[^"]*"[^>]*>(.*?)</li>', re.DOTALL
)


class BandcampError(ScraperError):
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


def _div_balanceado(html: str, inicio: int) -> str:
    """Contenido de un bloque `<div>` balanceado desde la posición de su apertura."""
    cierre_apertura = html.find(">", inicio)
    if cierre_apertura < 0:
        return ""
    profundidad = 1
    pos = cierre_apertura
    while pos < len(html):
        pos = html.find("<", pos + 1)
        if pos < 0:
            break
        if html.startswith("</div", pos):
            profundidad -= 1
            if profundidad == 0:
                return html[cierre_apertura + 1 : pos]
        elif html.startswith("<div", pos):
            profundidad += 1
    return ""


def _limpiar(texto: str) -> str:
    """Quita el toggle "read-more", las etiquetas y normaliza espacios."""
    texto = re.sub(
        r'<div[^>]*class=["\'][^"\']*read-more[^"\']*["\'][^>]*>.*?</div>',
        "",
        texto,
        flags=re.DOTALL,
    )
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _parse_bio(html: str) -> str:
    """Bio del artista desde el HTML de la página."""
    html = html or ""
    m = RE_BIO_TEXT.search(html)
    if m:
        contenido = _div_balanceado(html, m.start())
        bio = _limpiar(contenido)
        if bio:
            return bio
    og = RE_OG_DESCRIPTION.search(html) or RE_OG_DESCRIPTION_INV.search(html)
    if og:
        return og.group(1).strip()
    return ""


def _parse_tags(html: str) -> list[str]:
    """Etiquetas de género visibles en la página."""
    etiquetas = []
    for m in RE_TAG.finditer(html or ""):
        etiqueta = m.group(1).strip()
        if etiqueta and etiqueta not in etiquetas:
            etiquetas.append(etiqueta)
    return etiquetas


def bandcamp_bio(url: str) -> str:
    """Bio/descripción del artista desde su página de Bandcamp."""
    html = _get(url)
    if html is None:
        raise BandcampError(f"No se pudo leer la página de Bandcamp: {url}")
    return _parse_bio(html)


def bandcamp_tags(url: str) -> list[str]:
    """Etiquetas de género de la página de Bandcamp del artista."""
    html = _get(url)
    if html is None:
        raise BandcampError(f"No se pudo leer la página de Bandcamp: {url}")
    return _parse_tags(html)


def _fecha_desde_titulo(titulo: str) -> date | None:
    """Año del lanzamiento cuando el artista lo incluye en el título (ej. "(2025)").

    La cuadrícula de Bandcamp no expone la fecha exacta; el año que aparece en
    el título es un dato con fuente (lo escribió el artista). Sin año, `None`.
    """
    m = re.search(r"\((19|20)\d\d\)", titulo)
    if m:
        try:
            return date(int(m.group(0).strip("()")), 1, 1)
        except ValueError:
            return None
    return None


def _base_url(url: str) -> str:
    """Esquema + dominio de la página del artista (para resolver hrefs)."""
    partes = urlparse(url or "")
    return f"{partes.scheme}://{partes.netloc}"


def _parse_grid(html: str, url: str, limite: int) -> list[dict]:
    """Lanzamientos desde la cuadrícula (`li.music-grid-item`) de la página."""
    base = _base_url(url)
    items = []
    for li in RE_ITEM_GRID.finditer(html or ""):
        bloque = li.group(1)
        a = re.search(r'<a[^>]+href="([^"]+)"', bloque)
        img = re.search(r'<img[^>]+src="([^"]+)"', bloque)
        tit = re.search(r'<p class="title">(.*?)</p>', bloque, re.DOTALL)
        if not a:
            continue
        href = a.group(1)
        if href.startswith("http"):
            url_abs = href
        elif href.startswith("/"):
            url_abs = base + href
        else:
            continue
        titulo = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", tit.group(1))).strip() if tit else ""
        items.append(
            {
                "titulo": titulo,
                "url": url_abs,
                "fecha": _fecha_desde_titulo(titulo),
                "imagen": img.group(1) if img else "",
            }
        )
        if len(items) >= limite:
            break
    return items


def ultimos_lanzamientos(url: str, limite: int = 6) -> list[dict]:
    """Últimos lanzamientos del artista desde la cuadrícula de su página.

    Devuelve el formato normalizado de feed (`titulo`, `url`, `fecha`,
    `imagen`). La fecha es el año del título (ver `_fecha_desde_titulo`).
    """
    html = _get(url)
    if html is None:
        raise BandcampError(f"No se pudo leer la página de Bandcamp: {url}")
    return _parse_grid(html, url, limite)