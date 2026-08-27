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

RE_RELEASED = re.compile(
    r'<p[^>]*class=["\'][^"\']*released[^"\']*["\'][^>]*>(.*?)</p>',
    re.IGNORECASE | re.DOTALL,
)
RE_DATE_META = re.compile(
    r'itemprop=["\']datePublished["\'][^>]*content=["\']([^"\']+)',
    re.IGNORECASE,
)


class BandcampError(ScraperError):
    pass


def _get(url: str) -> tuple[str | None, int | None]:
    """Devuelve (HTML, status). HTML es None si hubo error de red o status no-ok."""
    try:
        respuesta = requests.get(
            url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}
        )
        return (respuesta.text if respuesta.ok else None), respuesta.status_code
    except requests.RequestException:
        return None, None


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
    html, status = _get(url)
    if html is None:
        raise BandcampError(f"No se pudo leer la página de Bandcamp: {url} (status {status})")
    return _parse_bio(html)


def bandcamp_tags(url: str) -> list[str]:
    """Etiquetas de género de la página de Bandcamp del artista."""
    html, status = _get(url)
    if html is None:
        raise BandcampError(f"No se pudo leer la página de Bandcamp: {url} (status {status})")
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


RE_RELEASED = re.compile(
    r'<p[^>]*class=["\'][^"\']*released[^"\']*["\'][^>]*>(.*?)</p>',
    re.IGNORECASE | re.DOTALL,
)
RE_DATE_META = re.compile(
    r'itemprop=["\']datePublished["\'][^>]*content=["\']([^"\']+)',
    re.IGNORECASE,
)


def _fecha_desde_bloque(bloque: str) -> date | None:
    """Intenta extraer fecha del bloque HTML del grid item."""
    m = RE_RELEASED.search(bloque)
    if m:
        texto = re.sub(r"<[^>]+>", " ", m.group(1)).strip()
        for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(texto, fmt).date()
            except ValueError:
                pass
    m = RE_DATE_META.search(bloque)
    if m:
        try:
            return datetime.fromisoformat(m.group(1).replace("Z", "+00:00")).date()
        except ValueError:
            pass
    return None


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
        fecha = _fecha_desde_bloque(bloque) or _fecha_desde_titulo(titulo)
        items.append(
            {
                "titulo": titulo,
                "url": url_abs,
                "fecha": fecha,
                "imagen": img.group(1) if img else "",
            }
        )
        if len(items) >= limite:
            break
    return items


def _music_url(url: str) -> str:
    """Convierte URL de artista a URL de música (/music)."""
    from urllib.parse import urlparse, urlunparse
    partes = urlparse(url)
    path = partes.path.rstrip("/")
    if not path or path == "/":
        path = "/music"
    elif not path.startswith("/music"):
        path = "/music"
    return urlunparse((partes.scheme, partes.netloc, path, "", "", ""))


def ultimos_lanzamientos(url: str, limite: int = 6) -> list[dict]:
    """Últimos lanzamientos del artista desde la cuadrícula de su página /music.

    Devuelve el formato normalizado de feed (`titulo`, `url`, `fecha`,
    `imagen`). La fecha se intenta extraer del HTML (released/datePublished);
    si no hay, cae al año entre paréntesis del título.
    Levanta `BandcampError` si la página no se puede leer o no expone lanzamientos.
    """
    music_url = _music_url(url)
    html, status = _get(music_url)
    if html is None:
        raise BandcampError(f"No se pudo leer la página de Bandcamp: {music_url} (status {status})")
    items = _parse_grid(html, music_url, limite)
    if not items:
        raise BandcampError(
            f"La página de Bandcamp no expone lanzamientos: {music_url} (status {status})"
        )
    return items