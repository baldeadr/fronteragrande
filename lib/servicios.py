"""Servicios de aplicación de la escena local.

Reúnen la lógica de dominio que consume la API: read-models (DataFrames),
feed unificado, métricas por plataforma y ranking de alcance. No tocan SQL
directo: delegan en `lib.repository`.
"""

import hashlib
from collections import Counter
from datetime import date, datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import ESTADOS_ACTIVO, Artist, ActivityCheck, AltaRegistro
from lib.helpers import (
    TIPOS_FEED,
    conteo_generos,
    dominancia_plataforma,
    patron_dominancia,
    ratio_engagement_spotify,
    ratio_social_musica,
    ratio_viralidad_yt,
    TEXTO_PATRON_CONSUMO,
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
    """DataFrame plano de artistas para tablas y gráficas."""
    filas = [
        {
            "id": a.id,
            "slug": a.slug,
            "nombre": a.nombre,
            "segmento": a.segmento,
            "ciudad": a.ciudad,
            "generos": a.generos,
            "estado_registro": a.estado_registro,
            "es_propio": a.es_propio,
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
    return pd.DataFrame(filas)


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
            youtube_thumbnail(fi.url) if fi.fuente == "youtube" else ""
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
            "reproducciones": fila["reproducciones_spotify"],
        },
        "bandcamp": {"reproducciones": fila["reproducciones_bandcamp"]},
        "soundcloud": {"reproducciones": fila["reproducciones_soundcloud"]},
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
            ("spotify", "reproducciones"),
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
            ("spotify", ("seguidores", "oyentes_mensuales", "reproducciones")),
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
    """Análisis de hábitos de consumo por plataforma.

    Devuelve el patrón detectado, ratios derivados, dominancia de plataforma
    y un texto interpretativo. Todo calculado a partir de datos existentes.
    """
    patron = patron_dominancia(metricas)
    viralidad_yt = ratio_viralidad_yt(metricas)
    engagement_sp = ratio_engagement_spotify(metricas)
    gap_social = ratio_social_musica(metricas)
    dominancia = dominancia_plataforma(metricas)

    return {
        "patron": patron,
        "texto": TEXTO_PATRON_CONSUMO.get(patron, TEXTO_PATRON_CONSUMO["sin_datos"]),
        "ratios": {
            "viralidad_yt": viralidad_yt,
            "engagement_spotify": engagement_sp,
            "gap_social_musica": gap_social,
        },
        "dominancia": dominancia,
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
        for genero in [
            g.strip()
            for g in str(fila["generos"]).split(",")
            if g.strip() and "PENDIENTE" not in g.upper()
        ]:
            por_genero.setdefault(genero, []).append(fila["slug"])
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


def ranking_global(df: pd.DataFrame) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Ranking de alcance y menciones de todos los artistas."""
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
    las altas por mes y los eventos próximos. Caller: `GET /api/stats`.
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
            "eventos_proximos": {"total": 0, "ciudad": None, "proximos": []},
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
        "spotify": ("reproducciones_spotify", "reproducciones"),
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

    eventos_repo = EventRepository(session)
    proximos = eventos_repo.proximos(desde=date.today())
    ciudad_proxima = None
    if proximos:
        agrupado = Counter(e.ciudad for e in proximos if e.ciudad)
        if agrupado:
            ciudad_proxima = agrupado.most_common(1)[0][0]
    eventos_proximos = {
        "total": len(proximos),
        "ciudad": ciudad_proxima,
        "proximos": [
            {
                "nombre": e.nombre,
                "ciudad": e.ciudad,
                "fecha": e.fecha,
            }
            for e in proximos[:3]
        ],
    }

    verificados = sum(
        1
        for a in ArtistRepository(session).todos(con_links=False)
        if a.fb_page_token and a.estado_registro
    )

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
        "eventos_proximos": eventos_proximos,
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
    """
    from lib.plataformas import plataforma_y_url

    links_repo = LinkRepository(session)
    for link in list(artista.links):
        if not link.es_busqueda:
            session.delete(link)
    for red in redes:
        url = (red.get("url") or "").strip()
        if not url:
            continue
        declarada = (red.get("plataforma") or "").strip().lower()
        plataforma, url = plataforma_y_url(declarada, url)
        es_busqueda = "/results?" in url or "/search?" in url
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
    if len(generos_partes) > 3:
        raise ValueError("Puedes indicar como máximo 3 géneros")
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

    links_repo = LinkRepository(session)
    for red in redes_limpias:
        existente = links_repo.url_ya_vinculada(red["url"])
        if existente is not None:
            nombre_duplicado = existente.artist.nombre if existente.artist else "otro proyecto"
            raise ValueError(
                f"La URL {red['url']} ya está vinculada a '{nombre_duplicado}'"
            )

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

    for red in redes_limpias:
        url = red["url"]
        declarada = red["plataforma"]
        plataforma, url = plataforma_y_url(declarada, url)
        es_busqueda = "/results?" in url or "/search?" in url
        links_repo.crear_para_artista(
            artista, plataforma=plataforma, url=url, es_busqueda=es_busqueda
        )
    return artista


def onboarding_artista(session: Session, artista: Artist) -> dict:
    """Scraping inicial tras el alta (best-effort, nunca rompe la creación).

    Resuelve foto de perfil desde las redes, inserta los últimos videos de
    YouTube (si hay canal) en el feed y recalcula `estado_activo` con la señal
    más reciente. Las fallas de red se registran y se continúa.
    """
    from scraper.adapters import imagenes
    from scraper.adapters.youtube import latest_videos
    from scraper.core import estado_activo_recomputado
    from scraper.errors import ScraperError

    resultado: dict = {
        "imagen": None,
        "videos": 0,
        "spotify_oyentes": None,
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

    # Últimos videos de YouTube (RSS, sin API key) → feed.
    canales = [
        l for l in artista.links if l.plataforma == "yt" and not l.es_busqueda
    ]
    if canales:
        try:
            feed = FeedRepository(session)
            for v in latest_videos(canales[0].url, max_videos=5):
                if feed.existe_url(v["url"]):
                    continue
                feed.crear(
                    artist_id=artista.id,
                    fuente="yt",
                    tipo="video",
                    titulo=v["titulo"],
                    url=v["url"],
                    fecha=v["fecha"],
                    imagen=v["imagen"] or None,
                    detalle=v["descripcion"],
                )
                resultado["videos"] += 1
        except ScraperError:
            pass

    # Oyentes mensuales desde el perfil público de Spotify (captura única).
    spotify_links = [
        l for l in artista.links if l.plataforma == "spotify" and not l.es_busqueda
    ]
    if spotify_links:
        from scraper.adapters.spotify_public import SpotifyPublicError, obtener_oyentes

        url_spotify = spotify_links[0].url
        try:
            oyentes = obtener_oyentes(url_spotify)
            artista.oyentes_mensuales_spotify = oyentes
            artista.fecha_oyentes_spotify = datetime.utcnow()
            artista.fuente_oyentes_spotify = "spotify_public_profile"
            SpotifySnapshotRepository(session).crear(
                artist_id=artista.id,
                url_spotify=url_spotify,
                oyentes_mensuales=oyentes,
            )
            resultado["spotify_oyentes"] = oyentes
        except SpotifyPublicError:
            pass

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
