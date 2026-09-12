"""Servicios de aplicación de la escena local.

Reúnen la lógica de dominio que consume la API: read-models (DataFrames),
feed unificado, métricas por plataforma y ranking de alcance. No tocan SQL
directo: delegan en `lib.repository`.
"""

import hashlib
import os
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import ESTADOS_ACTIVO, NIVELES, Artist, ActivityCheck, AltaRegistro
from lib.helpers import (
    TIPOS_FEED,
    TEXTO_BALANCE_AUDIENCIA_CONSUMO,
    GENEROS_DOMINANTES,
    balance_audiencia_consumo,
    calcular_indice_universal,
    clasificar_genero_dominante,
    clasificar_por_indice,
    conteo_generos,
    dominancia_audiencia,
    dominancia_consumo,
    ratio_engagement_spotify,
    ratio_social_musica,
    ratio_viralidad_yt,
    youtube_thumbnail,
)
from lib.repository import (
    ArtistRepository,
    ChecksRepository,
    EventRepository,
    FeedRepository,
    LinkRepository,
    SpotifySnapshotRepository,
)

TIPOS_FEED_CONTENIDO = ("video", "lanzamiento", "post", "evento")


def artistas_df(session: Session) -> pd.DataFrame:
    """DataFrame plano de artistas para tablas y gráficas.

    Incluye índice universal (0-100 contra TODOS) y clasificación on-the-fly
    (nivel_calculado) para separar Ligas vs Escena (base). El índice universal
    es solo para clasificación/admin; los rankings visibles se normalizan
    independientemente por grupo.
    """
    filas = [
        {
            "id": a.id,
            "slug": a.slug,
            "nombre": a.nombre,
            "segmento": a.segmento,
            "ciudad": a.ciudad,
            "generos": a.generos,
            "genero_dominante": a.genero_dominante,
            "estado_registro": a.estado_registro,
            "es_propio": a.es_propio,
            "nivel": a.nivel,
            "es_leyenda": a.es_leyenda,
            "estado_activo": a.estado_activo,
            "metodo_actividad": a.metodo_actividad,
            "ultimo_lanzamiento": a.ultimo_lanzamiento,
            "ultimo_evento": a.ultimo_evento,
            "followers_ig": a.followers_ig,
            "followers_fb": a.followers_fb,
            "followers_yt": a.followers_yt,
            "followers_tt": a.followers_tt,
            "followers_spotify": a.followers_spotify,
            "followers_beatport": a.followers_beatport,
            "followers_mixcloud": a.followers_mixcloud,
            "followers_soundcloud": a.followers_soundcloud,
            "oyentes_mensuales_spotify": a.oyentes_mensuales_spotify,
            "fecha_oyentes_spotify": a.fecha_oyentes_spotify,
            "vistas_yt": a.vistas_yt,
            "vistas_tt": a.vistas_tt,
            "reproducciones_spotify": a.reproducciones_spotify,
            "reproducciones_bandcamp": a.reproducciones_bandcamp,
            "reproducciones_soundcloud": a.reproducciones_soundcloud,
            "logros": a.logros,
            "notas": a.notas,
            "fecha_registro": a.fecha_registro,
            "fecha_creacion": a.created_at,
            "imagen_perfil": a.imagen_perfil,
            "imagen_origen": a.imagen_origen,
        }
        for a in ArtistRepository(session).todos(con_links=False)
    ]
    df = pd.DataFrame(filas)
    if df.empty:
        df["nivel"] = pd.Series(dtype=str)
        df["es_leyenda"] = pd.Series(dtype=bool)
        df["nivel_calculado"] = pd.Series(dtype=str)
        df["indice_universal"] = pd.Series(dtype=float)
        return df

    df["nivel"] = df["nivel"].fillna("").astype(str)
    df["es_leyenda"] = df["es_leyenda"].fillna(False).astype(bool)

    # Índice universal (0-100 contra techos fijos) - solo para clasificación/admin
    metricas = {fila["slug"]: metricas_artista(fila) for _, fila in df.iterrows()}
    indice_universal = calcular_indice_universal(metricas)
    df["indice_universal"] = df["slug"].map(indice_universal).fillna(0.0)

    # Clasificación on-the-fly por umbrales fijos del índice universal
    clasificacion = clasificar_por_indice(indice_universal)
    # Leyenda manual tiene prioridad
    for slug, es_leyenda in df.set_index("slug")["es_leyenda"].items():
        if es_leyenda:
            clasificacion[slug] = "Leyenda de la Frontera"
    df["nivel_calculado"] = df["slug"].map(clasificacion).fillna("")

    return df


def eventos_de_artista(session: Session, nombre: str) -> pd.DataFrame:
    """Eventos de la escena en cuyo cartel aparece el artista."""
    filas = [
        {
            "fecha": e.fecha,
            "nombre": e.nombre,
            "lugar": e.lugar,
            "ciudad": e.ciudad,
            "artistas": e.artistas,
            "que_demuestra": e.que_demuestra,
        }
        for e in EventRepository(session).de_artista(nombre)
    ]
    return pd.DataFrame(filas)


def ultimo_feed_de_artista(session: Session, artist: Artist) -> date | None:
    """Fecha del elemento de contenido más reciente del feed de un artista.

    Solo cuenta contenido real (video, lanzamiento, post, evento), no
    chequeos ni errores. Usa la fecha de publicación; si no la tiene,
    la de creación del registro.
    """
    item = FeedRepository(session).ultimo_contenido_de_artista(artist.id)
    if item is None:
        return None
    return (item.fecha or item.created_at).date()


def feed_df(
    session: Session, limite: int = 60, artista: str | None = None
) -> pd.DataFrame:
    """Feed unificado: contenido scrapeado + eventos + lanzamientos + chequeos.

    Con `artista` se filtra todo a ese proyecto (feed del perfil); sin él,
    es el feed global. El tope `limite` aplica al resultado final. La fuente
    se normaliza a la clave canónica (ej. `youtube` → `yt`) para que la API
    nunca exponga aliases duplicados.
    """
    from lib.plataformas import FUENTE_CANONICA

    feed_repo = FeedRepository(session)
    artist_repo = ArtistRepository(session)
    artista_id: int | None = None
    if artista is not None:
        artista_encontrado = artist_repo.por_nombre(artista)
        artista_id = artista_encontrado.id if artista_encontrado else None

    filas = []

    feed_items = (
        feed_repo.de_artista_desc(artista_id, limite=limite * 2)
        if artista_id is not None
        else feed_repo.todos_desc(limite=limite * 2)
    )
    for fi in feed_items:
        nombre_art = fi.artist.nombre if fi.artist else ""
        if artista is not None and nombre_art != artista:
            continue
        imagen = fi.imagen or (
            youtube_thumbnail(fi.url) if fi.fuente == "yt" else ""
        )
        filas.append(
            {
                "fecha": fi.fecha,
                "tipo": TIPOS_FEED.get(fi.tipo, fi.tipo),
                "tipo_bruto": fi.tipo,
                "fuente": FUENTE_CANONICA.get(fi.fuente, fi.fuente),
                "titulo": fi.titulo,
                "url": fi.url,
                "imagen": imagen,
                "detalle": fi.detalle,
                "artista_id": fi.artist_id,
                "artista": nombre_art,
                "artista_slug": fi.artist.slug if fi.artist else "",
                "imagen_artista": fi.artist.imagen_perfil if fi.artist else None,
            }
        )

    eventos = (
        EventRepository(session).de_artista(artista)
        if artista is not None
        else EventRepository(session).todos_fecha_desc()
    )
    for e in eventos:
        if e.fecha is None:
            continue
        detalle = " · ".join(
            parte for parte in (e.lugar, e.artistas, e.que_demuestra) if parte
        )
        filas.append(
            {
                "fecha": e.fecha,
                "tipo": TIPOS_FEED["evento"],
                "tipo_bruto": "evento",
                "fuente": "escena",
                "titulo": e.nombre,
                "url": None,
                "imagen": "",
                "detalle": detalle,
                "artista_id": None,
                "artista": artista or "",
                "artista_slug": "",
                "imagen_artista": None,
            }
        )

    artistas_con_lanzamiento = (
        [a for a in artist_repo.todos(con_links=False) if a.nombre == artista]
        if artista is not None
        else artist_repo.con_lanzamiento()
    )
    for a in artistas_con_lanzamiento:
        filas.append(
            {
                "fecha": a.ultimo_lanzamiento,
                "tipo": TIPOS_FEED["lanzamiento"],
                "tipo_bruto": "lanzamiento",
                "fuente": "registro",
                "titulo": f"{a.nombre} — lanzamiento",
                "url": None,
                "imagen": "",
                "detalle": a.logros[:240],
                "artista_id": a.id,
                "artista": a.nombre,
                "artista_slug": a.slug,
                "imagen_artista": a.imagen_perfil,
            }
        )

    chequeos = (
        ChecksRepository(session).ultimos_de_artista(artista_id, limite=30)
        if artista_id is not None
        else ChecksRepository(session).ultimos(30)
    )
    for c in chequeos:
        nombre = c.artist.nombre if c.artist else ""
        filas.append(
            {
                "fecha": c.fecha_chequeo,
                "tipo": TIPOS_FEED.get("error") if c.resultado == "error" else "🕸️ Chequeo",
                "tipo_bruto": "chequeo",
                "fuente": "scraper",
                "titulo": f"{nombre} — {c.plataforma}" if nombre else c.plataforma,
                "url": None,
                "imagen": "",
                "detalle": f"{c.metodo}: {c.resultado}",
                "artista_id": c.artist_id,
                "artista": nombre,
                "artista_slug": c.artist.slug if c.artist else "",
                "imagen_artista": c.artist.imagen_perfil if c.artist else None,
            }
        )

    if not filas:
        return pd.DataFrame()
    df = pd.DataFrame(filas)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"]).sort_values("fecha", ascending=False)
    return df.head(limite)


def metricas_artista(fila) -> dict:
    """Métricas por plataforma de una fila del DataFrame de artistas."""
    metricas = {
        "ig": {"seguidores": fila["followers_ig"]},
        "fb": {"seguidores": fila["followers_fb"]},
        "yt": {
            "seguidores": fila["followers_yt"],
            "vistas": fila["vistas_yt"],
        },
        "tt": {
            "seguidores": fila["followers_tt"],
            "vistas": fila["vistas_tt"],
        },
        "spotify": {
            "seguidores": fila["followers_spotify"],
        },
        "bandcamp": {"reproducciones": fila["reproducciones_bandcamp"]},
        "soundcloud": {
            "seguidores": fila["followers_soundcloud"],
            "reproducciones": fila["reproducciones_soundcloud"],
        },
        "beatport": {"seguidores": fila["followers_beatport"]},
        "mixcloud": {"seguidores": fila["followers_mixcloud"]},
    }
    oyentes = fila["oyentes_mensuales_spotify"]
    if pd.notna(oyentes):
        metricas["spotify"]["oyentes_mensuales"] = oyentes
        metricas["spotify"]["fecha_captura"] = fila["fecha_oyentes_spotify"]
    return metricas


def analisis_artista(metricas: dict, actualizado=None) -> dict:
    """Genera una lectura breve y neutral de las señales del perfil.

    No mezcla vistas, reproducciones y seguidores en una sola cifra. Usa los
    seguidores para comparar presencia social contra audiencia musical y deja
    las reproducciones como evidencia adicional de presencia en plataformas.
    """

    def valor(plataforma: str, tipo: str) -> float:
        dato = metricas.get(plataforma, {}).get(tipo)
        try:
            numero = float(dato)
        except (TypeError, ValueError):
            return 0.0
        return numero if numero > 0 else 0.0

    sociales = sum(
        valor(plataforma, "seguidores") for plataforma in ("ig", "fb", "tt", "yt")
    )
    oyentes_spotify = valor("spotify", "oyentes_mensuales")
    audiencia_musical = oyentes_spotify or valor("spotify", "seguidores")
    audiencia_musical += sum(
        valor(plataforma, "seguidores") for plataforma in ("beatport", "mixcloud")
    )
    consumo_registrado = any(
        valor(plataforma, tipo) > 0
        for plataforma, tipo in (
            ("yt", "vistas"),
            ("spotify", "oyentes_mensuales"),
            ("bandcamp", "reproducciones"),
            ("soundcloud", "reproducciones"),
        )
    )
    plataformas_con_datos = sum(
        any(valor(plataforma, tipo) > 0 for tipo in datos)
        for plataforma, datos in (
            ("ig", ("seguidores",)),
            ("fb", ("seguidores",)),
            ("tt", ("seguidores",)),
            ("yt", ("seguidores", "vistas")),
            ("spotify", ("seguidores", "oyentes_mensuales")),
            ("bandcamp", ("reproducciones",)),
            ("soundcloud", ("reproducciones",)),
            ("beatport", ("seguidores",)),
            ("mixcloud", ("seguidores",)),
        )
    )

    if plataformas_con_datos < 2:
        texto = "Aún hay pocos datos conectados para generar un análisis confiable."
        confianza = "baja"
        tipo = "datos_insuficientes"
    elif sociales >= 100 and audiencia_musical == 0:
        if consumo_registrado:
            texto = (
                "La audiencia registrada se concentra en redes sociales; hay "
                "consumo musical o audiovisual, pero todavía no una métrica de audiencia "
                "comparable entre ambas presencias."
            )
        else:
            texto = (
                "La audiencia registrada se concentra en redes sociales; todavía no "
                "hay una señal musical suficiente para comparar ambas presencias."
            )
        confianza = "media"
        tipo = "presencia_social"
    elif sociales >= audiencia_musical * 10 and sociales >= 100:
        texto = (
            "La mayor audiencia registrada proviene de redes sociales, mientras "
            "que la presencia musical es menor. Existe oportunidad para fortalecer "
            "el vínculo entre ambas plataformas."
        )
        confianza = "alta"
        tipo = "puente_musical"
    elif audiencia_musical >= sociales * 2 and audiencia_musical >= 100:
        texto = (
            "Las plataformas musicales concentran la mayor audiencia registrada; "
            "las redes sociales representan una oportunidad para ampliar el descubrimiento."
        )
        confianza = "media"
        tipo = "descubrimiento"
    else:
        texto = (
            "La presencia registrada está distribuida entre plataformas sociales "
            "y musicales, sin una diferencia dominante entre ambas."
        )
        confianza = "media"
        tipo = "presencia_distribuida"

    return {
        "texto": texto,
        "tipo": tipo,
        "confianza": confianza,
        "actualizado": actualizado,
    }


def analisis_consumo(metricas: dict) -> dict:
    """Análisis de audiencia y consumo por plataforma (balanceado).

    Separa las dos dimensiones que antes se mezclaban en una sola cifra
    sesgada hacia YouTube:
    - Audiencia: reparto de seguidores entre redes sociales (IG/FB/TT/YT/Spotify).
    - Consumo: reparto de reproducciones/vistas entre plataformas musicales.

    Cada dimensión compara solo unidades equivalentes en escala log10. Además
    devuelve una lectura global que compara audiencia contra consumo y los
    ratios derivados de siempre.
    """
    shares_audiencia, patron_aud = dominancia_audiencia(metricas)
    shares_consumo, patron_consumo = dominancia_consumo(metricas)
    balance = balance_audiencia_consumo(metricas)
    viralidad_yt = ratio_viralidad_yt(metricas)
    engagement_sp = ratio_engagement_spotify(metricas)
    gap_social = ratio_social_musica(metricas)

    return {
        "patron": patron_consumo,
        "texto": TEXTO_BALANCE_AUDIENCIA_CONSUMO.get(
            balance, TEXTO_BALANCE_AUDIENCIA_CONSUMO["sin_datos"]
        ),
        "balance": balance,
        "audiencia": {
            "patron": patron_aud,
            "dominancia": shares_audiencia,
        },
        "consumo": {
            "patron": patron_consumo,
            "dominancia": shares_consumo,
        },
        "ratios": {
            "viralidad_yt": viralidad_yt,
            "engagement_spotify": engagement_sp,
            "gap_social_musica": gap_social,
        },
        "dominancia": shares_consumo,
    }


def _agregar_grupo_mencion(
    menciones: dict[str, list[str]],
    indices: dict[str, float],
    nombre: str,
    slugs: list[str],
    formato: str,
) -> None:
    if len(slugs) < 3:
        return
    ordenados = sorted(
        ((indices.get(s, 0.0), s) for s in slugs),
        key=lambda x: x[0],
        reverse=True,
    )
    for puesto, (indice, slug) in enumerate(ordenados[:3], start=1):
        if indice <= 0:
            break
        menciones.setdefault(slug, []).append(
            formato.format(puesto=puesto, grupo=nombre, n=len(slugs))
        )


def menciones_ranking(df: pd.DataFrame, indices: dict[str, float]) -> dict[str, list[str]]:
    """Menciones especiales de ranking.

    Devuelve {slug: [texto, ...]} con el Top 3 de la Frontera Grande (ranking global)
    y el Top 3 de cada grupo (género/ciudad/segmento) con al menos 3 artistas
    y puntaje real. Solo algunos artistas tienen menciones.
    """
    menciones: dict[str, list[str]] = {}

    por_genero: dict[str, list[str]] = {}
    por_ciudad: dict[str, list[str]] = {}
    por_segmento: dict[str, list[str]] = {}
    for _, fila in df.iterrows():
        genero_dominante = fila.get("genero_dominante") or ""
        if genero_dominante and "PENDIENTE" not in genero_dominante.upper():
            por_genero.setdefault(genero_dominante, []).append(fila["slug"])
        if fila["ciudad"] and "PENDIENTE" not in str(fila["ciudad"]).upper():
            por_ciudad.setdefault(fila["ciudad"], []).append(fila["slug"])
        if fila["segmento"] and "PENDIENTE" not in str(fila["segmento"]).upper():
            por_segmento.setdefault(fila["segmento"], []).append(fila["slug"])

    globales = sorted(indices.items(), key=lambda x: x[1], reverse=True)
    for puesto, (slug, indice) in enumerate(globales[:3], start=1):
        if indice <= 0:
            break
        menciones.setdefault(slug, []).append(
            f"Nº {puesto} de la Frontera Grande"
        )

    for genero, slugs in por_genero.items():
        _agregar_grupo_mencion(menciones, indices, genero, slugs, "Nº {puesto} del género {grupo}")
    for ciudad, slugs in por_ciudad.items():
        _agregar_grupo_mencion(menciones, indices, ciudad, slugs, "Nº {puesto} de {grupo}")
    for segmento, slugs in por_segmento.items():
        _agregar_grupo_mencion(menciones, indices, segmento, slugs, "Nº {puesto} de la categoría {grupo}")

    return menciones


# Las 4 ligas de la escena: la Escena (base) es una liga más.
LIGAS_ORDEN = ["Escena", "Emergente", "Ligas Mayores", "Leyenda de la Frontera"]


def liga_de_nivel(nivel_calculado: str) -> str:
    """Nombre de liga de un `nivel_calculado` (la Escena es la base `""`)."""
    nivel = (nivel_calculado or "").strip()
    if not nivel:
        return "Escena"
    return nivel if nivel in LIGAS_ORDEN else "Escena"


def ranking_por_ligas(
    df: pd.DataFrame,
) -> tuple[dict[str, dict], dict[str, list[str]], dict[str, dict]]:
    """Ranking de alcance por cada una de las 4 ligas + ranking universal.

    La posición dentro de cada liga (`rank_liga`) y la posición del ranking
    universal (`rank_universal`) se derivan del **índice universal** (techos
    fijos, comparable entre todas las ligas, opción B): no se re-normaliza por
    liga, así la comparación entre ligas es coherente.

    Devuelve (ranking, menciones, ligas_meta):
      - ranking: {slug: {indice, audiencia, consumo, liga, rank_liga,
                          total_liga, rank_universal, total_universal}}
      - menciones: {slug: [texto]} con las menciones competitivas **dentro de
        la liga propia** del artista (categoría/género/ciudad, Nº de la Frontera).
      - ligas_meta: {liga: {"rank": {slug: puesto}, "total": int}}
    """
    from lib.helpers import indices_audiencia_consumo

    metricas = {fila["slug"]: metricas_artista(fila) for _, fila in df.iterrows()}
    indices = indices_audiencia_consumo(metricas)

    # Liga por artista y sub-DataFrames por liga.
    liga_por_slug: dict[str, str] = {}
    df_por_liga: dict[str, list[pd.DataFrame]] = {}
    for _, fila in df.iterrows():
        liga = liga_de_nivel(str(fila.get("nivel_calculado") or ""))
        liga_por_slug[fila["slug"]] = liga
        df_por_liga.setdefault(liga, []).append(fila)
    por_liga: dict[str, pd.DataFrame] = {
        liga: pd.DataFrame(filas) for liga, filas in df_por_liga.items()
    }

    # Índice universal ya calculado en `artistas_df`.
    indice_universal = {
        _s: float(fila.get("indice_universal") or 0.0)
        for _, fila in df.iterrows()
        for _s in [fila["slug"]]
    }

    # Posición universal: todos ordenados por índice universal.
    universo_ordenado = sorted(
        indice_universal.items(), key=lambda x: x[1], reverse=True
    )
    rank_universal = {
        slug: i + 1 for i, (slug, _) in enumerate(universo_ordenado)
    }
    total_universal = len(universo_ordenado)

    # Posición por liga y menciones dentro de cada liga.
    rank_por_liga: dict[str, dict[str, int]] = {}
    menciones: dict[str, list[str]] = {}
    for liga, sub_df in por_liga.items():
        indices_liga = {
            slug: indice_universal[slug]
            for slug in sub_df["slug"]
        }
        ordenados = sorted(
            indices_liga.items(), key=lambda x: x[1], reverse=True
        )
        rank_por_liga[liga] = {
            slug: i + 1 for i, (slug, _) in enumerate(ordenados)
        }
        menciones.update(
            menciones_ranking(sub_df, indices_liga)
        )

    ligas_meta: dict[str, dict] = {}
    for liga, rank in rank_por_liga.items():
        ligas_meta[liga] = {"rank": rank, "total": len(rank)}

    ranking: dict[str, dict] = {}
    for _, fila in df.iterrows():
        slug = fila["slug"]
        valores = indices.get(slug, {"indice": 0.0, "audiencia": 0.0, "consumo": 0.0})
        liga = liga_por_slug[slug]
        ranking[slug] = {
            "indice": valores["indice"],
            "audiencia": valores["audiencia"],
            "consumo": valores["consumo"],
            "liga": liga,
            "rank_liga": rank_por_liga[liga][slug],
            "total_liga": len(rank_por_liga[liga]),
            "rank_universal": rank_universal[slug],
            "total_universal": total_universal,
        }

    return ranking, menciones, ligas_meta


def _ranking_de(df: pd.DataFrame) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Ranking de alcance y menciones sobre un subconjunto del df.

    Normaliza las métricas entre ese subconjunto (no contra toda la escena),
    así el ranking de Ligas es independiente del de la escena local.
    """
    from lib.helpers import indices_audiencia_consumo

    metricas = {fila["slug"]: metricas_artista(fila) for _, fila in df.iterrows()}
    indices = indices_audiencia_consumo(metricas)
    ordenados = sorted(indices.items(), key=lambda x: x[1]["indice"], reverse=True)
    ranking = {
        slug: {
            "indice": valores["indice"],
            "audiencia": valores["audiencia"],
            "consumo": valores["consumo"],
            "rank": i + 1,
            "total": len(ordenados),
        }
        for i, (slug, valores) in enumerate(ordenados)
    }
    menciones = menciones_ranking(
        df, {slug: valores["indice"] for slug, valores in indices.items()}
    )
    return ranking, menciones


def ranking_global(df: pd.DataFrame) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Ranking de alcance y menciones de la escena local (Escena).

    Solo participan los artistas sin nivel calculado (`nivel_calculado == ""`).
    Los catalogados (Ligas Mayores / Emergente / Leyenda de la Frontera) van
    al ranking de Ligas.
    """
    base = df[df["nivel_calculado"].fillna("") == ""]
    return _ranking_de(base)


def ranking_ligas(df: pd.DataFrame) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Ranking de alcance de los artistas catalogados en Ligas.

    Agrupa juntos a Ligas Mayores, Emergente y Leyenda de la Frontera en una
    gráfica aparte (no se subdividen por ahora). Devuelve el ranking y las
    menciones normalizados solo entre ellos.
    """
    catalogados = df[df["nivel_calculado"].fillna("") != ""]
    return _ranking_de(catalogados)


CATEGORIAS_VALIDAS = ("Banda", "Solista", "DJ", "Colectivo", "Covers", "Tributo")


def _serie_mensual(fechas, meses: int = 12) -> list[dict]:
    """Conteo por mes de una serie de fechas (últimos `meses` meses).

    Devuelve una fila por mes en orden cronológico con `mes` (YYYY-MM),
    `año` y `conteo`; los meses sin datos van con 0 para no romper la serie.
    """
    ultimo = pd.Timestamp.today().to_period("M")
    periodos = [ultimo - i for i in range(meses - 1, -1, -1)]
    serie = pd.Series(pd.to_datetime(fechas, errors="coerce")).dropna()
    agrupado = serie.dt.to_period("M").value_counts()
    return [
        {"mes": str(p), "año": p.year, "conteo": int(agrupado.get(p, 0))}
        for p in periodos
    ]


def _etiqueta_registro(estado: str) -> str:
    """Etiqueta corta del estado de registro para agrupar en stats.

    Normaliza los estados `confirmado (artista, YYYY-MM-DD)` (que llevan la
    fecha de la conexión OAuth) a `confirmado (artista)` para que el conteo
    agrupe a todos los perfiles reclamados por el propio artista.
    """
    if estado and estado.startswith("confirmado (artista"):
        return "confirmado (artista)"
    if estado == "agregado (formulario)":
        return "registrado (formulario, sin conectar)"
    return estado or "sin dato"


def stats_escena(session: Session) -> dict:
    """Indicadores completos de la escena para el panel de stats.

    Todo se calcula con fuente (DataFrames semilla o repositorios): además de
    los conteos básicos, la huella digital agregada por plataforma, la
    cobertura (% de proyectos con cada red), la actividad mensual del feed,
    las altas por mes y la última alta registrada. Caller: `GET /api/stats`.
    """
    feed_repo = FeedRepository(session)
    df = artistas_df(session)
    if df.empty:
        return {
            "total": 0,
            "verificados": 0,
            "generos": {},
            "estados": {},
            "estados_registro": {},
            "ciudades": {},
            "segmentos": {},
            "feed_serie": [],
            "altas_por_mes": [],
            "seguidores": {},
            "reproducciones": {},
            "cobertura": {},
            "posts_90dias": 0,
            "por_ciudad": [],
            "ultima_alta": None,
        }

    total = len(df)
    generos = conteo_generos(df).head(15).to_dict()
    estados = df["estado_activo"].value_counts().to_dict()
    ciudades = df["ciudad"].value_counts().to_dict()
    segmentos = df["segmento"].value_counts().to_dict()
    estados_registro = (
        df["estado_registro"].map(_etiqueta_registro).value_counts().to_dict()
    )

    columnas_metricas = {
        "ig": ("followers_ig", "seguidores"),
        "fb": ("followers_fb", "seguidores"),
        "yt": ("followers_yt", "seguidores"),
        "tt": ("followers_tt", "seguidores"),
        "spotify": ("followers_spotify", "seguidores"),
        "bandcamp": ("reproducciones_bandcamp", "reproducciones"),
        "soundcloud": ("reproducciones_soundcloud", "reproducciones"),
        "beatport": ("followers_beatport", "seguidores"),
        "mixcloud": ("followers_mixcloud", "seguidores"),
    }
    seguidores: dict[str, int] = {}
    reproducciones: dict[str, int] = {}
    cobertura: dict[str, float] = {}
    for clave, (columna, clase) in columnas_metricas.items():
        serie = df[columna].fillna(0)
        suma = int(serie.sum())
        if clase == "seguidores":
            seguidores[clave] = suma
        else:
            reproducciones[clave] = suma
        cobertura[clave] = round(int((serie > 0).sum()) / total * 100, 1)

    feed_serie = feed_repo.serie_mensual(excluir_fuentes=["scraper"])
    posts_90dias = feed_repo.conteo_reciente(dias=90, excluir_fuentes=["scraper", "escena", "registro"])

    altas_por_mes = _serie_mensual(df["fecha_registro"].fillna(df["fecha_creacion"]))

    por_ciudad: list[dict] = []
    for ciudad, grupo in df.groupby("ciudad"):
        por_ciudad.append(
            {
                "nombre": ciudad,
                "total": len(grupo),
                "activo": int((grupo["estado_activo"] == "activo").sum()),
                "en_duda": int((grupo["estado_activo"] == "en_duda").sum()),
                "inactivo": int((grupo["estado_activo"] == "inactivo").sum()),
            }
        )
    por_ciudad.sort(key=lambda x: x["total"], reverse=True)

    filas_con_alta = df[
        df["fecha_registro"].notna() | df["fecha_creacion"].notna()
    ].copy()
    ultima_alta = None
    if not filas_con_alta.empty:
        filas_con_alta["_alta"] = pd.to_datetime(
            filas_con_alta["fecha_registro"].fillna(
                filas_con_alta["fecha_creacion"]
            ),
            errors="coerce",
        ).dropna()
        if not filas_con_alta.empty:
            tope = filas_con_alta.loc[filas_con_alta["_alta"].idxmax()]
            ultima_alta = {
                "nombre": tope["nombre"],
                "slug": tope["slug"],
                "fecha": str(tope["_alta"].date()),
            }

    verificados = sum(
        1
        for a in ArtistRepository(session).todos(con_links=False)
        if a.fb_page_token and a.estado_registro
    )

    # Stats separados por grupo (Ligas vs Escena)
    ligas_df = df[df["nivel_calculado"].fillna("") != ""]
    rookies_df = df[df["nivel_calculado"].fillna("") == ""]

    ligas = {
        "total": len(ligas_df),
        "por_nivel": ligas_df["nivel_calculado"].value_counts().to_dict() if not ligas_df.empty else {},
        "por_segmento": ligas_df["segmento"].value_counts().to_dict() if not ligas_df.empty else {},
        "por_ciudad": ligas_df["ciudad"].value_counts().to_dict() if not ligas_df.empty else {},
    }
    rookies = {
        "total": len(rookies_df),
        "por_segmento": rookies_df["segmento"].value_counts().to_dict() if not rookies_df.empty else {},
        "por_ciudad": rookies_df["ciudad"].value_counts().to_dict() if not rookies_df.empty else {},
        "por_estado_activo": rookies_df["estado_activo"].value_counts().to_dict() if not rookies_df.empty else {},
    }

    return {
        "total": total,
        "verificados": verificados,
        "generos": generos,
        "estados": estados,
        "estados_registro": estados_registro,
        "ciudades": ciudades,
        "segmentos": segmentos,
        "feed_serie": feed_serie,
        "altas_por_mes": altas_por_mes,
        "seguidores": seguidores,
        "reproducciones": reproducciones,
        "cobertura": cobertura,
        "posts_90dias": posts_90dias,
        "por_ciudad": por_ciudad,
        "ultima_alta": ultima_alta,
        "ligas": ligas,
        "rookies": rookies,
    }


def _slug_unico(session: Session, nombre: str) -> str:
    from lib.helpers import slugificar

    base = slugificar(nombre)
    slug = base
    contador = 2
    existentes = {a.slug for a in ArtistRepository(session).todos()}
    while slug in existentes:
        slug = f"{base}_{contador}"
        contador += 1
    return slug


def editar_artista(session: Session, slug: str, datos: dict) -> Artist | None:
    """Edición de un artista desde el panel de administración.

    Aplica solo los campos presentes en `datos`: campos básicos (nombre,
    ciudad, categoría, géneros, bio, notas, logros), estado de actividad,
    foto de perfil (`imagen_perfil`, `imagen_origen`) y el reemplazo de los
    enlaces de plataforma (si llega `redes`). Devuelve `None` si el slug no
    existe. No hace commit: lo hace el caller.
    """
    repos = ArtistRepository(session)
    artista = repos.por_slug(slug)
    if artista is None:
        return None

    if "nombre" in datos:
        nombre = (datos.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("El nombre es obligatorio")
        artista.nombre = nombre

    if "categoria" in datos:
        categoria = (datos.get("categoria") or "").strip()
        if categoria and categoria not in CATEGORIAS_VALIDAS:
            raise ValueError(f"Categoría inválida: {categoria}")
        artista.segmento = categoria

    if "ciudad" in datos:
        artista.ciudad = (datos.get("ciudad") or "").strip() or "[PENDIENTE]"
    if "generos" in datos:
        artista.generos = (datos.get("generos") or "").strip() or "[PENDIENTE]"
        if not artista.genero_dominante_manual:
            artista.genero_dominante = clasificar_genero_dominante(
                artista.slug, artista.generos
            )
    if "genero_dominante" in datos:
        manual = (datos.get("genero_dominante") or "").strip()
        if manual and manual not in GENEROS_DOMINANTES:
            raise ValueError(f"Género dominante inválido: {manual}")
        artista.genero_dominante_manual = manual
        if manual:
            artista.genero_dominante = manual
        else:
            artista.genero_dominante = clasificar_genero_dominante(
                artista.slug, artista.generos
            )
    if "bio" in datos:
        artista.bio = datos.get("bio") or ""
    if "notas" in datos:
        artista.notas = datos.get("notas") or ""
    if "logros" in datos:
        artista.logros = datos.get("logros") or ""
    if "estado_activo" in datos:
        estado = (datos.get("estado_activo") or "").strip()
        if estado and estado not in ESTADOS_ACTIVO:
            raise ValueError(f"Estado de actividad inválido: {estado}")
        artista.estado_activo = estado
    if "estado_registro" in datos:
        artista.estado_registro = datos.get("estado_registro") or ""
    if "nivel" in datos:
        nivel = (datos.get("nivel") or "").strip()
        if nivel and nivel not in NIVELES:
            raise ValueError(f"Nivel inválido: {nivel}")
        artista.nivel = nivel
    if "es_leyenda" in datos:
        artista.es_leyenda = bool(datos.get("es_leyenda"))
    if "imagen_perfil" in datos:
        artista.imagen_perfil = datos.get("imagen_perfil") or None
    if "imagen_origen" in datos:
        artista.imagen_origen = datos.get("imagen_origen") or None

    if "redes" in datos:
        _reemplazar_redes(session, artista, datos.get("redes") or [])

    return artista


def _reemplazar_redes(session: Session, artista: Artist, redes: list[dict]) -> None:
    """Reemplaza los enlaces de plataforma del artista por los indicados.

    Borra los enlaces no-búsqueda existentes y crea los nuevos (misma regla
    de detección de plataforma que el alta). Los enlaces de búsqueda
    (`es_busqueda`) se conservan: son respaldo de "dónde escucharlo".

    Aplica las mismas defensas que el alta: ninguna URL puede repetirse dentro
    del mismo envío (evita dobles conteos) ni estar ya vinculada a otro
    proyecto (evita robarse el enlace de un tercero para inflar números).
    """
    from lib.helpers import normalizar_url_para_duplicados
    from lib.plataformas import plataforma_y_url

    links_repo = LinkRepository(session)

    vistos: set[str] = set()
    nuevas: list[tuple[str, str, bool]] = []
    for red in redes:
        url = (red.get("url") or "").strip()
        if not url:
            continue
        existente = links_repo.url_ya_vinculada(
            url, excluir_artist_id=artista.id
        )
        if existente is not None:
            nombre_duplicado = existente.artist.nombre if existente.artist else "otro proyecto"
            raise ValueError(
                f"La URL {url} ya está vinculada a '{nombre_duplicado}'"
            )
        declarada = (red.get("plataforma") or "").strip().lower()
        plataforma, url = plataforma_y_url(declarada, url)
        canon = normalizar_url_para_duplicados(url)
        if canon in vistos:
            raise ValueError(f"El enlace {url} está repetido en las redes")
        vistos.add(canon)
        es_busqueda = "/results?" in url or "/search?" in url
        nuevas.append((plataforma, url, es_busqueda))

    for link in list(artista.links):
        if not link.es_busqueda:
            session.delete(link)
    for plataforma, url, es_busqueda in nuevas:
        links_repo.crear_para_artista(
            artista, plataforma=plataforma, url=url, es_busqueda=es_busqueda
        )


MAX_ALTAS_POR_DIA = 5
COOLDOWN_ALTAS_MINUTOS = 10


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()


def verificar_limite_altas(session: Session, ip: str) -> None:
    """Levanta ValueError si la IP excede el límite de altas recientes."""
    if not ip:
        raise ValueError("No se pudo determinar la dirección del solicitante")
    ahora = datetime.utcnow()
    desde = ahora - timedelta(hours=24)
    recientes = session.execute(
        select(AltaRegistro)
        .where(AltaRegistro.ip_hash == _hash_ip(ip))
        .where(AltaRegistro.creado_en >= desde)
        .order_by(AltaRegistro.creado_en.desc())
    ).scalars().all()

    if len(recientes) >= MAX_ALTAS_POR_DIA:
        raise ValueError(
            f"Límite alcanzado: máximo {MAX_ALTAS_POR_DIA} proyectos "
            "por dirección cada 24 h"
        )

    ultima = recientes[0] if recientes else None
    if ultima is not None:
        cooldown_hasta = ultima.creado_en + timedelta(minutes=COOLDOWN_ALTAS_MINUTOS)
        if ahora < cooldown_hasta:
            restante = int((cooldown_hasta - ahora).total_seconds() // 60) + 1
            raise ValueError(
                f"Espera {restante} min antes de registrar otro proyecto"
            )


def registrar_alta(session: Session, ip: str) -> None:
    """Registra un intento exitoso de alta para rate-limit futuro."""
    if ip:
        session.add(AltaRegistro(ip_hash=_hash_ip(ip)))


def crear_artista(session: Session, datos: dict) -> Artist:
    """Alta de artista nuevo desde el formulario (registro voluntario).

    Crea el registro y sus enlaces de plataforma en la BD. `segmento` viene
    como categoría; las redes se normalizan con `plataforma_y_url` (detección
    por dominio/correo, fallback a la plataforma declarada). El artista queda
    "sin conectar" hasta que reclama el perfil vía OAuth. No hace commit: lo
    hace el caller.
    """
    from lib.plataformas import plataforma_y_url

    nombre = (datos.get("nombre") or "").strip()
    if not nombre:
        raise ValueError("El nombre es obligatorio")

    categoria = (datos.get("categoria") or "").strip() or "Sin confirmar"
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoría inválida: {categoria}")

    ciudad = (datos.get("ciudad") or "").strip() or "[PENDIENTE]"

    generos_partes = [
        parte.strip() for parte in str(datos.get("generos") or "").split(",")
        if parte.strip()
    ]
    if len(generos_partes) > 5:
        raise ValueError("Puedes indicar como máximo 5 géneros")
    if any(len(genero) > 30 for genero in generos_partes):
        raise ValueError("Cada género puede tener como máximo 30 caracteres")
    generos = ", ".join(generos_partes) or "[PENDIENTE]"

    bio = str(datos.get("bio") or "").strip()
    if len(bio) > 500:
        raise ValueError("La bio puede tener como máximo 500 caracteres")

    redes_limpias = [
        {"plataforma": (r.get("plataforma") or "").strip().lower(),
         "url": (r.get("url") or "").strip()}
        for r in (datos.get("redes") or [])
        if (r.get("url") or "").strip()
    ]
    if not redes_limpias:
        raise ValueError("Debes incluir al menos un enlace a una red o plataforma")
    if len(redes_limpias) > 6:
        raise ValueError("Puedes incluir como máximo 6 enlaces")

    # Normaliza cada enlace y valida antes de crear nada: ninguna URL puede
    # repetirse dentro del mismo alta (evita dobles conteos) ni pertenecer ya a
    # otro proyecto (evita inflar números con el enlace de un tercero).
    from lib.helpers import normalizar_url_para_duplicados

    links_repo = LinkRepository(session)
    redes_normalizadas: list[tuple[str, str, bool]] = []
    vistos: set[str] = set()
    for red in redes_limpias:
        url = red["url"]
        declarada = red["plataforma"]
        plataforma, url = plataforma_y_url(declarada, url)
        canon = normalizar_url_para_duplicados(url)
        if canon in vistos:
            raise ValueError(f"El enlace {url} está repetido en tus redes")
        vistos.add(canon)
        existente = links_repo.url_ya_vinculada(url)
        if existente is not None:
            nombre_duplicado = existente.artist.nombre if existente.artist else "otro proyecto"
            raise ValueError(
                f"La URL {url} ya está vinculada a '{nombre_duplicado}'"
            )
        es_busqueda = "/results?" in url or "/search?" in url
        redes_normalizadas.append((plataforma, url, es_busqueda))

    repos = ArtistRepository(session)
    artista = repos.crear(
        slug=_slug_unico(session, nombre),
        nombre=nombre,
        segmento=categoria,
        ciudad=ciudad,
        generos=generos,
        estado_registro="registrado (formulario, sin conectar)",
        estado_activo="en_duda",
        metodo_actividad="sin datos",
    )
    artista.bio = bio
    artista.genero_dominante = clasificar_genero_dominante(artista.slug, artista.generos)

    for plataforma, url, es_busqueda in redes_normalizadas:
        links_repo.crear_para_artista(
            artista, plataforma=plataforma, url=url, es_busqueda=es_busqueda
        )
    return artista


def onboarding_artista(session: Session, artista: Artist) -> dict:
    """Scraping inicial tras el alta (best-effort, nunca rompe la creación).

    Resuelve foto de perfil desde las redes, inserta los últimos videos de
    YouTube (si hay canal) en el feed, captura oyentes mensuales de Spotify,
    suscriptores/vistas de YouTube, seguidores de SoundCloud y de Mixcloud, y
    recalcula `estado_activo` con la señal más reciente. Las fallas de red se
    registran y se continúa.
    """
    from scraper.adapters import imagenes
    from scraper.adapters.youtube import latest_videos
    from scraper.core import estado_activo_recomputado
    from scraper.errors import ScraperError

    resultado: dict = {
        "imagen": None,
        "videos": 0,
        "spotify_oyentes": None,
        "yt_suscriptores": None,
        "soundcloud_seguidores": None,
        "mixcloud_seguidores": None,
        "estado": artista.estado_activo,
    }

    # Foto de perfil desde las redes (URL, sin descargar).
    try:
        url, origen = imagenes.imagen_de_artista(artista.links)
        if url:
            artista.imagen_perfil = url
            artista.imagen_origen = origen or None
            artista.imagen_actualizada = datetime.utcnow()
            resultado["imagen"] = origen or "url"
    except Exception:
        pass

    # Últimos videos de YouTube (feed RSS público, sin API key ni cuota) → feed.
    canales = [
        l for l in artista.links if l.plataforma == "yt" and not l.es_busqueda
    ]
    if canales:
        feed = FeedRepository(session)
        for canal in canales:
            try:
                for v in latest_videos(canal.url, max_videos=5):
                    if feed.existe_url(v["url"]):
                        continue
                    feed.crear(
                        artist_id=artista.id,
                        fuente="yt",
                        tipo="video",
                        titulo=v["titulo"],
                        url=feed._url_canonica(v["url"]),
                        fecha=v["fecha"],
                        imagen=v["imagen"] or None,
                        detalle=v["descripcion"],
                    )
                    resultado["videos"] += 1
            except ScraperError:
                continue

        # Estadísticas de YouTube (suscriptores/vistas, Data API v3).
        from scraper.adapters.youtube import channel_id_from_url, channel_statistics

        api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
        if api_key:
            suscriptores: list[int] = []
            vistas: list[int] = []
            for canal in canales:
                try:
                    channel_id = channel_id_from_url(canal.url)
                    if not channel_id:
                        continue
                    datos = channel_statistics(channel_id, api_key)
                except Exception:
                    continue
                if datos.get("suscriptores") is not None:
                    suscriptores.append(datos["suscriptores"])
                if datos.get("vistas") is not None:
                    vistas.append(datos["vistas"])
            if suscriptores:
                artista.followers_yt = sum(suscriptores)
                resultado["yt_suscriptores"] = sum(suscriptores)
            if vistas:
                artista.vistas_yt = sum(vistas)

    # Oyentes mensuales desde los perfiles públicos de Spotify. Si hay varios
    # perfiles oficiales (cuentas duplicadas), se suma cada lectura y se guarda
    # la suma; los snapshots conservan el valor por perfil.
    spotify_links = [
        l for l in artista.links if l.plataforma == "spotify" and not l.es_busqueda
    ]
    if spotify_links:
        from scraper.adapters.spotify_public import SpotifyPublicError, obtener_oyentes

        snapshots = SpotifySnapshotRepository(session)
        suma = 0
        for link in spotify_links:
            try:
                oyentes = obtener_oyentes(link.url)
                if oyentes is not None:
                    suma += oyentes
                snapshots.crear(
                    artist_id=artista.id,
                    url_spotify=link.url,
                    oyentes_mensuales=oyentes,
                )
            except SpotifyPublicError:
                continue
        if suma > 0:
            artista.oyentes_mensuales_spotify = suma
            artista.fecha_oyentes_spotify = datetime.utcnow()
            artista.fuente_oyentes_spotify = "spotify_public_profile"
            resultado["spotify_oyentes"] = suma

    # Seguidores de SoundCloud (api-v2, una llamada por perfil).
    soundcloud_links = [
        l for l in artista.links
        if l.plataforma == "soundcloud" and not l.es_busqueda
    ]
    if soundcloud_links:
        from scraper.adapters.soundcloud import SoundCloudError, seguidores

        suma_sc = 0
        for link in soundcloud_links:
            try:
                suma_sc += seguidores(link.url)
            except SoundCloudError:
                continue
        if suma_sc > 0:
            artista.followers_soundcloud = suma_sc
            resultado["soundcloud_seguidores"] = suma_sc

    # Seguidores de Mixcloud (API REST pública, una llamada por perfil).
    mixcloud_links = [
        l for l in artista.links
        if l.plataforma == "mixcloud" and not l.es_busqueda
    ]
    if mixcloud_links:
        from scraper.adapters.mixcloud import seguidores as mixcloud_seguidores

        suma_mx = 0
        for link in mixcloud_links:
            try:
                suma_mx += mixcloud_seguidores(link.url)
            except ScraperError:
                continue
        if suma_mx > 0:
            artista.followers_mixcloud = suma_mx
            resultado["mixcloud_seguidores"] = suma_mx

    # Recalcular actividad con la señal más reciente (feed incluido).
    ultimo_feed = ultimo_feed_de_artista(session, artista)
    artista.estado_activo = estado_activo_recomputado(
        artista, ultimo_feed=ultimo_feed
    )
    resultado["estado"] = artista.estado_activo
    return resultado


def actualizar_ultimo_evento(session: Session, artista: Artist) -> None:
    """Pone `ultimo_evento` con la fecha del evento más reciente del cartel.

    Solo avanza la fecha (nunca regresa): si el evento más reciente de la
    escena en cuyo cartel aparece el artista es posterior a lo registrado, se
    actualiza; en caso contrario se conserva el valor manual/CSV.
    """
    fechas = [
        e.fecha for e in EventRepository(session).de_artista(artista.nombre)
        if e.fecha is not None
    ]
    if not fechas:
        return
    mas_reciente = max(fechas)
    if artista.ultimo_evento is None or mas_reciente > artista.ultimo_evento:
        artista.ultimo_evento = mas_reciente


def recalcular_actividad(session: Session) -> list[tuple]:
    """Recomputa `estado_activo` de todos los artistas con su señal más reciente.

    Actualiza primero `ultimo_evento` desde la tabla `events` (los eventos del
    cartel también son señal de actividad) y luego aplica la regla de
    `scraper/core.py` tomando la señal más reciente (lanzamiento, evento o
    feed). Devuelve la lista de cambios `(nombre, antes, después)`.
    """
    from scraper.core import estado_activo_recomputado

    cambios = []
    for artista in ArtistRepository(session).todos():
        actualizar_ultimo_evento(session, artista)
        ultimo_feed = ultimo_feed_de_artista(session, artista)
        nuevo = estado_activo_recomputado(artista, ultimo_feed=ultimo_feed)
        if nuevo != artista.estado_activo:
            cambios.append((artista.nombre, artista.estado_activo, nuevo))
            artista.estado_activo = nuevo
    return cambios
