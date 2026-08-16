"""Repositorios de acceso a datos de la escena local.

Encapsulan las consultas SQLAlchemy para que la presentación (FastAPI) y los
scripts no dependan de SQL directo. Cada repositorio recibe una `Session` en su
constructor: la inyecta `backend/dependencies.py` en la API, o la crea el
propio script cuando se usa desde línea de comandos.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import (
    ActivityCheck,
    Artist,
    ArtistLink,
    Event,
    FeedItem,
    SpotifyListenerSnapshot,
)


class ArtistRepository:
    """Consultas sobre `artists`."""

    def __init__(self, session: Session):
        self.session = session

    def todos(self) -> list[Artist]:
        return self.session.execute(
            select(Artist).order_by(Artist.nombre)
        ).scalars().all()

    def por_slug(self, slug: str) -> Artist | None:
        return self.session.execute(
            select(Artist).where(Artist.slug == slug)
        ).scalar_one_or_none()

    def por_id(self, artist_id: int) -> Artist | None:
        return self.session.get(Artist, artist_id)

    def crear(
        self,
        slug: str,
        nombre: str,
        segmento: str,
        ciudad: str,
        generos: str = "[PENDIENTE]",
        estado_registro: str = "investigado (web)",
        estado_activo: str = "en_duda",
        metodo_actividad: str = "sin datos",
        es_propio: bool = False,
        fecha_registro: date | None = None,
    ) -> Artist:
        """Crea (sin commit) un artista nuevo en la base de datos."""
        artista = Artist(
            slug=slug,
            nombre=nombre,
            segmento=segmento,
            ciudad=ciudad,
            generos=generos,
            estado_registro=estado_registro,
            estado_activo=estado_activo,
            metodo_actividad=metodo_actividad,
            es_propio=es_propio,
            fecha_registro=fecha_registro or date.today(),
        )
        self.session.add(artista)
        return artista

    def conectados_meta(self) -> list[Artist]:
        return self.session.execute(
            select(Artist).where(Artist.fb_page_token.isnot(None))
        ).scalars().all()

    def conectados_tiktok(self) -> list[Artist]:
        return self.session.execute(
            select(Artist).where(Artist.tt_refresh_token.isnot(None))
        ).scalars().all()

    def con_spotify(self) -> list[Artist]:
        """Artistas con un perfil oficial de Spotify registrado."""
        return self.session.execute(
            select(Artist)
            .join(ArtistLink)
            .where(
                ArtistLink.plataforma == "spotify",
                ArtistLink.es_busqueda.is_(False),
                ArtistLink.url != "",
            )
            .distinct()
            .order_by(Artist.nombre)
        ).scalars().all()

    def con_lanzamiento(self) -> list[Artist]:
        return self.session.execute(
            select(Artist).where(Artist.ultimo_lanzamiento.isnot(None))
        ).scalars().all()


class EventRepository:
    """Consultas sobre `events`."""

    def __init__(self, session: Session):
        self.session = session

    def todos_fecha_desc(self) -> list[Event]:
        return self.session.execute(
            select(Event).order_by(Event.fecha.desc())
        ).scalars().all()

    def todos_fecha_asc(self) -> list[Event]:
        return self.session.execute(
            select(Event).order_by(Event.fecha)
        ).scalars().all()

    def de_artista(self, nombre: str) -> list[Event]:
        """Eventos de la escena en cuyo cartel aparece el artista."""
        nombre_bajo = (nombre or "").lower()
        return [
            e for e in self.todos_fecha_desc()
            if nombre_bajo and nombre_bajo in (e.artistas or "").lower()
        ]


class FeedRepository:
    """Consultas y alta de elementos del feed (`feed_items`).

    La desduplicación por URL vive aquí para que la API y los scripts de
    ingesta compartan la misma regla.
    """

    def __init__(self, session: Session):
        self.session = session

    def todos_desc(self, limite: int | None = None) -> list[FeedItem]:
        consulta = select(FeedItem).order_by(FeedItem.created_at.desc())
        if limite:
            consulta = consulta.limit(limite)
        return self.session.execute(consulta).scalars().all()

    def por_url(self, url: str) -> FeedItem | None:
        return self.session.execute(
            select(FeedItem).where(FeedItem.url == url)
        ).scalar_one_or_none()

    def de_artista(self, artist_id: int) -> list[FeedItem]:
        return self.session.execute(
            select(FeedItem).where(FeedItem.artist_id == artist_id)
        ).scalars().all()

    def existe_url(self, url: str) -> bool:
        return self.por_url(url) is not None

    def crear(
        self,
        artist_id: int | None,
        fuente: str,
        tipo: str,
        titulo: str,
        url: str | None,
        fecha: date | None,
        imagen: str | None,
        detalle: str = "",
    ) -> FeedItem:
        item = FeedItem(
            artist_id=artist_id,
            fuente=fuente,
            tipo=tipo,
            titulo=titulo,
            url=url,
            fecha=fecha,
            imagen=imagen,
            detalle=detalle,
        )
        self.session.add(item)
        return item


class LinkRepository:
    """Consultas sobre `artist_links`."""

    def __init__(self, session: Session):
        self.session = session

    def de_artista(self, artist_id: int) -> list[ArtistLink]:
        return self.session.execute(
            select(ArtistLink)
            .where(ArtistLink.artist_id == artist_id)
            .order_by(ArtistLink.plataforma)
        ).scalars().all()

    def crear_para_artista(
        self,
        artista: Artist,
        plataforma: str,
        url: str,
        es_busqueda: bool = False,
    ) -> ArtistLink:
        """Registra (sin commit) un enlace de plataforma para un artista."""
        link = ArtistLink(
            artist=artista,
            plataforma=plataforma,
            url=url,
            es_busqueda=es_busqueda,
        )
        self.session.add(link)
        return link


class SpotifySnapshotRepository:
    """Acceso a capturas históricas de oyentes de Spotify."""

    def __init__(self, session: Session):
        self.session = session

    def crear(
        self,
        artist_id: int,
        url_spotify: str,
        oyentes_mensuales: int | None,
        estado: str = "ok",
        detalle: str = "",
    ) -> SpotifyListenerSnapshot:
        snapshot = SpotifyListenerSnapshot(
            artist_id=artist_id,
            url_spotify=url_spotify,
            oyentes_mensuales=oyentes_mensuales,
            estado=estado,
            detalle=detalle,
        )
        self.session.add(snapshot)
        return snapshot


class ChecksRepository:
    """Consultas sobre `activity_checks` (chequeos del scraper)."""

    def __init__(self, session: Session):
        self.session = session

    def ultimos(self, limite: int = 30) -> list[ActivityCheck]:
        return self.session.execute(
            select(ActivityCheck).order_by(ActivityCheck.fecha_chequeo.desc()).limit(limite)
        ).scalars().all()
