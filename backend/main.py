"""API REST de la escena local.

Capa pública que reutiliza la capa de datos (`lib/repository` + `lib/servicios`)
y deja la puerta abierta a otros consumidores (mobile, terceros). Solo
orquesta: el conocimiento de plataformas vive en `lib/plataformas`.
"""

import os
from datetime import date, datetime, time
from typing import Any

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.dependencies import (
    get_artist_repo,
    get_db,
    get_event_repo,
)
from lib.helpers import (
    artista_link_principal,
    conteo_generos,
    generos_hashtags,
)
from lib.plataformas import (
    link_con_metadatos,
    preview_feed,
)
from lib.repository import ArtistRepository, EventRepository
from lib.servicios import (
    artistas_df,
    crear_artista,
    eventos_de_artista,
    feed_df,
    onboarding_artista,
    ranking_global,
    stats_escena,
)
from backend.feed_meta import meta_configurado, router as feed_meta_router

app = FastAPI(title="Frontera Grande API", version="0.1.0")

CORS_ORIGINS = [
  o.strip()
  for o in os.getenv(
      "CORS_ORIGINS",
      "http://localhost:3000,http://127.0.0.1:3000",
  ).split(",")
  if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feed_meta_router)

ESTADO_COLORES = {
    "activo": "#76B041",
    "en_duda": "#F5A623",
    "inactivo": "#E4572E",
}


class RedEntrada(BaseModel):
    """Una red social / plataforma de streaming del formulario de alta."""

    plataforma: str = ""
    url: str = ""


class AltaArtistaEntrada(BaseModel):
    """Cuerpo de POST /api/artists (alta desde el formulario)."""

    nombre: str
    ciudad: str = ""
    categoria: str = ""
    redes: list[RedEntrada] = []


def _json_safe(valor: Any) -> Any:
    """Convierte valores no serializables a JSON (fechas, NaN, numpy)."""
    if isinstance(valor, dict):
        return {k: _json_safe(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple, pd.Series)):
        return [_json_safe(v) for v in valor]
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    if isinstance(valor, float) and pd.isna(valor):
        return None
    if hasattr(valor, "item"):  # escalares numpy (int64, float64...)
        return _json_safe(valor.item())
    return valor


@app.get("/api/health")
def health():
    return {"estado": "ok"}


@app.get("/api/artists")
def list_artists(
    segmento: str | None = None,
    ciudad: str | None = None,
    genero: str | None = None,
    estado: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    artistas: ArtistRepository = Depends(get_artist_repo),
):
    """Listado de artistas (tarjetas para el directorio)."""
    df = artistas_df(db)
    if df.empty:
        return []

    ranking, menciones = ranking_global(df)

    if q:
        q = q.lower()
        df = df[
            df["nombre"].str.lower().str.contains(q, na=False)
            | df["generos"].str.lower().str.contains(q, na=False)
        ]
    if segmento:
        df = df[df["segmento"] == segmento]
    if ciudad:
        df = df[df["ciudad"] == ciudad]
    if estado:
        df = df[df["estado_activo"] == estado]
    if genero:
        df = df[df["generos"].str.lower().str.contains(genero.lower(), na=False)]

    tarjetas = []
    for _, fila in df.iterrows():
        artist = artistas.por_id(fila["id"])
        tarjetas.append(
            {
                "slug": fila["slug"],
                "nombre": fila["nombre"],
                "segmento": fila["segmento"],
                "ciudad": fila["ciudad"],
                "generos": generos_hashtags(fila["generos"]),
                "estado_activo": fila["estado_activo"],
                "color_estado": ESTADO_COLORES.get(fila["estado_activo"], "#888"),
                "metodo_actividad": fila["metodo_actividad"],
                "estado_registro": fila.get("estado_registro") or "",
                "verificado": bool(
                    artist and artist.fb_page_token and artist.estado_registro
                ),
                "ultimo_lanzamiento": _json_safe(fila["ultimo_lanzamiento"]),
                "ultimo_evento": _json_safe(fila["ultimo_evento"]),
                "followers": {
                    "ig": fila["followers_ig"],
                    "fb": fila["followers_fb"],
                    "yt": fila["followers_yt"],
                    "spotify": fila["followers_spotify"],
                    "tt": fila["followers_tt"],
                },
                "imagen_perfil": fila.get("imagen_perfil") or None,
                "imagen_origen": fila.get("imagen_origen") or None,
                "ranking": ranking.get(
                    fila["slug"],
                    {"indice": None, "rank": None, "total": len(ranking)},
                ),
                "menciones": menciones.get(fila["slug"], []),
                "link_principal": (
                    artista_link_principal(db, artist) if artist else None
                ),
                "links": [
                    {"plataforma": l.plataforma, "url": l.url}
                    for l in (artist.links if artist else [])
                    if not l.es_busqueda
                ],
            }
        )
    return _json_safe(tarjetas)


@app.post("/api/artists", status_code=201)
def crear_artista_endpoint(
    entrada: AltaArtistaEntrada,
    db: Session = Depends(get_db),
):
    """Alta de un artista nuevo desde el formulario web (modo desarrollo).

    Crea el registro y sus enlaces, y dispara un onboarding *best-effort*:
    foto de perfil desde las redes, último feed de YouTube (si hay canal) y
    recalculo de `estado_activo`. Las fallas de red no impiden la creación.
    """
    try:
        artista = crear_artista(db, entrada.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.flush()  # asigna artista.id antes del onboarding (snapshots/feed lo usan)
    resumen = onboarding_artista(db, artista)
    db.commit()
    return {
        "slug": artista.slug,
        "nombre": artista.nombre,
        "onboarding": resumen,
    }


@app.get("/api/artists/{slug}")
def artist_detail(
    slug: str,
    db: Session = Depends(get_db),
    artistas: ArtistRepository = Depends(get_artist_repo),
):
    """Perfil completo de un artista: datos, redes, eventos y feed propio."""
    artist = artistas.por_slug(slug)
    if artist is None:
        raise HTTPException(status_code=404, detail="Artista no encontrado")

    df = artistas_df(db)
    fila = df[df["slug"] == slug].iloc[0] if not df.empty else None

    ranking, menciones = ranking_global(df)

    links = [link_con_metadatos(l) for l in artist.links]
    eventos = [
        _json_safe(
            {
                "fecha": e["fecha"],
                "nombre": e["nombre"],
                "lugar": e["lugar"],
                "ciudad": e["ciudad"],
                "artistas": e["artistas"],
                "que_demuestra": e["que_demuestra"],
            }
        )
        for _, e in eventos_de_artista(db, artist.nombre).iterrows()
    ]

    feed = feed_df(db, limite=60, artista=artist.nombre)
    feed_propio = feed.to_dict(orient="records")
    feed_propio = [
        {**f, "preview": preview_feed(f), "fecha": _json_safe(f["fecha"])}
        for f in feed_propio
    ]

    perfil = {
        "slug": artist.slug,
        "nombre": artist.nombre,
        "segmento": artist.segmento,
        "ciudad": artist.ciudad,
        "generos": generos_hashtags(artist.generos),
        "es_propio": artist.es_propio,
        "estado_activo": artist.estado_activo,
        "color_estado": ESTADO_COLORES.get(artist.estado_activo, "#888"),
        "metodo_actividad": artist.metodo_actividad,
        "estado_registro": artist.estado_registro or "",
        "verificado": bool(artist.fb_page_token and artist.estado_registro),
        "ultimo_lanzamiento": _json_safe(artist.ultimo_lanzamiento),
        "ultimo_evento": _json_safe(artist.ultimo_evento),
        "followers": {
            "ig": artist.followers_ig,
            "fb": artist.followers_fb,
            "yt": artist.followers_yt,
            "tt": artist.followers_tt,
            "spotify": artist.followers_spotify,
        },
        "stats": {
            "ig": {"seguidores": artist.followers_ig},
            "fb": {"seguidores": artist.followers_fb},
            "yt": {
                "seguidores": artist.followers_yt,
                "vistas": artist.vistas_yt,
            },
            "tt": {
                "seguidores": artist.followers_tt,
                "vistas": artist.vistas_tt,
            },
            "spotify": {
                "seguidores": artist.followers_spotify,
                "reproducciones": artist.reproducciones_spotify,
            },
            "bandcamp": {
                "reproducciones": artist.reproducciones_bandcamp,
            },
            "soundcloud": {
                "reproducciones": artist.reproducciones_soundcloud,
            },
        },
        "fecha_captura": _json_safe(artist.fecha_captura),
        "ranking": ranking.get(
            artist.slug,
            {"indice": None, "rank": None, "total": len(ranking)},
        ),
        "menciones": menciones.get(artist.slug, []),
        "igfb": {
            "configurado": meta_configurado(),
            "conectado": bool(artist.fb_page_token),
            "pagina_fb": artist.fb_page_id or None,
            "ig": artist.ig_user_id or None,
        },
        "imagen_perfil": artist.imagen_perfil or None,
        "imagen_origen": artist.imagen_origen or None,
        "logros": artist.logros or "",
        "bio": artist.bio or "",
        "notas": artist.notas or "",
        "links": _json_safe(links),
        "eventos": eventos,
        "feed": feed_propio,
    }
    if artist.oyentes_mensuales_spotify is not None:
        perfil["stats"]["spotify"]["oyentes_mensuales"] = artist.oyentes_mensuales_spotify
        perfil["stats"]["spotify"]["fecha_captura"] = _json_safe(
            artist.fecha_oyentes_spotify
        )
    return _json_safe(perfil)


@app.get("/api/feed")
def get_feed(db: Session = Depends(get_db)):
    """Feed unificado con previews de contenido."""
    feed = feed_df(db, limite=80)
    if feed.empty:
        return []
    filas = [
        {
            "fecha": _json_safe(f["fecha"]),
            "tipo": f["tipo"],
            "fuente": f["fuente"],
            "titulo": f["titulo"],
            "url": f.get("url"),
            "detalle": f.get("detalle") or "",
            "artista": f.get("artista") or "",
            "artista_slug": f.get("artista_slug") or None,
            "imagen_artista": f.get("imagen_artista") or None,
            "preview": preview_feed(f),
        }
        for f in feed.to_dict(orient="records")
    ]
    return _json_safe(filas)


@app.get("/api/events")
def list_events(eventos_repo: EventRepository = Depends(get_event_repo)):
    eventos = [
        {
            "id": e.id,
            "nombre": e.nombre,
            "fecha": _json_safe(e.fecha),
            "lugar": e.lugar,
            "ciudad": e.ciudad,
            "artistas": e.artistas,
            "que_demuestra": e.que_demuestra,
            "fuente": e.fuente,
        }
        for e in eventos_repo.todos_fecha_desc()
    ]
    return _json_safe(eventos)


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    """Indicadores de la escena para el panel público."""
    return _json_safe(stats_escena(db))


@app.get("/api/genres")
def genres(db: Session = Depends(get_db)):
    df = artistas_df(db)
    return _json_safe(conteo_generos(df).index.tolist())
