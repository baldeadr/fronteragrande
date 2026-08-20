"""API REST de la escena local.

Capa pública que reutiliza la capa de datos (`lib/repository` + `lib/servicios`)
y deja la puerta abierta a otros consumidores (mobile, terceros). Solo
orquesta: el conocimiento de plataformas vive en `lib/plataformas`.
"""

import os
from datetime import date, datetime, time
from typing import Any

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.dependencies import (
    get_artist_repo,
    get_db,
    get_event_repo,
)
from backend.push import router as push_router
from db.models import FeedItem, SpotifyListenerSnapshot
from lib.helpers import (
    artista_link_principal,
    conteo_generos,
    generos_hashtags,
)
from lib.plataformas import (
    link_con_metadatos,
    preview_feed,
)
from lib.notificaciones import notificar_todos
from lib.repository import ArtistRepository, EventRepository, PushSubscriptionRepository, SettingsRepository
from lib.servicios import (
    artistas_df,
    analisis_artista,
    crear_artista,
    editar_artista,
    eventos_de_artista,
    feed_df,
    metricas_artista,
    onboarding_artista,
    ranking_global,
    recalcular_actividad,
    stats_escena,
)
from backend.feed_meta import (
    ADMIN_PASSWORD,
    meta_configurado,
    router as feed_meta_router,
)
from backend.feed_tiktok import (
    tiktok_configurado,
    router as feed_tiktok_router,
)

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
app.include_router(feed_tiktok_router)
app.include_router(push_router)

@app.get("/tiktokZRAuUrtos3HEHHPy6apDTOQcgqkpwyZC.txt")
def _verificacion_tiktok():
    """Archivo de verificación de la URL prefix en TikTok for Developers."""
    ruta = os.path.join(
        os.path.dirname(__file__), "tiktokZRAuUrtos3HEHHPy6apDTOQcgqkpwyZC.txt"
    )
    with open(ruta, encoding="utf-8") as f:
        return PlainTextResponse(f.read())


_PAGINA_PENDIENTE = """<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} · Frontera Grande</title></head>
<body style="font-family:system-ui;max-width:640px;margin:3rem auto;padding:0 1rem">
<h1>{titulo}</h1>
<p>Documento en preparación. <strong>[PENDIENTE]</strong></p>
</body></html>"""


@app.get("/terminos")
def _terminos():
    """Página mínima de Términos de Servicio (requisito de TikTok/Meta)."""
    return HTMLResponse(_PAGINA_PENDIENTE.format(titulo="Términos de Servicio"))


@app.get("/privacidad")
def _privacidad():
    """Página mínima de Política de Privacidad (requisito de TikTok/Meta)."""
    return HTMLResponse(_PAGINA_PENDIENTE.format(titulo="Política de Privacidad"))

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
    generos: str = ""
    bio: str = ""
    redes: list[RedEntrada] = []


class EditarArtistaEntrada(BaseModel):
    """Cuerpo de PUT /api/artists/{slug} (edición desde el panel de admin).

    Todos los campos son opcionales: solo se aplican los presentes.
    """

    nombre: str | None = None
    ciudad: str | None = None
    categoria: str | None = None
    generos: str | None = None
    bio: str | None = None
    notas: str | None = None
    logros: str | None = None
    estado_activo: str | None = None
    estado_registro: str | None = None
    redes: list[RedEntrada] | None = None


class EventoEntrada(BaseModel):
    """Cuerpo de POST/PUT /api/admin/events (alta/edición desde el admin).

    Todos los campos son opcionales salvo `nombre` en el alta: solo se
    aplican los presentes. `fecha` llega como ISO `YYYY-MM-DD`.
    """

    nombre: str | None = None
    fecha: str | None = None
    lugar: str | None = None
    ciudad: str | None = None
    artistas: str | None = None
    que_demuestra: str | None = None
    fuente: str | None = None


def _fecha_desde(texto: str | None) -> date | None:
    """Convierte una fecha ISO `YYYY-MM-DD` a `date` (None si está vacía)."""
    if not texto or not texto.strip():
        return None
    return date.fromisoformat(texto.strip())


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
                    artist
                    and (artist.fb_page_token or artist.tt_refresh_token)
                    and artist.estado_registro
                ),
                "ultimo_lanzamiento": _json_safe(fila["ultimo_lanzamiento"]),
                "ultimo_evento": _json_safe(fila["ultimo_evento"]),
                "followers": {
                    "ig": fila["followers_ig"],
                    "fb": fila["followers_fb"],
                    "yt": fila["followers_yt"],
                    "spotify": fila["followers_spotify"],
                    "tt": fila["followers_tt"],
                    "beatport": fila["followers_beatport"],
                    "mixcloud": fila["followers_mixcloud"],
                },
                "imagen_perfil": fila.get("imagen_perfil") or None,
                "imagen_origen": fila.get("imagen_origen") or None,
                "ranking": ranking.get(
                    fila["slug"],
                    {
                        "indice": None,
                        "audiencia": None,
                        "consumo": None,
                        "rank": None,
                        "total": len(ranking),
                    },
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
    try:
        notificar_todos(
            PushSubscriptionRepository(db),
            "Nuevo proyecto en Frontera Grande",
            f"{artista.nombre} se sumó a la escena.",
            f"/artistas/{artista.slug}",
        )
        db.commit()
    except Exception:
        db.rollback()
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
    analisis = analisis_artista(
        metricas_artista(fila) if fila is not None else {},
        artist.fecha_captura,
    )

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
        "verificado": bool(
            (artist.fb_page_token or artist.tt_refresh_token)
            and artist.estado_registro
        ),
        "ultimo_lanzamiento": _json_safe(artist.ultimo_lanzamiento),
        "ultimo_evento": _json_safe(artist.ultimo_evento),
        "followers": {
            "ig": artist.followers_ig,
            "fb": artist.followers_fb,
            "yt": artist.followers_yt,
            "tt": artist.followers_tt,
            "spotify": artist.followers_spotify,
            "beatport": artist.followers_beatport,
            "mixcloud": artist.followers_mixcloud,
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
            "beatport": {
                "seguidores": artist.followers_beatport,
            },
            "mixcloud": {
                "seguidores": artist.followers_mixcloud,
            },
        },
        "fecha_captura": _json_safe(artist.fecha_captura),
        "ranking": ranking.get(
            artist.slug,
            {
                "indice": None,
                "audiencia": None,
                "consumo": None,
                "rank": None,
                "total": len(ranking),
            },
        ),
        "menciones": menciones.get(artist.slug, []),
        "analisis": analisis,
        "igfb": {
            "configurado": meta_configurado(),
            "conectado": bool(artist.fb_page_token),
            "pagina_fb": artist.fb_page_id or None,
            "ig": artist.ig_user_id or None,
        },
        "tiktok": {
            "configurado": tiktok_configurado(),
            "conectado": bool(artist.tt_refresh_token),
            "user_id": artist.tt_user_id or None,
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


def _requiere_admin(x_admin_token: str) -> None:
    """Levanta 403 si no hay token de admin o no coincide con `ADMIN_PASSWORD`."""
    if not ADMIN_PASSWORD or x_admin_token != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=403, detail="Acción restringida al administrador"
        )


@app.post("/api/admin/events")
def admin_crear_evento(
    entrada: EventoEntrada,
    x_admin_token: str = Header(default=""),
    db: Session = Depends(get_db),
    eventos: EventRepository = Depends(get_event_repo),
):
    """Alta de un evento desde el panel de administración.

    Requiere el `X-Admin-Token`. Tras registrar el evento recalcula la
    actividad de los artistas del cartel (un evento también es señal).
    """
    _requiere_admin(x_admin_token)
    if not entrada.nombre or not entrada.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del evento es obligatorio")
    try:
        evento = eventos.crear(
            nombre=entrada.nombre.strip(),
            fecha=_fecha_desde(entrada.fecha),
            lugar=(entrada.lugar or "").strip(),
            ciudad=(entrada.ciudad or "").strip(),
            artistas=(entrada.artistas or "").strip(),
            que_demuestra=(entrada.que_demuestra or "").strip(),
            fuente=(entrada.fuente or "").strip(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.flush()
    recalcular_actividad(db)
    db.commit()
    return {"ok": True, "id": evento.id}


@app.put("/api/admin/events/{evento_id}")
def admin_editar_evento(
    evento_id: int,
    entrada: EventoEntrada,
    x_admin_token: str = Header(default=""),
    db: Session = Depends(get_db),
    eventos: EventRepository = Depends(get_event_repo),
):
    """Edición de un evento desde el panel de administración.

    Requiere el `X-Admin-Token`. Aplica solo los campos presentes; tras
    guardar recalcula la actividad de los artistas del cartel.
    """
    _requiere_admin(x_admin_token)
    evento = eventos.por_id(evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    campos = entrada.model_dump(exclude_unset=True)
    if "fecha" in campos:
        try:
            campos["fecha"] = _fecha_desde(campos["fecha"])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    try:
        eventos.actualizar(evento, campos)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.flush()
    recalcular_actividad(db)
    db.commit()
    return {"ok": True, "id": evento.id}


@app.delete("/api/admin/events/{evento_id}")
def admin_eliminar_evento(
    evento_id: int,
    x_admin_token: str = Header(default=""),
    db: Session = Depends(get_db),
    eventos: EventRepository = Depends(get_event_repo),
):
    """Elimina un evento desde el panel de administración.

    Requiere el `X-Admin-Token`. Tras borrar recalcula la actividad para que
    los artistas del cartel no conserven la señal del evento eliminado.
    """
    _requiere_admin(x_admin_token)
    evento = eventos.eliminar(evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    db.flush()
    recalcular_actividad(db)
    db.commit()
    return {"ok": True}


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    """Indicadores de la escena para el panel público."""
    return _json_safe(stats_escena(db))


@app.delete("/api/artists/{slug}")
def eliminar_artista_endpoint(
    slug: str,
    x_admin_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Elimina un artista y todo su contenido (solo administración).

    Requiere el `X-Admin-Token` (ADMIN_PASSWORD de `.env`). Borra en cascada
    enlaces, feed, chequeos de actividad y snapshots de Spotify.
    """
    if not ADMIN_PASSWORD or x_admin_token != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=403, detail="Acción restringida al administrador"
        )
    artista = ArtistRepository(db).por_slug(slug)
    if artista is None:
        raise HTTPException(status_code=404, detail="Artista no encontrado")
    db.execute(delete(FeedItem).where(FeedItem.artist_id == artista.id))
    db.execute(
        delete(SpotifyListenerSnapshot).where(
            SpotifyListenerSnapshot.artist_id == artista.id
        )
    )
    db.delete(artista)  # cascada ORM: enlaces y chequeos
    db.commit()
    return {"ok": True}


@app.get("/api/admin/artists")
def admin_list_artists(
    x_admin_token: str = Header(default=""),
    db: Session = Depends(get_db),
    artistas: ArtistRepository = Depends(get_artist_repo),
):
    """Listado de administración: campos editables de todos los artistas.

    Requiere el `X-Admin-Token`. Devuelve los datos crudos (sin tags, sin
    ranking) para el panel de edición: bio, notas, logros, géneros en texto
    plano y enlaces de plataforma.
    """
    if not ADMIN_PASSWORD or x_admin_token != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=403, detail="Acción restringida al administrador"
        )
    lista = []
    for a in artistas.todos():
        lista.append(
            {
                "slug": a.slug,
                "nombre": a.nombre,
                "segmento": a.segmento,
                "ciudad": a.ciudad,
                "generos": a.generos,
                "estado_activo": a.estado_activo,
                "estado_registro": a.estado_registro,
                "es_propio": a.es_propio,
                "bio": a.bio or "",
                "notas": a.notas or "",
                "logros": a.logros or "",
                "imagen_perfil": a.imagen_perfil or None,
                "verificado": bool(
                    (a.fb_page_token or a.tt_refresh_token) and a.estado_registro
                ),
                "links": [
                    {"plataforma": l.plataforma, "url": l.url}
                    for l in a.links
                    if not l.es_busqueda
                ],
            }
        )
    return _json_safe(lista)


@app.put("/api/artists/{slug}")
def editar_artista_endpoint(
    slug: str,
    entrada: EditarArtistaEntrada,
    x_admin_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Edita un artista (solo administración).

    Requiere el `X-Admin-Token`. Aplica solo los campos presentes en el
    cuerpo (`EditarArtistaEntrada`): datos básicos, bio, notas, logros,
    estado de actividad y reemplazo de enlaces de plataforma. Recalcula
    `estado_activo` si cambió la señal que lo alimenta (feed/lanzamiento).
    """
    if not ADMIN_PASSWORD or x_admin_token != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=403, detail="Acción restringida al administrador"
        )
    try:
        artista = editar_artista(
            db, slug, entrada.model_dump(exclude_unset=True)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if artista is None:
        raise HTTPException(status_code=404, detail="Artista no encontrado")
    db.commit()
    return {"ok": True, "slug": artista.slug, "nombre": artista.nombre}


@app.get("/api/genres")
def genres(db: Session = Depends(get_db)):
    df = artistas_df(db)
    return _json_safe(conteo_generos(df).index.tolist())


@app.get("/api/admin/settings")
def admin_get_settings(
    x_admin_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Devuelve la configuración actual del admin (solo lectura)."""
    if not ADMIN_PASSWORD or x_admin_token != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=403, detail="Acción restringida al administrador"
        )
    repo = SettingsRepository(db)
    return {
        "notificar_auto_feed": repo.obtener_bool("notificar_auto_feed"),
        "notificar_auto_verificacion": repo.obtener_bool("notificar_auto_verificacion"),
    }


@app.put("/api/admin/settings")
def admin_put_settings(
    entrada: dict,
    x_admin_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Actualiza la configuración del admin."""
    if not ADMIN_PASSWORD or x_admin_token != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=403, detail="Acción restringida al administrador"
        )
    repo = SettingsRepository(db)
    for key in ("notificar_auto_feed", "notificar_auto_verificacion"):
        if key in entrada:
            repo.guardar(key, "1" if entrada[key] else "0")
    db.commit()
    return {"ok": True}
