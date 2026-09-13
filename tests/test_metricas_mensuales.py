"""Pruebas del historial mensual de métricas (`metric_snapshots`).

Cubre el repositorio (dedupe consecutivo y fila-ancla con `forzar`), la
agregación mensual con carry-forward, el endpoint `GET /api/artists/{slug}/metricas`
y la construcción de hitos desde feed/eventos. Usa un artista real de la BD
sembrada y limpia lo que inserta para no contaminar la sesión compartida.
"""

from datetime import datetime

from db.models import Artist, Event, FeedItem
from lib.repository import ArtistRepository, MetricSnapshotRepository
from lib.servicios import hitos_artista, metricas_mensuales, registrar_snapshots

SLUG = "alexis_mvgler"


def _artista(session) -> Artist:
    artista = ArtistRepository(session).por_slug(SLUG)
    assert artista is not None
    return artista


def _limpiar_snapshots(session, artista_id: int):
    for s in MetricSnapshotRepository(session).serie(artista_id):
        session.delete(s)
    session.commit()


def _en_mes(anio: int, mes: int, dia: int) -> datetime:
    return datetime(anio, mes, dia)


def _meses_atras(ahora: datetime, n: int) -> datetime:
    total = ahora.year * 12 + (ahora.month - 1) - n
    return _en_mes(total // 12, total % 12 + 1, 10)


def test_registrar_snapshots_dedupe_consecutivo(session):
    artista = _artista(session)
    repo = MetricSnapshotRepository(session)
    medidas = [{"plataforma": "ig", "metrica": "seguidores", "valor": 1234}]
    try:
        assert registrar_snapshots(session, artista.id, medidas) == 1
        session.flush()
        # Mismo valor seguido → se omite.
        assert registrar_snapshots(session, artista.id, medidas) == 0
        # Cambio de valor → nueva fila.
        assert (
            registrar_snapshots(
                session,
                artista.id,
                [{"plataforma": "ig", "metrica": "seguidores", "valor": 1300}],
            )
            == 1
        )
        session.commit()
        serie = repo.serie(artista.id)
        assert len(serie) == 2
        assert serie[-1].valor == 1300
        assert repo.ultimo(artista.id, "ig", "seguidores").valor == 1300
    finally:
        _limpiar_snapshots(session, artista.id)


def test_registrar_snapshots_forzar_escribe_fila_ancla(session):
    artista = _artista(session)
    repo = MetricSnapshotRepository(session)
    medidas = [
        {"plataforma": "spotify", "metrica": "oyentes_mensuales", "valor": 5000}
    ]
    try:
        # Con forzar se escribe aunque el valor no cambió (ancla mensual).
        assert registrar_snapshots(session, artista.id, medidas, forzar=True) == 1
        assert registrar_snapshots(session, artista.id, medidas, forzar=True) == 1
        session.commit()
        serie = repo.serie(artista.id)
        assert len(serie) == 2
        assert all(s.valor == 5000 for s in serie)
    finally:
        _limpiar_snapshots(session, artista.id)


def test_metricas_mensuales_agrega_ultimo_y_rellena(session):
    artista = _artista(session)
    repo = MetricSnapshotRepository(session)
    ahora = datetime.utcnow()
    prev2 = _meses_atras(ahora, 2)
    prev1 = _meses_atras(ahora, 1)
    try:
        # Dos capturas en el mismo mes: cuenta la de cierre del mes (día 20).
        repo.crear(artista.id, "yt", "seguidores", 900, capturado_en=prev2)
        repo.crear(artista.id, "yt", "seguidores", 1200, capturado_en=_en_mes(prev1.year, prev1.month, 5))
        repo.crear(artista.id, "yt", "seguidores", 1000, capturado_en=_en_mes(prev1.year, prev1.month, 20))
        repo.crear(artista.id, "yt", "seguidores", 1500, capturado_en=ahora)
        session.commit()
        serie = metricas_mensuales(session, artista.id)["yt"]["seguidores"]
        assert len(serie) == 3
        assert serie[0]["mes"] == prev2.strftime("%Y-%m")
        assert serie[0]["valor"] == 900
        assert serie[0]["primera_captura"] is True
        assert serie[1]["valor"] == 1000
        assert serie[-1]["mes"] == ahora.strftime("%Y-%m")
        assert serie[-1]["valor"] == 1500
        assert serie[-1]["primera_captura"] is False
    finally:
        _limpiar_snapshots(session, artista.id)


def test_metricas_mensuales_vacio_sin_capturas(session):
    artista = _artista(session)
    assert metricas_mensuales(session, artista.id) == {}


def test_hitos_artista_desde_feed_y_eventos(session):
    artista = _artista(session)
    hoy = datetime.utcnow()
    lanzamiento = FeedItem(
        artist_id=artista.id,
        fuente="test",
        tipo="lanzamiento",
        titulo="ME PONGO",
        url="https://example.com/lanzamiento",
        fecha=hoy,
    )
    video = FeedItem(
        artist_id=artista.id,
        fuente="test",
        tipo="video",
        titulo="Sesión en vivo",
        url="https://www.youtube.com/watch?v=abc123",
        fecha=hoy,
    )
    toquin = Event(
        nombre="Toquín en Juana Gallo",
        fecha=hoy.date(),
        lugar="Juana Gallo",
        ciudad="Zacatecas",
        artistas=artista.nombre,
        que_demuestra="",
        fuente="test",
    )
    session.add_all([lanzamiento, video, toquin])
    session.commit()
    try:
        hitos = hitos_artista(session, artista)
        tipos = {h["tipo"] for h in hitos}
        assert "lanzamiento" in tipos
        assert "videoclip" in tipos
        assert "toquín" in tipos
        for h in hitos:
            assert "titulo" in h and "fecha" in h
            assert h["url"] is None or isinstance(h["url"], str)
    finally:
        for obj in (lanzamiento, video, toquin):
            session.delete(obj)
        session.commit()


def test_endpoint_artista_metricas(client, session):
    artista = _artista(session)
    try:
        # Registramos una captura propia y verificamos que la API la exponga.
        registrar_snapshots(
            session,
            artista.id,
            [{"plataforma": "ig", "metrica": "seguidores", "valor": 333}],
        )
        session.commit()
        resp = client.get(f"/api/artists/{SLUG}/metricas")
        assert resp.status_code == 200
        datos = resp.json()
        assert datos["slug"] == SLUG
        assert datos["historial"]["ig"]["seguidores"][-1]["valor"] == 333
        assert isinstance(datos["hitos"], list)
        for h in datos["hitos"]:
            assert h["tipo"] in {"lanzamiento", "videoclip", "toquín"}
    finally:
        _limpiar_snapshots(session, artista.id)


def test_endpoint_artista_metricas_404(client):
    resp = client.get("/api/artists/no-existe-xyz/metricas")
    assert resp.status_code == 404