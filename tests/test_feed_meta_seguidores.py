"""Pruebas de los seguidores FB/IG desde Meta (backend/feed_meta.py + sync).

Se sustituye `_grafo` por respuestas de muestra y se verifica que el sync
escribe `followers_fb`/`followers_ig` solo cuando la API entrega un valor
(nunca pisa con None) y marca `fecha_captura`.
"""

from datetime import date

import backend.feed_meta as fm
from backend.feed_meta import ig_seguidores, pagina_seguidores


def test_pagina_seguidores(monkeypatch):
    monkeypatch.setattr(
        fm, "_grafo", lambda ruta, params: {"followers_count": 1234}
    )
    assert pagina_seguidores("123", "tok") == 1234


def test_pagina_seguidores_sin_campo(monkeypatch):
    monkeypatch.setattr(fm, "_grafo", lambda ruta, params: {"id": "123"})
    assert pagina_seguidores("123", "tok") is None


def test_ig_seguidores(monkeypatch):
    monkeypatch.setattr(
        fm, "_grafo", lambda ruta, params: {"followers_count": 987}
    )
    assert ig_seguidores("456", "tok") == 987


def _artista_fake(fb=True, ig=True, followers_fb=None, followers_ig=None):
    class Fake:
        pass

    a = Fake()
    a.nombre = "Fake"
    a.fb_page_id = "123" if fb else None
    a.ig_user_id = "456" if ig else None
    a.fb_page_token = "tok"
    a.followers_fb = followers_fb
    a.followers_ig = followers_ig
    a.fecha_captura = None
    return a


def test_sync_escribe_seguidores_y_fecha(monkeypatch):
    import scripts.sync_feed_igfb as sync

    a = _artista_fake()
    monkeypatch.setattr(sync, "pagina_seguidores", lambda *_: 100)
    monkeypatch.setattr(sync, "ig_seguidores", lambda *_: 200)
    sync._actualizar_seguidores_meta(a)
    assert a.followers_fb == 100
    assert a.followers_ig == 200
    assert a.fecha_captura == date.today()


def test_sync_no_pisa_con_none(monkeypatch):
    import scripts.sync_feed_igfb as sync

    a = _artista_fake(followers_fb=100, followers_ig=200)
    monkeypatch.setattr(sync, "pagina_seguidores", lambda *_: None)
    monkeypatch.setattr(sync, "ig_seguidores", lambda *_: None)
    sync._actualizar_seguidores_meta(a)
    assert a.followers_fb == 100
    assert a.followers_ig == 200
    assert a.fecha_captura is None


def test_sync_tolerante_a_errores(monkeypatch):
    import scripts.sync_feed_igfb as sync

    a = _artista_fake(followers_fb=100)

    def falla(*_):
        raise RuntimeError("Graph API caída")

    monkeypatch.setattr(sync, "pagina_seguidores", falla)
    monkeypatch.setattr(sync, "ig_seguidores", lambda *_: 300)
    sync._actualizar_seguidores_meta(a)
    assert a.followers_fb == 100
    assert a.followers_ig == 300
    assert a.fecha_captura == date.today()
