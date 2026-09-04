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
# Ajuste 2026-08: más peso a consumo real (Spotify oyentes, YT vistas) y menos a seguidores sociales.
PESOS_ALCANCE = {
    "ig": 0.18,
    "fb": 0.12,
    "spotify": 0.28,
    "yt": 0.20,
    "tt": 0.08,
    "bandcamp": 0.03,
    "soundcloud": 0.03,
    "beatport": 0.04,
    "mixcloud": 0.04,
}

PESOS_AUDIENCIA = {
    ("ig", "seguidores"): 0.15,
    ("fb", "seguidores"): 0.10,
    ("tt", "seguidores"): 0.08,
    ("yt", "seguidores"): 0.02,
    ("spotify", "seguidores"): 0.03,
    ("beatport", "seguidores"): 0.03,
    ("mixcloud", "seguidores"): 0.02,
}

PESOS_CONSUMO = {
    ("yt", "vistas"): 0.12,
    ("spotify", "consumo"): 0.25,
    ("bandcamp", "reproducciones"): 0.03,
    ("soundcloud", "reproducciones"): 0.03,
}

PESO_GRUPO_AUDIENCIA = 0.40
PESO_GRUPO_CONSUMO = 0.60

# Métrica de alcance por plataforma, en orden de prioridad.
# YouTube prioriza suscriptores antes que vistas: las vistas (viewCount del canal)
# incluyen Shorts y se descuentan con `FACTOR_CAPACIDAD_VISTAS_YT` en los índices.
METRICA_ALCANCE_POR_PLATAFORMA = {
    "ig": ("seguidores",),
    "fb": ("seguidores",),
    "yt": ("seguidores", "vistas"),
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


def _vistas_yt_capacidad(metricas: dict) -> float:
    """Vistas de YouTube con el descuento anti-shorts (60% de capacidad).

    El viewCount del canal incluye Shorts; para la clasificación y el ranking de
    alcance se aplica `FACTOR_CAPACIDAD_VISTAS_YT` para no premiar el inflado.
    """
    return _valor_seguro(metricas, "yt", "vistas") * FACTOR_CAPACIDAD_VISTAS_YT


def _alcance_para_indice(metricas: dict, plataforma: str) -> float:
    """Métrica de alcance de una plataforma para los índices de ranking.

    Igual que `_alcance_bruto` pero descuenta las vistas de YouTube con
    `FACTOR_CAPACIDAD_VISTAS_YT` (el viewCount del canal incluye Shorts), de modo
    que usa suscriptores cuando hay y, si solo hay vistas, las aplica al 60%.
    """
    bruto = _alcance_bruto(metricas, plataforma)
    if plataforma == "yt":
        seguidores = _valor_seguro(metricas, "yt", "seguidores")
        if seguidores > 0:
            return seguidores
        return _vistas_yt_capacidad(metricas)
    return bruto


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
                _log_reach(_alcance_para_indice(metricas, plataforma))
            )

    indice: dict[str, float] = {}
    for slug, metricas in metricas_por_artista.items():
        total = 0.0
        for plataforma, peso in PESOS_ALCANCE.items():
            maximo = max(logs_por_plataforma[plataforma])
            if maximo <= 0:
                continue
            valor_log = _log_reach(_alcance_para_indice(metricas, plataforma))
            total += peso * (valor_log / maximo) * 100.0
        indice[slug] = round(total, 1)
    return indice


def indices_audiencia_consumo(
    metricas_por_artista: dict[str, dict],
) -> dict[str, dict[str, float]]:
    """Calcula índices separados de audiencia, consumo y total.

    Cada señal se normaliza por separado después de aplicar log10. YouTube
    aporta parte de su peso a suscriptores y a vistas (las vistas se descuentan
    con `FACTOR_CAPACIDAD_VISTAS_YT` por el inflado de Shorts); Spotify reparte
    su peso entre seguidores y señales de escucha. Los índices de grupo quedan
    en 0-100 y el índice global combina audiencia (55%) y consumo (45%).
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
        if plataforma == "yt" and tipo == "vistas":
            return _vistas_yt_capacidad(metricas)
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


# Señales de audiencia y consumo separadas por dimensión.
#
# Cada dimensión compara SOLO unidades equivalentes (seguidores vs seguidores,
# reproducciones vs reproducciones) en escala log10, para que la comparativa sea
# justa. Históricamente se mezclaban vistas de YouTube (enormes por naturaleza)
# con oyentes de Spotify o seguidores sociales, lo que sesgaba siempre hacia YouTube.

MAPEO_AUDIENCIA = {
    "ig": ("seguidores",),
    "fb": ("seguidores",),
    "tt": ("seguidores",),
    "yt": ("seguidores",),
    "spotify": ("seguidores",),
    "beatport": ("seguidores",),
    "mixcloud": ("seguidores",),
}

MAPEO_CONSUMO = {
    "yt": ("vistas",),
    "spotify": ("reproducciones", "oyentes_mensuales"),
    "bandcamp": ("reproducciones",),
    "soundcloud": ("reproducciones",),
}

NOMBRE_DIMENSION_PATRON = {
    "ig": "instagram_dominante",
    "fb": "facebook_dominante",
    "tt": "tiktok_dominante",
    "yt": "youtube_dominante",
    "spotify": "spotify_dominante",
    "beatport": "beatport_dominante",
    "mixcloud": "mixcloud_dominante",
    "bandcamp": "bandcamp_dominante",
    "soundcloud": "soundcloud_dominante",
}


def _share_log(metricas: dict, señales: dict) -> tuple[dict[str, float], str]:
    """Reparto % por plataforma en escala log10 dentro de una dimensión.

    Devuelve (shares, patron). El patrón es 'sin_datos' si no hay señal, el
    nombre de la plataforma dominante si supera ~50% con diferencia clara, o
    'distribuido' cuando el peso está repartido.
    """
    brutos: dict[str, float] = {}
    for plataforma, tipos in señales.items():
        met = metricas.get(plataforma) or {}
        for tipo in tipos:
            valor = met.get(tipo)
            if _es_metrico(valor):
                brutos[plataforma] = float(valor)
                break
    if not brutos:
        return {}, "sin_datos"
    logs = {p: math.log10(v + 1.0) for p, v in brutos.items()}
    total = sum(logs.values())
    shares = {p: round(l / total * 100.0, 1) for p, l in logs.items()}
    shares = dict(sorted(shares.items(), key=lambda kv: kv[1], reverse=True))
    primero, primero_v = next(iter(shares.items()))
    segundo_v = (list(shares.values())[1] if len(shares) > 1 else 0.0)
    if primero_v >= 50.0 and primero_v - segundo_v >= 15.0:
        patron = NOMBRE_DIMENSION_PATRON.get(primero, "distribuido")
        return shares, patron
    return shares, "distribuido"


def dominancia_audiencia(metricas: dict) -> tuple[dict[str, float], str]:
    """Reparto de seguidores por red social (IG/FB/TT/YT/Spotify/Beatport/Mixcloud)
    y patrón resultante. Compara solo seguidores en escala log10."""
    return _share_log(metricas, MAPEO_AUDIENCIA)


def dominancia_consumo(metricas: dict) -> tuple[dict[str, float], str]:
    """Reparto de reproducciones/vistas entre plataformas musicales
    (YT/Spotify/Bandcamp/SoundCloud) y patrón resultante. Compara solo consumo
    en escala log10."""
    return _share_log(metricas, MAPEO_CONSUMO)


def balance_audiencia_consumo(metricas: dict) -> str:
    """Lectura global de la comparativa entre audiencia (seguidores) y consumo
    (reproducciones). Devuelve una clave legible para el texto combinado."""
    sociales = sum(
        _valor_seguro(metricas, p, "seguidores") for p in ("ig", "fb", "tt", "yt")
    )
    consumo = (
        _valor_seguro(metricas, "yt", "vistas")
        + _valor_seguro(metricas, "spotify", "reproducciones")
        + _valor_seguro(metricas, "spotify", "oyentes_mensuales")
        + _valor_seguro(metricas, "bandcamp", "reproducciones")
        + _valor_seguro(metricas, "soundcloud", "reproducciones")
    )
    if sociales <= 0 and consumo <= 0:
        return "sin_datos"
    if sociales <= 0 or consumo <= 0:
        return "parcial"
    ratio = consumo / sociales
    if ratio >= 10:
        return "consumo_dominante"
    if ratio >= 3:
        return "inclinado_consumo"
    if ratio >= 1 / 3:
        return "equilibrado"
    if ratio >= 1 / 10:
        return "inclinado_social"
    return "social_dominante"


TEXTO_BALANCE_AUDIENCIA_CONSUMO = {
    "consumo_dominante": (
        "El consumo (reproducciones y vistas) es claramente mayor que los "
        "seguidores registrados: la música se escucha más de lo que se sigue. "
        "La audiencia descubre y consume el contenido, pero aún hay oportunidad "
        "de convertir esas escuchas en comunidad."
    ),
    "inclinado_consumo": (
        "El consumo supera ligeramente a la audiencia social registrada. La "
        "gente consume la música, aunque la comunidad que la sigue es menor. "
        "Reforzar el vínculo entre escucha y seguidores ayudaría a fidelizar."
    ),
    "equilibrado": (
        "Audiencia y consumo están equilibrados: los seguidores que se acumulan "
        "en redes guardan proporción con las reproducciones que se generan. "
        "Una base sana sobre la que construir."
    ),
    "inclinado_social": (
        "Hay más seguidores que consumo registrado. La comunidad sigue al "
        "proyecto en redes, pero el consumo musical es menor: distribuir y "
        "enlazar la música desde los perfiles ayudaría a convertir seguidores "
        "en reproducciones."
    ),
    "social_dominante": (
        "La audiencia social (seguidores) supera ampliamente al consumo "
        "registrado. La comunidad sigue al proyecto en redes, pero la música "
        "apenas se reproduce: es el caso típico de perfil de influencia sin "
        "conversión musical todavía."
    ),
    "parcial": (
        "Solo hay señal en una de las dos dimensiones (audiencia o consumo), "
        "así que la comparativa está incompleta. Conecta más plataformas para "
        "tener una lectura equilibrada."
    ),
    "sin_datos": (
        "Aún no hay suficientes datos conectados para comparar audiencia y consumo."
    ),
}


def dominancia_plataforma(metricas: dict) -> dict[str, float]:
    """Porcentaje de dominancia de cada plataforma sobre el total.

    Usa la métrica de alcance de cada plataforma (seguidores, vistas,
    reproducciones) y calcula qué % representa del total combinado.
    Devuelve {plataforma: porcentaje} solo para las que tienen dato.

    Legado: mezcla unidades incomparables; se mantiene por compatibilidad pero
    el análisis nuevo usa `dominancia_audiencia`/`dominancia_consumo` por separado.
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


# ── Géneros dominantes (clasificación interna) ──────────────────────────

GENEROS_DOMINANTES = [
    "Regional Mexicano",
    "Rock",
    "Metal",
    "Urbano",
    "EDM",
    "Dark",
    "Pop",
    "Cumbia y Tropical",
    "Raíces",
]

# Mapeo de subgéneros conocidos → género dominante.
# Se busca el token más largo primero (ej. "hip hop" antes de "hop") para
# que nombres compuestos matcheen correctamente.
_CLASIFICACION_SUBGENERO: dict[str, str] = {
    # Regional Mexicano
    "norteño": "Regional Mexicano",
    "banda": "Regional Mexicano",
    "sierreño": "Regional Mexicano",
    "corridos tumbados": "Regional Mexicano",
    "corridos tropicales": "Regional Mexicano",
    "corridos": "Regional Mexicano",
    "tejano": "Regional Mexicano",
    "tex-mex": "Regional Mexicano",
    "grupero": "Regional Mexicano",
    "regional mexicano": "Regional Mexicano",
    "regional": "Regional Mexicano",
    # Híbridos cumbia-regional: se tocan en formato norteño/regional y
    # pertenecen a la familia Regional Mexicano (no a Cumbia y Tropical pura).
    "cumbia norteña": "Regional Mexicano",
    "cumbias bélicas": "Regional Mexicano",
    "cumbia bélica": "Regional Mexicano",
    # Rock
    "rock alternativo": "Rock",
    "rock en español": "Rock",
    "rock n roll": "Rock",
    "rock and roll": "Rock",
    "rock n' roll": "Rock",
    "rock progresivo": "Rock",
    "rock pop": "Rock",
    "hard rock": "Rock",
    "classic rock": "Rock",
    "garage rock": "Rock",
    "blues rock": "Rock",
    "southern rock": "Rock",
    "pop punk melancólico": "Rock",
    "pop punk": "Rock",
    "punk rock": "Rock",
    "post-rock": "Rock",
    "noise rock": "Rock",
    "dreampop": "Rock",
    "shoegaze": "Rock",
    "grunge": "Rock",
    "punk": "Rock",
    "indie": "Rock",
    "alternative": "Rock",
    "alternativa": "Rock",
    "emo": "Rock",
    "rock": "Rock",
    # Metal
    "industrial metal": "Metal",
    "metal progresivo": "Metal",
    "metal alternativo": "Metal",
    "death metal": "Metal",
    "nu metal": "Metal",
    "glam metal": "Metal",
    "metalcore": "Metal",
    "electronicore": "Metal",
    "melodic hardcore": "Metal",
    "hardcore": "Metal",
    "doom": "Metal",
    "stoner": "Metal",
    "sludge": "Metal",
    "metal": "Metal",
    # Urbano
    "música urbana": "Urbano",
    "latin hip hop": "Urbano",
    "narco rap": "Urbano",
    "hip hop": "Urbano",
    "hip-hop": "Urbano",
    "reggaetón": "Urbano",
    "reggaeton": "Urbano",
    "emo trap": "Urbano",
    "freestyle": "Urbano",
    "trap": "Urbano",
    "rap": "Urbano",
    "r&b": "Urbano",
    # EDM
    "electronic drone": "EDM",
    "progressive house": "EDM",
    "drum and bass": "EDM",
    "deep house": "EDM",
    "bass house": "EDM",
    "tech house": "EDM",
    "hyperpop industrial": "EDM",
    "hyperpop": "EDM",
    "electrónica": "EDM",
    "electronica": "EDM",
    "electrónico": "EDM",
    "electronic": "EDM",
    "dubstep": "EDM",
    "trance": "EDM",
    "techno": "EDM",
    "hardstyle": "EDM",
    "riddim": "EDM",
    "house": "EDM",
    "acid": "EDM",
    # Dark
    "post-punk": "Dark",
    "post punk": "Dark",
    "darkwave": "Dark",
    "dark wave": "Dark",
    "coldwave": "Dark",
    "cold wave": "Dark",
    "industrial": "Dark",
    "dark electro": "Dark",
    "cybercore": "Dark",
    "goth rock": "Dark",
    "synthpop": "Dark",
    "synth pop": "Dark",
    "new wave": "Dark",
    "drone": "Dark",
    # Pop
    "latin pop": "Pop",
    "pop romantico": "Pop",
    "pop rock": "Pop",
    "pop": "Pop",
    # Cumbia y Tropical
    "cumbia tropical": "Cumbia y Tropical",
    "cumbia villera": "Cumbia y Tropical",
    "world music": "Cumbia y Tropical",
    "afrobeat": "Cumbia y Tropical",
    "tropical": "Cumbia y Tropical",
    "cumbia": "Cumbia y Tropical",
    "reggae": "Cumbia y Tropical",
    "salsa": "Cumbia y Tropical",
    "ska": "Cumbia y Tropical",
    # Raíces
    "jazz": "Raíces",
    "blues": "Raíces",
    "soul": "Raíces",
    "funk": "Raíces",
    "folk": "Raíces",
    "trova": "Raíces",
    "country": "Raíces",
}

# Orden de búsqueda: tokens más largos primero para que "hip hop" matchee
# antes que un substring suelto.
_ORDEN_CLASIFICACION = sorted(
    _CLASIFICACION_SUBGENERO.keys(), key=len, reverse=True
)

# Excepciones editoriales por slug: el conteo automático no captura la base
# real de ciertos artistas (ej. Apex Ultra pone "Rock" primero pero su base
# es industrial/Dark). Se resuelven manualmente y se documentan aquí.
EXCEPCIONES_GENERO_DOMINANTE: dict[str, str] = {
    "apex_ultra": "Dark",
    "angelic_oz": "Urbano",
    "de_regreso_a_nocheosfera": "Dark",
    "anidonia": "Dark",
}


def clasificar_genero_dominante(slug: str, generos: str) -> str:
    """Clasifica el género dominante de un artista a partir de sus subgéneros.

    Divide por `/`, `,` o `()` y busca cada token en el diccionario de
    clasificación. Al haber empate gana el género que aparece primero (el
    artista declara su base primero). `slug` permite aplicar sobre-escrituras
    editoriales (`EXCEPCIONES_GENERO_DOMINANTE`). Devuelve el nombre del género
    dominante o `""` si no hay coincidencia.
    """
    if slug in EXCEPCIONES_GENERO_DOMINANTE:
        return EXCEPCIONES_GENERO_DOMINANTE[slug]

    generos = str(generos or "").strip()
    if not generos or generos == "[PENDIENTE]":
        return ""

    tokens = re.split(r"[/,()]", generos)
    conteo: dict[str, int] = {}
    orden: dict[str, int] = {}
    for pos, token in enumerate(tokens):
        token = token.strip().lower()
        if not token or token == "[pendiente]":
            continue
        for subgenero in _ORDEN_CLASIFICACION:
            if subgenero in token:
                dominante = _CLASIFICACION_SUBGENERO[subgenero]
                conteo[dominante] = conteo.get(dominante, 0) + 1
                orden.setdefault(dominante, pos)
                break

    if not conteo:
        return ""
    maximo = max(conteo.values())
    candidatos = [g for g, n in conteo.items() if n == maximo]
    if len(candidatos) == 1:
        return candidatos[0]
    return min(candidatos, key=lambda g: orden[g])


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


# Clasificación por índice universal (techos de referencia fijos)
# Cada señal se normaliza contra un techo mundial absoluto (no contra el máximo
# local de la escena, que inflaba números semilla como seguidores de FB):
# IG/FB/TT/YT seguidores 50M · YT vistas 10B · Spotify oyentes 50M · Spotify
# seguidores 20M · Spotify reproducciones 1B · SoundCloud 10M · Bandcamp 1M ·
# Beatport 100K · Mixcloud 50K.
TECHOS_REFERENCIA: dict[tuple[str, str], float] = {
    ("ig", "seguidores"): 50_000_000,
    ("fb", "seguidores"): 50_000_000,
    ("tt", "seguidores"): 50_000_000,
    ("yt", "seguidores"): 50_000_000,
    ("yt", "vistas"): 10_000_000_000,
    ("spotify", "seguidores"): 20_000_000,
    ("spotify", "oyentes_mensuales"): 50_000_000,
    ("spotify", "reproducciones"): 1_000_000_000,
    ("soundcloud", "reproducciones"): 10_000_000,
    ("bandcamp", "reproducciones"): 1_000_000,
    ("beatport", "seguidores"): 100_000,
    ("mixcloud", "seguidores"): 50_000,
}

# Señales de audiencia social "comprable" (la normalizan la regla anti-trampa).
SEÑALES_SOCIALES = {"ig", "fb", "tt"}

# Señales de consumo real (lo que evidencia que la gente consume la música).
SEÑALES_CONSUMO = {
    ("yt", "vistas"),
    ("spotify", "oyentes_mensuales"),
    ("spotify", "reproducciones"),
    ("soundcloud", "reproducciones"),
    ("bandcamp", "reproducciones"),
}

# Regla anti-trampa: la audiencia social (IG/FB/TT) no puede exceder el consumo
# real × este factor (audiencia comprada o perfil de influencer no infla el índice).
FACTOR_COHERENCIA_AUDIENCIA = 3.0

# Descuento 2026-08 (shorts): el `viewCount` del canal de YouTube (viewCount de la
# Data API) incluye Shorts y puede inflarse fácilmente. Por eso, para los índices
# de clasificación y ranking de alcance las vistas de YouTube cuentan al 60%
# (reduce su "capacidad" relativa frente al resto de señales, sin tocar la cifra
# cruda que se muestra en el perfil).
FACTOR_CAPACIDAD_VISTAS_YT = 0.6

# Índice híbrido: 70% la señal dominante (mejor ratio) + 30% cobertura (media).
PESO_SEÑAL_DOMINANTE = 0.7
PESO_COBERTURA = 0.3

# Umbrales fijos de clasificación (documentados en AGENTS.md y en la web):
UMBRAL_LIGAS_MAYORES = 60.0   # ≥ 60 = Ligas Mayores
UMBRAL_EN_ASCENSO = 50.0      # ≥ 50 = En Ascenso


def _ratio_frente_techo(valor: float, techo: float) -> float:
    """Ratio 0-1 de un valor contra su techo de referencia (escala log10)."""
    if not _es_metrico(valor) or valor <= 0:
        return 0.0
    return min(1.0, math.log10(float(valor) + 1.0) / math.log10(float(techo) + 1.0))


def calcular_indice_universal(
    metricas_por_artista: dict[str, dict],
) -> dict[str, float]:
    """Índice universal 0-100 normalizado contra techos de referencia fijos.

    Para cada artista se calcula el ratio de cada señal contra su techo mundial
    (escala log10). El índice híbrido combina el 70% de la señal dominante
    (la mejor ratio) con el 30% de cobertura (media de ratios, contar 0 las
    señales ausentes penaliza no tener la plataforma). La regla anti-trampa
    limita las señales sociales (IG/FB/TT) a `consumo real × 3` cuando existe
    consumo registrado, para que una audiencia comprada o el perfil de un
    influencer no inflen el índice. No se expone públicamente (solo admin);
    los rankings visibles (Ligas/Rookies) se normalizan dentro de cada grupo.
    """
    resultado: dict[str, float] = {}
    for slug, metricas in metricas_por_artista.items():
        ratios: list[tuple[tuple[str, str], float]] = []
        consumo_max = 0.0
        for señal, techo in TECHOS_REFERENCIA.items():
            plataforma, tipo = señal
            if plataforma == "yt" and tipo == "vistas":
                valor = _vistas_yt_capacidad(metricas)
            else:
                valor = _valor_seguro(metricas, plataforma, tipo)
            ratio = _ratio_frente_techo(valor, techo)
            ratios.append((señal, ratio))
            if señal in SEÑALES_CONSUMO and ratio > 0:
                consumo_max = max(consumo_max, ratio)

        # Anti-trampa: límite a las señales sociales cuando hay consumo real.
        if consumo_max > 0:
            tope_social = consumo_max * FACTOR_COHERENCIA_AUDIENCIA
            ratios = [
                (señal, min(ratio, tope_social) if plataforma in SEÑALES_SOCIALES else ratio)
                for (señal, ratio) in ratios
                for plataforma in [señal[0]]
            ]

        dominante = max((ratio for _, ratio in ratios), default=0.0)
        if dominante <= 0:
            resultado[slug] = 0.0
            continue
        cobertura = sum(ratio for _, ratio in ratios) / len(ratios)
        resultado[slug] = round(
            (PESO_SEÑAL_DOMINANTE * dominante + PESO_COBERTURA * cobertura) * 100.0,
            1,
        )
    return resultado


def clasificar_por_indice(
    indice_universal: dict[str, float],
    umbral_ligas: float = UMBRAL_LIGAS_MAYORES,
    umbral_ascenso: float = UMBRAL_EN_ASCENSO,
) -> dict[str, str]:
    """Clasifica artistas en tres niveles según umbrales fijos del índice.

    Args:
        indice_universal: {slug: índice 0-100} calculado contra techos fijos.
        umbral_ligas: Índice mínimo para Ligas Mayores (≥ 60).
        umbral_ascenso: Índice mínimo para En Ascenso (≥ 50).

    Returns:
        {slug: "Ligas Mayores" | "En Ascenso" | ""}

    Los umbrales son absolutos y no dependen de la distribución de la escena:
    quien supera el umbral lo supera aunque la escena crezca. Nota: "Leyenda de
    la Frontera" se gestiona aparte (flag editorial `es_leyenda`).
    """
    resultado: dict[str, str] = {}
    for slug, idx in indice_universal.items():
        if idx >= umbral_ligas:
            resultado[slug] = "Ligas Mayores"
        elif idx >= umbral_ascenso:
            resultado[slug] = "En Ascenso"
        else:
            resultado[slug] = ""
    return resultado
