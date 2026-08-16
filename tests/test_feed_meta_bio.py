"""Pruebas de la bio desde Meta (backend/feed_meta.py + sync) sin red.

Se sustituye `_grafo` por respuestas de muestra y se verifica el parseo de
`about`/`biography` y la escritura condicionada en el sync de 6 h.
"""

import backend.feed_meta as fm
from backend.feed_meta import ig_bio, pagina_about


def test_pagina_about_usa_description(monkeypatch):
    monkeypatch.setattr(
        fm,
        "_grafo",
        lambda ruta, params: {"description": "Banda desde Reynosa.", "about": "Reynosa"},
    )
    assert pagina_about("123", "tok") == "Banda desde Reynosa."


def test_pagina_about_fallback_about(monkeypatch):
    monkeypatch.setattr(
        fm, "_grafo", lambda ruta, params: {"description": "", "about": "DJ local"}
    )
    assert pagina_about("123", "tok") == "DJ local"


def test_ig_bio(monkeypatch):
    monkeypatch.setattr(fm, "_grafo", lambda ruta, params: {"biography": "DJ y productor."})
    assert ig_bio("456", "tok") == "DJ y productor."


def _artista_fake(bio="", notas="", fb=True, ig=True):
    class Fake:
        pass

    a = Fake()
    a.nombre = "Fake"
    a.bio = bio
    a.notas = notas
    a.fb_page_id = "123" if fb else None
    a.ig_user_id = "456" if ig else None
    a.fb_page_token = "tok"
    return a


def test_escribir_bio_meta_desde_facebook(monkeypatch):
    import scripts.sync_feed_igfb as sync

    a = _artista_fake()
    monkeypatch.setattr(sync, "pagina_about", lambda *_: "Banda de post-punk de Reynosa.")
    monkeypatch.setattr(sync, "ig_bio", lambda *_: "otra")
    sync._escribir_bio_meta(a)
    assert a.bio == "Banda de post-punk de Reynosa."
    assert "Bio de Facebook" in a.notas


def test_escribir_bio_meta_cae_a_instagram(monkeypatch):
    import scripts.sync_feed_igfb as sync

    a = _artista_fake(fb=False, ig=True)
    monkeypatch.setattr(sync, "pagina_about", lambda *_: "")
    monkeypatch.setattr(sync, "ig_bio", lambda *_: "DJ y productor de Matamoros.")
    sync._escribir_bio_meta(a)
    assert a.bio == "DJ y productor de Matamoros."
    assert "Bio de Instagram" in a.notas


def test_escribir_bio_meta_no_escribe_si_plantilla(monkeypatch):
    import scripts.sync_feed_igfb as sync

    a = _artista_fake()
    plantilla = "Share your videos with friends, family, and the world"
    monkeypatch.setattr(sync, "pagina_about", lambda *_: plantilla)
    monkeypatch.setattr(sync, "ig_bio", lambda *_: plantilla)
    sync._escribir_bio_meta(a)
    assert a.bio == ""
    assert a.notas == ""


def test_escribir_bio_meta_respeta_bio_existente(monkeypatch):
    import scripts.sync_feed_igfb as sync

    a = _artista_fake(bio="Ya tengo bio", notas="nota previa")
    sync._escribir_bio_meta(a)
    assert a.bio == "Ya tengo bio"
    assert a.notas == "nota previa"