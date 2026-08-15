"""Servicios de aplicación de la escena local.

Reúnen la lógica de dominio que consume la API: read-models (DataFrames),
feed unificado, métricas por plataforma y ranking de alcance. No tocan SQL
directo: delegan en `lib.repository`.
"""

from collections import Counter
from datetime import date, datetime

import pandas as pd
from sqlalchemy.orm import Session

from db.models import Artist, ActivityCheck
from lib.helpers import TIPOS_FEED, conteo_generos, youtube_thumbnail
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
        for a in ArtistRepository(session).todos()
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
    fechas = [
        (fi.fecha or fi.created_at).date()
        for fi in FeedRepository(session).de_artista(artist.id)
        if fi.tipo in TIPOS_FEED_CONTENIDO
    ]
    if not fechas:
        return None
    return max(fechas)


def feed_df(
    session: Session, limite: int = 60, artista: str | None = None
) -> pd.DataFrame:
    """Feed unificado: contenido scrapeado + eventos + lanzamientos + chequeos.

    Con `artista` se filtra todo a ese proyecto (feed del perfil); sin él,
    es el feed global. El tope `limite` solo aplica al resultado final, no
    por artista.
    """
    filas = []

    for fi in FeedRepository(session).todos_desc():
        nombre_art = fi.artist.nombre if fi.artist else ""
        if artista is not None and nombre_art != artista:
            continue
        imagen = fi.imagen or (
            youtube_thumbnail(fi.url) if fi.fuente == "youtube" else ""
        )
        filas.append(
            {
                "fecha": fi.fecha or fi.created_at,
                "tipo": TIPOS_FEED.get(fi.tipo, fi.tipo),
                "fuente": fi.fuente,
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

    for e in EventRepository(session).todos_fecha_desc():
        if e.fecha is None:
            continue
        if artista is not None and artista.lower() not in (e.artistas or "").lower():
            continue
        detalle = " · ".join(
            parte for parte in (e.lugar, e.artistas, e.que_demuestra) if parte
        )
        filas.append(
            {
                "fecha": e.fecha,
                "tipo": TIPOS_FEED["evento"],
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

    for a in ArtistRepository(session).con_lanzamiento():
        if artista is not None and a.nombre != artista:
            continue
        filas.append(
            {
                "fecha": a.ultimo_lanzamiento,
                "tipo": TIPOS_FEED["lanzamiento"],
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

    for c in ChecksRepository(session).ultimos(30):
        nombre = c.artist.nombre if c.artist else ""
        if artista is not None and nombre != artista:
            continue
        filas.append(
            {
                "fecha": c.fecha_chequeo,
                "tipo": TIPOS_FEED.get("error") if c.resultado == "error" else "🕸️ Chequeo",
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
    }
    oyentes = fila["oyentes_mensuales_spotify"]
    if pd.notna(oyentes):
        metricas["spotify"]["oyentes_mensuales"] = oyentes
        metricas["spotify"]["fecha_captura"] = fila["fecha_oyentes_spotify"]
    return metricas


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

    Devuelve {slug: [texto, ...]} con el Top 3 de la escena (ranking global)
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
            f"Nº {puesto} de la escena (de {len(globales)})"
        )

    for genero, slugs in por_genero.items():
        _agregar_grupo_mencion(menciones, indices, genero, slugs, "Nº {puesto} del género {grupo} (de {n})")
    for ciudad, slugs in por_ciudad.items():
        _agregar_grupo_mencion(menciones, indices, ciudad, slugs, "Nº {puesto} en {grupo} (de {n})")
    for segmento, slugs in por_segmento.items():
        _agregar_grupo_mencion(menciones, indices, segmento, slugs, "Nº {puesto} en la categoría {grupo} (de {n})")

    return menciones


def ranking_global(df: pd.DataFrame) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Ranking de alcance y menciones de todos los artistas."""
    from lib.helpers import indice_alcance

    metricas = {fila["slug"]: metricas_artista(fila) for _, fila in df.iterrows()}
    indices = indice_alcance(metricas)
    ordenados = sorted(indices.items(), key=lambda x: x[1], reverse=True)
    ranking = {
        slug: {"indice": indice, "rank": i + 1, "total": len(ordenados)}
        for i, (slug, indice) in enumerate(ordenados)
    }
    menciones = menciones_ranking(df, indices)
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

    feed = feed_df(session, limite=3000)
    if feed.empty:
        feed_serie: list[dict] = []
        posts_90dias = 0
    else:
        sin_chequeos = feed[feed["fuente"] != "scraper"]
        publicaciones = feed[~feed["fuente"].isin(["scraper", "escena", "registro"])]
        feed_serie = (
            _serie_mensual(sin_chequeos["fecha"]) if not sin_chequeos.empty else []
        )
        posts_90dias = int(
            (
                publicaciones["fecha"]
                >= pd.Timestamp.today() - pd.Timedelta(days=90)
            ).sum()
        )

    altas = df["fecha_registro"].fillna(df["fecha_creacion"])
    altas_por_mes = _serie_mensual(altas)

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

    hoy = date.today()
    proximos = [
        e
        for e in EventRepository(session).todos_fecha_asc()
        if e.fecha and e.fecha >= hoy
    ]
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
        for a in ArtistRepository(session).todos()
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


def crear_artista(session: Session, datos: dict) -> Artist:
    """Alta de artista nuevo desde el formulario (registro voluntario).

    Crea el registro y sus enlaces de plataforma en la BD. `segmento` viene
    como categoría; las redes se mapean a `plataforma` con `detectar_plataforma`
    (fallback a la plataforma declarada). El artista queda "sin conectar" hasta
    que reclama el perfil vía OAuth. No hace commit: lo hace el caller.
    """
    from lib.plataformas import detectar_plataforma

    nombre = (datos.get("nombre") or "").strip()
    if not nombre:
        raise ValueError("El nombre es obligatorio")

    categoria = (datos.get("categoria") or "").strip() or "Sin confirmar"
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoría inválida: {categoria}")

    ciudad = (datos.get("ciudad") or "").strip() or "[PENDIENTE]"

    repos = ArtistRepository(session)
    artista = repos.crear(
        slug=_slug_unico(session, nombre),
        nombre=nombre,
        segmento=categoria,
        ciudad=ciudad,
        generos="[PENDIENTE]",
        estado_registro="registrado (formulario, sin conectar)",
        estado_activo="en_duda",
        metodo_actividad="sin datos",
    )

    links_repo = LinkRepository(session)
    for red in datos.get("redes") or []:
        url = (red.get("url") or "").strip()
        if not url:
            continue
        declarada = (red.get("plataforma") or "").strip().lower()
        plataforma = detectar_plataforma(url) or declarada or "otro"
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
