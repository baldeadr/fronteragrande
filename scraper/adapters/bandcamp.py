"""Adaptador Bandcamp: bio y etiquetas de género desde la página del artista.

Las páginas de Bandcamp se sirven como HTML sin ejecutar JS e incluyen la bio
del artista en `#bio-text` (y como respaldo en `og:description`). Las
etiquetas de género aparecen como enlaces con clase `tag`.
"""

import re

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