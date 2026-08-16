"""Modelos de la base de datos de la escena local."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# Valores normalizados de categoría (campo interno `segmento`, etiqueta de UI "Categoría")
SEGMENTOS = [
    "Banda",
    "Solista",
    "DJ",
    "Colectivo",
    "Covers",
    "Tributo",
    "Sin confirmar",
]

ESTADOS_ACTIVO = ["activo", "en_duda", "inactivo"]

METODOS_ACTIVIDAD = [
    "evento",
    "lanzamiento",
    "lanzamiento_próximo",
    "presencia_continua",
    "sin datos",
    "artista (EN PAUSA)",
]

PLATAFORMAS = [
    "ig",
    "fb",
    "yt",
    "tt",
    "spotify",
    "bandcamp",
    "soundcloud",
    "beatport",
    "mixcloud",
    "apple",
    "linktree",
    "deezer",
    "web",
    "otro",
]


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    segmento: Mapped[str] = mapped_column(String(60), index=True)
    ciudad: Mapped[str] = mapped_column(String(120), default="[PENDIENTE]")
    generos: Mapped[str] = mapped_column(String(300), default="[PENDIENTE]")
    estado_registro: Mapped[str] = mapped_column(String(80), default="investigado (web)")
    es_propio: Mapped[bool] = mapped_column(Boolean, default=False)

    followers_ig: Mapped[int | None] = mapped_column(Integer, nullable=True)
    followers_fb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    followers_yt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    followers_tt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    followers_spotify: Mapped[int | None] = mapped_column(Integer, nullable=True)
    followers_beatport: Mapped[int | None] = mapped_column(Integer, nullable=True)
    followers_mixcloud: Mapped[int | None] = mapped_column(Integer, nullable=True)
    oyentes_mensuales_spotify: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_oyentes_spotify: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fuente_oyentes_spotify: Mapped[str] = mapped_column(String(80), default="")

    vistas_yt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vistas_tt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reproducciones_spotify: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reproducciones_bandcamp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reproducciones_soundcloud: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_captura: Mapped[datetime | None] = mapped_column(Date, nullable=True)

    ultimo_lanzamiento: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    ultimo_evento: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    estado_activo: Mapped[str] = mapped_column(String(20), default="en_duda", index=True)
    metodo_actividad: Mapped[str] = mapped_column(String(60), default="sin datos")

    logros: Mapped[str] = mapped_column(Text, default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    notas: Mapped[str] = mapped_column(Text, default="")

    imagen_perfil: Mapped[str | None] = mapped_column(String(500), nullable=True)
    imagen_origen: Mapped[str | None] = mapped_column(String(30), nullable=True)
    imagen_actualizada: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fecha_registro: Mapped[datetime | None] = mapped_column(Date, nullable=True)

    fb_page_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fb_page_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ig_user_id: Mapped[str | None] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    links: Mapped[list["ArtistLink"]] = relationship(
        back_populates="artist",
        cascade="all, delete-orphan",
        order_by="ArtistLink.plataforma",
    )
    checks: Mapped[list["ActivityCheck"]] = relationship(
        back_populates="artist", cascade="all, delete-orphan"
    )


class ArtistLink(Base):
    __tablename__ = "artist_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), index=True)
    plataforma: Mapped[str] = mapped_column(String(30), index=True)
    url: Mapped[str] = mapped_column(String(500))
    es_busqueda: Mapped[bool] = mapped_column(Boolean, default=False)
    nota: Mapped[str] = mapped_column(String(300), default="")

    artist: Mapped["Artist"] = relationship(back_populates="links")


class SpotifyListenerSnapshot(Base):
    """Captura histórica de oyentes mensuales del perfil público de Spotify."""

    __tablename__ = "spotify_listener_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    oyentes_mensuales: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url_spotify: Mapped[str] = mapped_column(String(500))
    fuente: Mapped[str] = mapped_column(String(80), default="spotify_public_profile")
    estado: Mapped[str] = mapped_column(String(20), default="ok")
    detalle: Mapped[str] = mapped_column(Text, default="")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    fecha: Mapped[datetime | None] = mapped_column(Date, nullable=True, index=True)
    lugar: Mapped[str] = mapped_column(String(200), default="")
    ciudad: Mapped[str] = mapped_column(String(120), default="")
    artistas: Mapped[str] = mapped_column(String(400), default="")
    que_demuestra: Mapped[str] = mapped_column(Text, default="")
    fuente: Mapped[str] = mapped_column(String(300), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ActivityCheck(Base):
    """Registro de un chequeo de actividad del scraper (snapshot)."""

    __tablename__ = "activity_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), index=True)
    fecha_chequeo: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    plataforma: Mapped[str] = mapped_column(String(40), default="web")
    metodo: Mapped[str] = mapped_column(String(60), default="http")
    resultado: Mapped[str] = mapped_column(String(20))  # ok / fallo / error / sin_datos
    detalle: Mapped[str] = mapped_column(Text, default="")
    latencia_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    link_id: Mapped[int | None] = mapped_column(
        ForeignKey("artist_links.id"), nullable=True
    )

    artist: Mapped["Artist"] = relationship(back_populates="checks")


class FeedItem(Base):
    """Elemento del feed: contenido reciente detectado de los proyectos.

    Puede venir de un adaptador (ej. YouTube) o del registro interno
    (eventos, lanzamientos, chequeos).
    """

    __tablename__ = "feed_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artist_id: Mapped[int | None] = mapped_column(
        ForeignKey("artists.id"), nullable=True, index=True
    )
    fuente: Mapped[str] = mapped_column(String(40), index=True)  # youtube, escena, scraper...
    tipo: Mapped[str] = mapped_column(String(30), index=True)  # video, lanzamiento, evento, error
    titulo: Mapped[str] = mapped_column(String(300))
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fecha: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    imagen: Mapped[str | None] = mapped_column(Text, nullable=True)
    detalle: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    artist: Mapped["Artist"] = relationship()
