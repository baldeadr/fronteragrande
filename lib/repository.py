"""Repositorios de acceso a datos de la escena local.

Encapsulan las consultas SQLAlchemy para que la presentación (FastAPI) y los
scripts no dependan de SQL directo. Cada repositorio recibe una `Session` en su
constructor: la inyecta `backend/dependencies.py` en la API, o la crea el
propio script cuando se usa desde línea de comandos.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from db.models import (
    ActivityCheck,
    Artist,
    ArtistLink,
    Event,
    FeedItem,
    MetricSnapshot,
    PushSubscription,
    Setting,
    SpotifyListenerSnapshot,
)


class ArtistRepository:
    """Consultas sobre `artists`."""

    def __init__(self, session: Session):
        self.session = session

    def todos(self, con_links: bool = False) -> list[Artist]:
        consulta = select(Artist).order_by(Artist.nombre)
        if con_links:
            consulta = consulta.options(selectinload(Artist.links))
        return self.session.execute(consulta).scalars().all()

    def por_slug(self, slug: str) -> Artist | None:
        return self.session.execute(
            select(Artist).where(Artist.slug == slug)
        ).scalar_one_or_none()

    def por_id(self, artist_id: int) -> Artist | None:
        return self.session.get(Artist, artist_id)

    def por_nombre(self, nombre: str) -> Artist | None:
        return self.session.execute(
            select(Artist).where(Artist.nombre == nombre)
        ).scalar_one_or_none()

    def por_nombre_insensible(self, nombre: str) -> Artist | None:
        return self.session.execute(
            select(Artist).where(func.lower(Artist.nombre) == nombre.strip().lower())
        ).scalar_one_or_none()

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
            .distinct(Artist.id)
            .order_by(Artist.id, Artist.nombre)
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
        if not nombre_bajo:
            return []
        return self.session.execute(
            select(Event)
            .where(func.lower(Event.artistas).like(f"%{nombre_bajo}%"))
            .order_by(Event.fecha.desc())
        ).scalars().all()

    def por_id(self, evento_id: int) -> Event | None:
        return self.session.execute(
            select(Event).where(Event.id == evento_id)
        ).scalar_one_or_none()

    def por_fuente(self, fuente: str) -> Event | None:
        """Evento ya registrado desde una fuente externa (desduplicación)."""
        if not fuente:
            return None
        return self.session.execute(
            select(Event).where(Event.fuente == fuente)
        ).scalar_one_or_none()

    def crear(
        self,
        nombre: str,
        fecha: date | None,
        lugar: str,
        ciudad: str,
        artistas: str,
        que_demuestra: str,
        fuente: str,
    ) -> Event:
        evento = Event(
            nombre=nombre,
            fecha=fecha,
            lugar=lugar,
            ciudad=ciudad,
            artistas=artistas,
            que_demuestra=que_demuestra,
            fuente=fuente,
        )
        self.session.add(evento)
        return evento

    def actualizar(self, evento: Event, campos: dict) -> Event:
        """Aplica los campos presentes del dict al evento (sin pisar los ausentes)."""
        for campo in (
            "nombre",
            "fecha",
            "lugar",
            "ciudad",
            "artistas",
            "que_demuestra",
            "fuente",
        ):
            if campo in campos and campos[campo] is not None:
                setattr(evento, campo, campos[campo])
        return evento

    def eliminar(self, evento_id: int) -> Event | None:
        evento = self.por_id(evento_id)
        if evento is not None:
            self.session.delete(evento)
        return evento

    def proximos(self, desde: date) -> list[Event]:
        """Eventos con fecha >= desde, ordenados cronológicamente."""
        return self.session.execute(
            select(Event)
            .where(Event.fecha >= desde)
            .order_by(Event.fecha)
        ).scalars().all()


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

    def de_artista_desc(
        self,
        artist_id: int,
        limite: int | None = None,
        desde: date | None = None,
    ) -> list[FeedItem]:
        """Feed de un artista, filtrado y ordenado en la base de datos."""
        consulta = (
            select(FeedItem)
            .where(FeedItem.artist_id == artist_id)
            .order_by(FeedItem.created_at.desc())
        )
        if desde is not None:
            consulta = consulta.where(
                func.coalesce(FeedItem.fecha, FeedItem.created_at) >= desde
            )
        if limite:
            consulta = consulta.limit(limite)
        return self.session.execute(consulta).scalars().all()

    def por_url(self, url: str) -> FeedItem | None:
        return self.session.execute(
            select(FeedItem).where(FeedItem.url == self._url_canonica(url))
        ).scalar_one_or_none()

    @staticmethod
    def _url_canonica(url: str) -> str:
        """Normaliza la URL de un ítem de feed para la des-duplicación.

        Los enlaces de YouTube admiten varias formas del mismo video
        (`watch?v=<id>`, `/shorts/<id>`, `/embed/<id>`, `youtu.be/<id>`)
        que YouTube alterna según el tipo de contenido y la época. Como la
        identidad de un ítem es su URL, se declara canónica la forma
        `https://www.youtube.com/watch?v=<id>` para que la misma pieza no se
        duplique al cambiar de formato.
        """
        from lib.helpers import youtube_video_id

        vid = youtube_video_id(url)
        if vid:
            return f"https://www.youtube.com/watch?v={vid}"
        return url

    def de_artista(self, artist_id: int) -> list[FeedItem]:
        return self.session.execute(
            select(FeedItem).where(FeedItem.artist_id == artist_id)
        ).scalars().all()

    def ultimo_contenido_de_artista(
        self, artist_id: int
    ) -> FeedItem | None:
        """Elemento de contenido más reciente de un artista (sin chequeos).

        Se ordena por la fecha de publicación (con fallback a la de creación)
        y no por `created_at`: si un respaldo inserta elementos viejos después
        de los nuevos, el recálculo de actividad no debe tomarlos como señal.
        """
        return self.session.execute(
            select(FeedItem)
            .where(
                FeedItem.artist_id == artist_id,
                FeedItem.tipo.in_(["video", "lanzamiento", "post", "evento"]),
            )
            .order_by(func.coalesce(FeedItem.fecha, FeedItem.created_at).desc())
            .limit(1)
        ).scalar_one_or_none()

    def serie_mensual(
        self,
        meses: int = 12,
        excluir_fuentes: list[str] | None = None,
    ) -> list[dict]:
        """Conteo de ítems por mes, opcionalmente excluyendo fuentes."""
        columna = func.coalesce(FeedItem.fecha, FeedItem.created_at)
        mes = (
            func.to_char(columna, "YYYY-MM")
            if self.session.bind.dialect.name == "postgresql"
            else func.strftime("%Y-%m", columna)
        )
        consulta = select(
            mes.label("mes"),
            func.count().label("conteo"),
        )
        if excluir_fuentes:
            consulta = consulta.where(FeedItem.fuente.notin_(excluir_fuentes))
        consulta = consulta.group_by("mes").order_by("mes")
        filas = self.session.execute(consulta).all()
        return self._completar_serie(filas, meses)

    def conteo_reciente(
        self,
        dias: int,
        excluir_fuentes: list[str] | None = None,
    ) -> int:
        """Cantidad de ítems de los últimos N días."""
        columna = func.coalesce(FeedItem.fecha, FeedItem.created_at)
        desde = datetime.utcnow() - timedelta(days=dias)
        consulta = select(func.count()).where(columna >= desde)
        if excluir_fuentes:
            consulta = consulta.where(FeedItem.fuente.notin_(excluir_fuentes))
        return self.session.execute(consulta).scalar() or 0

    @staticmethod
    def _completar_serie(filas, meses: int) -> list[dict]:
        desde = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        periodos = []
        for i in range(meses - 1, -1, -1):
            mes = desde.month - i
            anio = desde.year
            while mes <= 0:
                mes += 12
                anio -= 1
            periodos.append(datetime(anio, mes, 1))
        datos = {fila.mes: fila.conteo for fila in filas}
        return [
            {"mes": p.strftime("%Y-%m"), "año": p.year, "conteo": datos.get(p.strftime("%Y-%m"), 0)}
            for p in periodos
        ]

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

    def crear_si_nuevo(
        self, artist_id: int, fuente: str, tipo: str, item: dict
    ) -> bool:
        """Crea un FeedItem desde un dict normalizado si su URL no existe.

        `item` lleva las claves `url`, `titulo`, `fecha` e `imagen` (el
        formato común de los adaptadores). Devuelve True solo si lo creó:
        la regla anti-duplicados vive en un solo lugar para todos los syncs.
        """
        url = item.get("url") or ""
        if not url or self.existe_url(url):
            return False
        url = self._url_canonica(url)
        self.crear(
            artist_id=artist_id,
            fuente=fuente,
            tipo=tipo,
            titulo=(item.get("titulo") or "")[:200],
            url=url,
            fecha=item.get("fecha"),
            imagen=item.get("imagen") or None,
            detalle="",
        )
        return True


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

    def url_ya_vinculada(
        self, url: str, excluir_artist_id: int | None = None
    ) -> ArtistLink | None:
        """Devuelve el primer enlace cuya URL canónica coincida con `url`.

        Ignora enlaces de búsqueda (`es_busqueda`). Se puede excluir un
        artista para permitir re-editar sus propios enlaces.
        """
        from lib.helpers import normalizar_url_para_duplicados

        canon = normalizar_url_para_duplicados(url)
        if not canon:
            return None
        stmt = select(ArtistLink).where(
            ArtistLink.es_busqueda.is_(False),
            ArtistLink.url != "",
        )
        if excluir_artist_id is not None:
            stmt = stmt.where(ArtistLink.artist_id != excluir_artist_id)
        for link in self.session.execute(stmt).scalars().all():
            if normalizar_url_para_duplicados(link.url) == canon:
                return link
        return None

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


class MetricSnapshotRepository:
    """Acceso a capturas históricas de métricas (`metric_snapshots`).

    Cada fila es una captura × métrica. El dedupe consecutivo se resuelve en
    `lib.servicios.registrar_snapshots` comparando con `ultimo`.
    """

    def __init__(self, session: Session):
        self.session = session

    def ultimo(
        self, artist_id: int, plataforma: str, metrica: str
    ) -> MetricSnapshot | None:
        """Última captura de una métrica (para decidir si hubo cambio)."""
        return self.session.execute(
            select(MetricSnapshot)
            .where(
                MetricSnapshot.artist_id == artist_id,
                MetricSnapshot.plataforma == plataforma,
                MetricSnapshot.metrica == metrica,
            )
            .order_by(MetricSnapshot.capturado_en.desc(), MetricSnapshot.id.desc())
            .limit(1)
        ).scalar_one_or_none()

    def crear(
        self,
        artist_id: int,
        plataforma: str,
        metrica: str,
        valor: int,
        fuente: str = "",
        capturado_en: datetime | None = None,
    ) -> MetricSnapshot:
        snapshot = MetricSnapshot(
            artist_id=artist_id,
            plataforma=plataforma,
            metrica=metrica,
            valor=valor,
            fuente=fuente,
            capturado_en=capturado_en or datetime.utcnow(),
        )
        self.session.add(snapshot)
        return snapshot

    def serie(self, artist_id: int) -> list[MetricSnapshot]:
        """Todas las capturas de un artista, cronológicas."""
        return self.session.execute(
            select(MetricSnapshot)
            .where(MetricSnapshot.artist_id == artist_id)
            .order_by(MetricSnapshot.capturado_en.asc(), MetricSnapshot.id.asc())
        ).scalars().all()


class ChecksRepository:
    """Consultas sobre `activity_checks` (chequeos del scraper)."""

    def __init__(self, session: Session):
        self.session = session

    def ultimos(self, limite: int = 30) -> list[ActivityCheck]:
        return self.session.execute(
            select(ActivityCheck).order_by(ActivityCheck.fecha_chequeo.desc()).limit(limite)
        ).scalars().all()

    def ultimos_de_artista(
        self, artist_id: int, limite: int = 30
    ) -> list[ActivityCheck]:
        return self.session.execute(
            select(ActivityCheck)
            .where(ActivityCheck.artist_id == artist_id)
            .order_by(ActivityCheck.fecha_chequeo.desc())
            .limit(limite)
        ).scalars().all()


class PushSubscriptionRepository:
    """Suscripciones Web Push de dispositivos (`push_subscriptions`)."""

    def __init__(self, session: Session):
        self.session = session

    def guardar(
        self, endpoint: str, keys_p256dh: str, keys_auth: str
    ) -> PushSubscription:
        """Crea la suscripción o actualiza sus llaves si el endpoint ya existe."""
        sub = self.session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        ).scalar_one_or_none()
        if sub is None:
            sub = PushSubscription(
                endpoint=endpoint,
                keys_p256dh=keys_p256dh,
                keys_auth=keys_auth,
            )
            self.session.add(sub)
        else:
            sub.keys_p256dh = keys_p256dh
            sub.keys_auth = keys_auth
        return sub

    def por_endpoint(self, endpoint: str) -> PushSubscription | None:
        return self.session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        ).scalar_one_or_none()

    def todos(self) -> list[PushSubscription]:
        return self.session.execute(
            select(PushSubscription).order_by(PushSubscription.created_at)
        ).scalars().all()

    def eliminar(self, endpoint: str) -> bool:
        sub = self.por_endpoint(endpoint)
        if sub is None:
            return False
        self.session.delete(sub)
        return True


class SettingsRepository:
    """Configuración clave-valor del admin (`settings`)."""

    def __init__(self, session: Session):
        self.session = session

    def obtener(self, key: str, default: str = "") -> str:
        row = self.session.execute(
            select(Setting).where(Setting.key == key)
        ).scalar_one_or_none()
        return row.value if row else default

    def obtener_bool(self, key: str, default: bool = False) -> bool:
        val = self.obtener(key, "").lower()
        if not val:
            return default
        return val in ("1", "true", "yes", "on")

    def guardar(self, key: str, value: str) -> Setting:
        row = self.session.execute(
            select(Setting).where(Setting.key == key)
        ).scalar_one_or_none()
        if row is None:
            row = Setting(key=key, value=value)
            self.session.add(row)
        else:
            row.value = value
        return row
