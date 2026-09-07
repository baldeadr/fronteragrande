"""Pruebas de la suma de métricas cuando un artista tiene varios canales de
YouTube oficiales (cuentas duplicadas vigentes)."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db.models import Artist, ArtistLink, Base


def _artista_con_dos_canales(session):
    artista = Artist(
        slug="dos_canales",
        nombre="Dos Canales",
        segmento="Banda",
        ciudad="Reynosa",
    )
    artista.links = [
        ArtistLink(plataforma="yt", url="https://www.youtube.com/@canal-a"),
        ArtistLink(plataforma="yt", url="https://www.youtube.com/@canal-b"),
    ]
    session.add(artista)
    session.commit()
    return artista


def test_sync_suma_dos_canales(monkeypatch, tmp_path):
    """Suscriptores y vistas de dos canales oficiales se suman en el artista."""
    import scripts.sync_youtube_stats as sync

    engine = create_engine(f"sqlite:///{tmp_path}/yt.db")
    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine)

    s = Sesion()
    _artista_con_dos_canales(s)
    s.close()

    def channel_id_from_url(url):
        return "UC-A" if "@canal-a" in url else "UC-B"

    def channel_statistics(channel_id, api_key):
        if channel_id == "UC-A":
            return {"suscriptores": 5000, "vistas": 100_000, "videos": 30}
        return {"suscriptores": 2000, "vistas": 70_000, "videos": 10}

    monkeypatch.setattr(sync, "channel_id_from_url", channel_id_from_url)
    monkeypatch.setattr(sync, "channel_statistics", channel_statistics)
    monkeypatch.setattr(sync, "SessionLocal", lambda: Sesion())

    actualizados, errores = sync.sincronizar("clave")
    assert actualizados == 1
    assert errores == 0

    s = Sesion()
    try:
        artista = s.execute(
            select(Artist).where(Artist.slug == "dos_canales")
        ).scalar_one()
        assert artista.followers_yt == 7000
        assert artista.vistas_yt == 170_000
    finally:
        s.close()


def test_sync_con_canal_muerto_suma_los_demas(monkeypatch, tmp_path):
    """Si un canal falla, la suma conserva las métricas de los canales vivos."""
    import scripts.sync_youtube_stats as sync
    from scraper.errors import ScraperError

    engine = create_engine(f"sqlite:///{tmp_path}/yt2.db")
    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine)

    s = Sesion()
    _artista_con_dos_canales(s)
    s.close()

    def channel_id_from_url(url):
        return "UC-A" if "@canal-a" in url else "UC-B"

    def channel_statistics(channel_id, api_key):
        if channel_id == "UC-A":
            return {"suscriptores": 5000, "vistas": 100_000, "videos": 30}
        raise ScraperError("canal caído")

    monkeypatch.setattr(sync, "channel_id_from_url", channel_id_from_url)
    monkeypatch.setattr(sync, "channel_statistics", channel_statistics)
    monkeypatch.setattr(sync, "SessionLocal", lambda: Sesion())

    actualizados, errores = sync.sincronizar("clave")
    assert actualizados == 1
    assert errores == 0

    s = Sesion()
    try:
        artista = s.execute(
            select(Artist).where(Artist.slug == "dos_canales")
        ).scalar_one()
        assert artista.followers_yt == 5000
        assert artista.vistas_yt == 100_000
    finally:
        s.close()