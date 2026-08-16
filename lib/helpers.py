"""Utilidades puras compartidas de la escena local.

Funciones sin efectos: formato de URLs, géneros y el índice de alcance.
La lógica de aplicación (read-models, feed, ranking) vive en `lib/servicios`,
y el acceso a datos en `lib/repository`.
"""

import math
import re
from urllib.parse import quote

import pandas as pd
from sqlalchemy.orm import Session

from db.models import Artist
from scraper.jerarquias import PRIORIDAD_LINK_PUENTE


def youtube_video_id(url: str) -> str:
    """Extrae el ID de video de un URL de YouTube."""
    m = re.search(
        r"(?:v=|youtu\.be/|shorts/|embed/)([0-9A-Za-z_-]{11})", url or ""
    )
    return m.group(1) if m else ""


def youtube_thumbnail(url: str) -> str:
    """Miniatura por defecto de YouTube a partir de un URL de video."""
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([0-9A-Za-z_-]{11})", url or "")
    if m:
        return f"https://i.ytimg.com/vi/{m.group(1)}/hqdefault.jpg"
    return ""


def instagram_post_code(url: str) -> str:
    """Código corto de un post de Instagram (/p/, /reel/, /tv/)."""
    m = re.search(r"/(?:p|reel|tv)/([0-9A-Za-z_-]+)", url or "")
    return m.group(1) if m else ""


def instagram_embed_url(url: str) -> str:
    """Iframe embebible oficial de Instagram para un post (sin token)."""
    codigo = instagram_post_code(url)
    if codigo:
        return f"https://www.instagram.com/p/{codigo}/embed/captioned/"
    return ""


def facebook_embed_url(url: str) -> str:
    """Iframe embebible oficial de Facebook (plugin de post, sin token)."""
    url = (url or "").strip()
    if not url:
        return ""
    return (
        "https://www.facebook.com/plugins/post.php"
        f"?href={quote(url, safe='')}&show_text=true"
    )


def artista_link_principal(session: Session, artist: Artist) -> dict | None:
    """Enlace 'puente' para la tarjeta de un artista (mayor prioridad de plataforma)."""
    candidatos = [l for l in artist.links if not l.es_busqueda and l.url]
    if not candidatos:
        return None
    candidatos.sort(
        key=lambda l: (
            PRIORIDAD_LINK_PUENTE.index(l.plataforma)
            if l.plataforma in PRIORIDAD_LINK_PUENTE
            else len(PRIORIDAD_LINK_PUENTE)
        )
    )
    mejor = candidatos[0]
    return {"plataforma": mejor.plataforma, "url": mejor.url}


TIPOS_FEED = {
    "video": "🎬 Video",
    "lanzamiento": "💿 Lanzamiento",
    "evento": "📅 Evento",
    "post": "📝 Post",
    "error": "⚠️ Error",
}


def conteo_generos(df: pd.DataFrame) -> pd.Series:
    """Conteo de géneros a partir de la columna `generos`.

    Cada artista puede declarar varios géneros separados por `/`, `,` o
    paréntesis; se cuenta cada uno por separado (sin mayúsculas).
    """
    conteo: dict[str, int] = {}
    for generos in df["generos"].dropna():
        generos = str(generos).strip()
        if not generos or generos == "[PENDIENTE]":
            continue
        for parte in re.split(r"[/,()]", generos):
            parte = parte.strip().lower()
            if not parte or parte == "[pendiente]" or parte.startswith("+"):
                continue
            conteo[parte] = conteo.get(parte, 0) + 1
    return pd.Series(conteo).sort_values(ascending=False)


def generos_hashtags(generos: str) -> list[str]:
    """Divide la cadena de géneros en etiquetas individuales (sin '#')."""
    generos = str(generos or "").strip()
    if not generos or generos == "[PENDIENTE]":
        return []
    etiquetas = []
    for parte in re.split(r"[/,()]", generos):
        parte = parte.strip()
        if not parte or parte.lower() == "[pendiente]" or parte.startswith("+"):
            continue
        etiquetas.append(parte)
    return etiquetas


# Vocabulario para detectar géneros dentro de una bio/descripción con fuente.
GENEROS_VOCABULARIO = {
    "pop punk": "pop punk",
    "punk rock": "punk rock",
    "rock n roll": "rock n' roll",
    "rock and roll": "rock n' roll",
    "rock en español": "rock en español",
    "rock alternativo": "rock alternativo",
    "post-punk": "post-punk",
    "post punk": "post-punk",
    "electrónica": "electrónica",
    "electronica": "electrónica",
    "electrónico": "electrónica",
    "electronicore": "electronicore",
    "industrial": "industrial",
    "darkwave": "darkwave",
    "dark wave": "darkwave",
    "new wave": "new wave",
    "coldwave": "coldwave",
    "cold wave": "coldwave",
    "synthpop": "synthpop",
    "synth pop": "synthpop",
    "techno": "techno",
    "tech house": "tech house",
    "house": "house",
    "deep house": "deep house",
    "tribal": "tribal",
    "riddim": "riddim",
    "dubstep": "dubstep",
    "drum and bass": "drum and bass",
    "hardcore": "hardcore",
    "metalcore": "metalcore",
    "hardstyle": "hardstyle",
    "metal": "metal",
    "drone": "drone",
    "ambient": "ambient",
    "emo": "emo",
    "rock": "rock",
    "pop": "pop",
    "cumbia": "cumbia",
    "villero": "villero",
    "reggae": "reggae",
    "ska": "ska",
    "indie": "indie",
    "rap": "rap",
    "hip hop": "hip hop",
    "hip-hop": "hip hop",
    "reggaetón": "reggaetón",
    "reggaeton": "reggaetón",
    "trap": "trap",
    "norteño": "norteño",
    "corridos": "corridos",
    "salsa": "salsa",
    "jazz": "jazz",
    "blues": "blues",
    "funk": "funk",
    "soul": "soul",
    "folk": "folk",
}

TEXTO_PLANTILLA = (
    "share your videos with friends, family, and the world",
    "listen to",  # plantillas de SoundCloud: "Play X and discover followers..."
    "explore the largest community",
    "stream tracks, albums",
    "fans and supporters",
    "view the profiles of people",
    "the official channel of",
    "videos every week",
    "subscribe to see",
)


def es_bio_clara(texto: str, minimo: int = 15) -> bool:
    """True si el texto puede usarse como bio (no es plantilla de plataforma).

    Una bio "clara" tiene longitud mínima y no repite el texto por defecto de
    la plataforma (YouTube, SoundCloud, etc.).
    """
    texto = (texto or "").strip()
    if len(texto) < minimo:
        return False
    bajo = texto.lower()
    for plantilla in TEXTO_PLANTILLA:
        if plantilla in bajo:
            return False
    return True


def generos_desde_texto(texto: str) -> list[str]:
    """Géneros del vocabulario presentes en una bio/descripción (con fuente).

    Devuelve los géneros detectados en el orden en que aparecen en el texto,
    sin duplicados y sin redundancias (un género que ya es parte de otro, ej.
    "pop" dentro de "pop punk", se omite).
    """
    texto = (texto or "").lower()
    posiciones: list[tuple[int, str]] = []
    for patron, etiqueta in GENEROS_VOCABULARIO.items():
        m = re.search(rf"(?<!\w){re.escape(patron)}(?!\w)", texto)
        if m:
            posiciones.append((m.start(), etiqueta))
    posiciones.sort()
    encontrados = [etiqueta for _, etiqueta in posiciones]
    return [
        g
        for g in encontrados
        if not any(g in otro and g != otro for otro in encontrados)
    ]


# Peso de cada plataforma en el índice de alcance (suma 100).
PESOS_ALCANCE = {
    "ig": 0.29,
    "fb": 0.24,
    "spotify": 0.19,
    "yt": 0.09,
    "tt": 0.09,
    "bandcamp": 0.025,
    "soundcloud": 0.025,
    "beatport": 0.03,
    "mixcloud": 0.02,
}

# Métrica de alcance por plataforma, en orden de prioridad.
METRICA_ALCANCE_POR_PLATAFORMA = {
    "ig": ("seguidores",),
    "fb": ("seguidores",),
    "yt": ("vistas", "seguidores"),
    "tt": ("vistas", "seguidores"),
    "spotify": ("reproducciones", "seguidores"),
    "bandcamp": ("reproducciones",),
    "soundcloud": ("reproducciones",),
    "beatport": ("seguidores",),
    "mixcloud": ("seguidores",),
}


def _es_metrico(valor) -> bool:
    """True si el valor es un número positivo real (métrica). Excluye NaN."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return False
    return bool(v) and not math.isnan(v)


def _alcance_bruto(metricas: dict, plataforma: str) -> float:
    """Valor bruto de la métrica de alcance de una plataforma (0 si no hay)."""
    met = metricas.get(plataforma) or {}
    for tipo in METRICA_ALCANCE_POR_PLATAFORMA[plataforma]:
        valor = met.get(tipo)
        if _es_metrico(valor):
            return float(valor)
    return 0.0


def _log_reach(valor: float) -> float:
    return math.log10(valor + 1.0) if valor > 0 else 0.0


def indice_alcance(metricas_por_artista: dict[str, dict]) -> dict[str, float]:
    """Índice de alcance 0-100 por artista: suma ponderada por plataforma.

    `metricas_por_artista`: {slug: {plataforma: {tipo: valor}}}. Para cada
    plataforma se toma su métrica de alcance (seguidores, reproducciones,
    vistas), se transforma con log10(v+1) y se normaliza 0-100 entre **todos**
    los artistas (los que no tienen la plataforma cuentan 0, así se penaliza no
    tenerla). El índice es la suma ponderada de esos alcances (`PESOS_ALCANCE`).
    """
    logs_por_plataforma: dict[str, list[float]] = {}
    for metricas in metricas_por_artista.values():
        for plataforma in PESOS_ALCANCE:
            logs_por_plataforma.setdefault(plataforma, []).append(
                _log_reach(_alcance_bruto(metricas, plataforma))
            )

    indice: dict[str, float] = {}
    for slug, metricas in metricas_por_artista.items():
        total = 0.0
        for plataforma, peso in PESOS_ALCANCE.items():
            maximo = max(logs_por_plataforma[plataforma])
            if maximo <= 0:
                continue
            valor_log = _log_reach(_alcance_bruto(metricas, plataforma))
            total += peso * (valor_log / maximo) * 100.0
        indice[slug] = round(total, 1)
    return indice


def slugificar(nombre: str) -> str:
    """Slug simple para identificadores (`"DJ Vikingo"` → `"dj_vikingo"`)."""
    import re
    import unicodedata

    texto = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "_", texto.lower()).strip("_")
    return texto or "sin_nombre"