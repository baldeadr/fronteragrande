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


# Pesos globales de las señales de audiencia y consumo (suman 100).
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

PESOS_AUDIENCIA = {
    ("ig", "seguidores"): 0.29,
    ("fb", "seguidores"): 0.24,
    ("tt", "seguidores"): 0.09,
    ("yt", "seguidores"): 0.027,
    ("spotify", "seguidores"): 0.0475,
    ("beatport", "seguidores"): 0.03,
    ("mixcloud", "seguidores"): 0.02,
}

PESOS_CONSUMO = {
    ("yt", "vistas"): 0.063,
    ("spotify", "consumo"): 0.1425,
    ("bandcamp", "reproducciones"): 0.025,
    ("soundcloud", "reproducciones"): 0.025,
}

PESO_GRUPO_AUDIENCIA = 0.55
PESO_GRUPO_CONSUMO = 0.45

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
    if not _es_metrico(valor):
        return 0.0
    return math.log10(float(valor) + 1.0)


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


def indices_audiencia_consumo(
    metricas_por_artista: dict[str, dict],
) -> dict[str, dict[str, float]]:
    """Calcula índices separados de audiencia, consumo y total.

    Cada señal se normaliza por separado después de aplicar log10. YouTube
    aporta 30% de su peso a suscriptores y 70% a vistas; Spotify reparte su
    peso entre seguidores y señales de escucha. Los índices de grupo quedan en
    0-100 y el índice global combina audiencia (55%) y consumo (45%).
    """

    grupos = {
        "audiencia": PESOS_AUDIENCIA,
        "consumo": PESOS_CONSUMO,
    }

    def valor_señal(metricas: dict, señal: tuple[str, str]):
        plataforma, tipo = señal
        datos = metricas.get(plataforma) or {}
        if plataforma == "spotify" and tipo == "consumo":
            return datos.get("oyentes_mensuales") or datos.get("reproducciones")
        return datos.get(tipo, 0)

    logs: dict[tuple[str, str], list[float]] = {}
    for pesos in grupos.values():
        for señal in pesos:
            logs[señal] = [
                _log_reach(valor_señal(metricas, señal))
                for metricas in metricas_por_artista.values()
            ]

    resultado: dict[str, dict[str, float]] = {}
    for slug, metricas in metricas_por_artista.items():
        scores: dict[str, float] = {}
        for nombre, pesos in grupos.items():
            peso_total = sum(pesos.values())
            score = 0.0
            for señal, peso in pesos.items():
                maximo = max(logs[señal], default=0.0)
                if maximo <= 0:
                    continue
                valor = _log_reach(valor_señal(metricas, señal))
                score += (peso / peso_total) * (valor / maximo) * 100.0
            scores[nombre] = round(score, 1)
        scores["indice"] = round(
            scores["audiencia"] * PESO_GRUPO_AUDIENCIA
            + scores["consumo"] * PESO_GRUPO_CONSUMO,
            1,
        )
        resultado[slug] = scores
    return resultado


def _valor_seguro(metricas: dict, plataforma: str, tipo: str) -> float:
    """Valor numérico de una métrica (0 si no existe o no es válida)."""
    dato = metricas.get(plataforma, {}).get(tipo)
    try:
        numero = float(dato)
    except (TypeError, ValueError):
        return 0.0
    return numero if numero > 0 else 0.0


def ratio_viralidad_yt(metricas: dict) -> float | None:
    """Vistas / suscriptores de YouTube. None si no hay datos suficientes."""
    vistas = _valor_seguro(metricas, "yt", "vistas")
    suscriptores = _valor_seguro(metricas, "yt", "seguidores")
    if vistas <= 0 or suscriptores <= 0:
        return None
    return round(vistas / suscriptores, 1)


def ratio_engagement_spotify(metricas: dict) -> float | None:
    """Oyentes mensuales / seguidores de Spotify. None si no hay datos."""
    oyentes = _valor_seguro(metricas, "spotify", "oyentes_mensuales")
    seguidores = _valor_seguro(metricas, "spotify", "seguidores")
    if oyentes <= 0 or seguidores <= 0:
        return None
    return round(oyentes / seguidores, 1)


def ratio_social_musica(metricas: dict) -> float | None:
    """Seguidores sociales / consumo musical. None si no hay ambos."""
    sociales = sum(
        _valor_seguro(metricas, p, "seguidores") for p in ("ig", "fb", "tt", "yt")
    )
    musica = _valor_seguro(metricas, "spotify", "oyentes_mensuales") or _valor_seguro(
        metricas, "spotify", "reproducciones"
    )
    musica += _valor_seguro(metricas, "bandcamp", "reproducciones")
    musica += _valor_seguro(metricas, "soundcloud", "reproducciones")
    if sociales <= 0 or musica <= 0:
        return None
    return round(sociales / musica, 1)


def dominancia_plataforma(metricas: dict) -> dict[str, float]:
    """Porcentaje de dominancia de cada plataforma sobre el total.

    Usa la métrica de alcance de cada plataforma (seguidores, vistas,
    reproducciones) y calcula qué % representa del total combinado.
    Devuelve {plataforma: porcentaje} solo para las que tienen dato.
    """
    partes: dict[str, float] = {}
    for plataforma in PESOS_ALCANCE:
        bruto = _alcance_bruto(metricas, plataforma)
        if bruto > 0:
            partes[plataforma] = bruto
    total = sum(partes.values())
    if total <= 0:
        return {}
    return {p: round(v / total * 100, 1) for p, v in sorted(
        partes.items(), key=lambda kv: kv[1], reverse=True
    )}


def patron_dominancia(metricas: dict) -> str:
    """Detecta el patrón de consumo dominante del artista.

    Devuelve: 'youtube_dominante', 'spotify_dominante', 'social_dominante',
    'distribuido' o 'sin_datos'.
    """
    vistas_yt = _valor_seguro(metricas, "yt", "vistas")
    oyentes_sp = _valor_seguro(metricas, "spotify", "oyentes_mensuales") or _valor_seguro(
        metricas, "spotify", "reproducciones"
    )
    sociales = sum(
        _valor_seguro(metricas, p, "seguidores") for p in ("ig", "fb", "tt", "yt")
    )

    if vistas_yt <= 0 and oyentes_sp <= 0 and sociales <= 0:
        return "sin_datos"

    total = vistas_yt + oyentes_sp + sociales
    if total <= 0:
        return "sin_datos"

    pct_yt = vistas_yt / total
    pct_sp = oyentes_sp / total
    pct_soc = sociales / total

    if pct_yt >= 0.5:
        return "youtube_dominante"
    if pct_sp >= 0.5:
        return "spotify_dominante"
    if pct_soc >= 0.5:
        return "social_dominante"
    return "distribuido"


TEXTO_PATRON_CONSUMO = {
    "youtube_dominante": (
        "La audiencia se concentra en YouTube, donde el contenido de audio "
        "genera vistas significativas. Esto refleja un hábito de consumo "
        "regional: la audiencia busca y escucha gratis en YouTube. Oportunidad: "
        "los videos ya llegan a mucha gente, pero en YouTube los ingresos por "
        "audio son mínimos. Añade enlaces y llamadas a la acción (descripción, "
        "pantallas finales) hacia tu página de Spotify, tus redes y tus "
        "lanzamientos para convertir esas vistas en seguidores conectados que "
        "generen ingresos reales."
    ),
    "spotify_dominante": (
        "Las plataformas de streaming concentran la mayor parte del consumo "
        "registrado. La audiencia descubre y guarda contenido en playlists, "
        "lo que indica un consumo más intencional y mejor monetizado. "
        "Oportunidad: tienes oyentes que ya te escuchan de forma activa; "
        "fortalece tu presencia en redes sociales (Instagram, TikTok) para que "
        "esos oyentes también te sigan y vean tu contenido, ampliando el "
        "descubrimiento y fidelizando a tu audiencia."
    ),
    "social_dominante": (
        "Las redes sociales concentran la mayor audiencia registrada; el "
        "consumo en plataformas musicales es menor. Oportunidad: ya cuentas "
        "con una comunidad que te sigue en redes; distribuye tu música en "
        "plataformas de streaming (Spotify, YouTube Music) y enlázala desde "
        "tus perfiles para que esa audiencia social se convierta en oyentes y "
        "en ingresos por reproducción."
    ),
    "distribuido": (
        "La presencia está distribuida entre redes sociales y plataformas "
        "musicales sin una dominancia clara, lo que indica una audiencia "
        "multicanal. Oportunidad: tu base está equilibrada, así que el "
        "crecimiento puede venir de enfocar una plataforma concreta y medir "
        "dónde responden mejor tu audiencia y tu contenido."
    ),
    "sin_datos": (
        "Aún no hay suficientes datos para detectar un patrón de consumo. "
        "Conecta tus plataformas (Facebook/Instagram, TikTok) y añade tus "
        "enlaces de streaming para que el análisis pueda ayudarte."
    ),
}


def slugificar(nombre: str) -> str:
    """Slug simple para identificadores (`"DJ Vikingo"` → `"dj_vikingo"`)."""
    import re
    import unicodedata

    texto = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "_", texto.lower()).strip("_")
    return texto or "sin_nombre"


def normalizar_url_para_duplicados(url: str) -> str:
    """Devuelve una forma canónica de una URL para detectar duplicados.

    Quita espacios, fuerza `https://` si no tiene esquema, normaliza el host
    a minúsculas, elimina `www.`, elimina querystring y fragmento, y quita la
    barra final del path. Esto cubre variantes comunes de un mismo perfil
    social (ej. `instagram.com/user/`, `www.instagram.com/user?igsh=...`).
    """
    from urllib.parse import urlparse, urlunparse

    url = (url or "").strip()
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme.lower(), host, path, "", "", ""))
