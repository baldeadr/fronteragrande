"""Pruebas puras de la regla de actividad (scraper/core.py)."""

from datetime import date, timedelta
from types import SimpleNamespace

from scraper.core import (
    DIAS_ACTIVO,
    DIAS_EN_DUDA,
    dias_desde,
    estado_activo_recomputado,
    ultimo_referencia,
)


def _artista(**kwargs):
    base = dict(
        metodo_actividad="sin datos",
        ultimo_lanzamiento=None,
        ultimo_evento=None,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_pausa_marca_inactivo():
    artista = _artista(metodo_actividad="artista (EN PAUSA)")
    assert estado_activo_recomputado(artista) == "inactivo"


def test_metodos_que_cuentan_activo():
    for metodo in ("lanzamiento_próximo", "presencia_continua"):
        artista = _artista(metodo_actividad=metodo)
        assert estado_activo_recomputado(artista) == "activo"


def test_sin_senales_en_duda():
    assert estado_activo_recomputado(_artista()) == "en_duda"


def test_lanzamiento_reciente_activo():
    artista = _artista(ultimo_lanzamiento=date.today() - timedelta(days=5))
    assert estado_activo_recomputado(artista) == "activo"


def test_evento_reciente_activo():
    artista = _artista(ultimo_evento=date.today() - timedelta(days=30))
    assert estado_activo_recomputado(artista) == "activo"


def test_feed_cuenta_como_senal():
    artista = _artista()
    hoy = date.today() - timedelta(days=1)
    assert estado_activo_recomputado(artista, ultimo_feed=hoy) == "activo"


def test_limites_de_dias():
    ref_lanzamiento = date.today() - timedelta(days=DIAS_ACTIVO)
    assert estado_activo_recomputado(_artista(ultimo_lanzamiento=ref_lanzamiento)) == "activo"

    ref_en_duda = date.today() - timedelta(days=DIAS_ACTIVO + 1)
    assert estado_activo_recomputado(_artista(ultimo_lanzamiento=ref_en_duda)) == "en_duda"

    ref_en_duda_max = date.today() - timedelta(days=DIAS_EN_DUDA)
    assert estado_activo_recomputado(_artista(ultimo_lanzamiento=ref_en_duda_max)) == "en_duda"


def test_mas_de_18_meses_inactivo():
    artista = _artista(ultimo_lanzamiento=date.today() - timedelta(days=DIAS_EN_DUDA + 1))
    assert estado_activo_recomputado(artista) == "inactivo"


def test_senal_mas_reciente_gana():
    artista = _artista(
        ultimo_lanzamiento=date.today() - timedelta(days=700),
        ultimo_evento=date.today() - timedelta(days=10),
    )
    assert estado_activo_recomputado(artista) == "activo"


def test_dias_desde():
    assert dias_desde(None) is None
    assert dias_desde(date.today()) == 0
    assert dias_desde(date.today() - timedelta(days=3)) == 3


def test_ultimo_referencia():
    # Comportamiento actual: prefiere `ultimo_lanzamiento` sobre `ultimo_evento`.
    artista = _artista(
        ultimo_lanzamiento=date(2026, 1, 1),
        ultimo_evento=date(2026, 2, 1),
    )
    assert ultimo_referencia(artista) == date(2026, 1, 1)
    solo_evento = _artista(ultimo_evento=date(2026, 2, 1))
    assert ultimo_referencia(solo_evento) == date(2026, 2, 1)
    assert ultimo_referencia(_artista()) is None


def test_ultimo_feed_por_fecha_publicacion(session):
    """Un elemento viejo insertado tarde no gana a uno reciente.

    Regresión (caso Cada Martes, 2026-08): `ultimo_contenido_de_artista`
    ordenaba por `created_at`, así que un respaldo que insertaba
    publicaciones viejas al final dejaba artistas activos como inactivo.
    """
    from datetime import datetime

    from db.models import FeedItem
    from lib.repository import ArtistRepository, FeedRepository
    from lib.servicios import ultimo_feed_de_artista

    artista = ArtistRepository(session).todos()[0]
    insercion = datetime(2026, 8, 20, 12, 0, 0)
    items = [
        FeedItem(
            artist_id=artista.id,
            fuente="spotify",
            tipo="lanzamiento",
            titulo="reciente",
            url="https://test/regresion/reciente",
            fecha=datetime(2026, 8, 14),
            created_at=insercion,
        ),
        FeedItem(
            artist_id=artista.id,
            fuente="soundcloud",
            tipo="lanzamiento",
            titulo="viejo",
            url="https://test/regresion/viejo",
            fecha=datetime(2024, 10, 17),
            created_at=insercion.replace(hour=13),
        ),
    ]
    session.add_all(items)
    session.commit()
    try:
        senal = ultimo_feed_de_artista(session, artista)
        assert senal == items[0].fecha.date()
        elegido = FeedRepository(session).ultimo_contenido_de_artista(artista.id)
        assert elegido.url == "https://test/regresion/reciente"
    finally:
        for it in items:
            session.delete(it)
        session.commit()