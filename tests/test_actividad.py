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