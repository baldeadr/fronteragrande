"""Pruebas de los extractores de foto de perfil vía API (sin red)."""

import requests as requests_real

from scraper.adapters import imagenes


class Respuesta:
    def __init__(self, status_code=200, url="", json_data=None):
        self.status_code = status_code
        self.url = url
        self._json = json_data

    def json(self):
        return self._json


class LinkFake:
    def __init__(self, plataforma, url, es_busqueda=False):
        self.plataforma = plataforma
        self.url = url
        self.es_busqueda = es_busqueda


def test_meta_picture_devuelve_url_final(monkeypatch):
    capturado = {}

    def get(url, **kw):
        capturado.update(kw)
        return Respuesta(url="https://scontent.xx/fb.jpg")

    monkeypatch.setattr(imagenes.requests, "get", get)
    assert imagenes.meta_picture("123", "tok") == "https://scontent.xx/fb.jpg"
    assert capturado["params"]["width"] == 800
    assert capturado["params"]["height"] == 800


def test_meta_picture_sin_red_devuelve_vacio(monkeypatch):
    def falla(*a, **k):
        raise requests_real.RequestException("sin red")

    monkeypatch.setattr(imagenes.requests, "get", falla)
    assert imagenes.meta_picture("123", "tok") == ""


def test_ig_picture_parsea_json(monkeypatch):
    monkeypatch.setattr(
        imagenes.requests,
        "get",
        lambda url, **kw: Respuesta(
            json_data={"profile_picture_url": "https://cdn.ig/p.jpg"}
        ),
    )
    assert imagenes.ig_picture("456", "tok") == "https://cdn.ig/p.jpg"


def test_youtube_thumbnail_usa_primer_canal(monkeypatch):
    monkeypatch.setattr(
        "scraper.adapters.youtube.channel_id_from_url", lambda url: "UC123"
    )
    monkeypatch.setattr(
        imagenes.requests,
        "get",
        lambda url, **kw: Respuesta(
            json_data={
                "items": [
                    {
                        "snippet": {
                            "thumbnails": {
                                "high": {"url": "https://yt.ggpht.com/c.jpg"}
                            }
                        }
                    }
                ]
            }
        ),
    )
    links = [LinkFake("yt", "https://youtube.com/@canal")]
    assert imagenes.youtube_thumbnail_de_canal(links, "clave") == "https://yt.ggpht.com/c.jpg"


def test_youtube_thumbnail_ignora_busquedas(monkeypatch):
    links = [LinkFake("yt", "https://youtube.com/results?q=x", es_busqueda=True)]
    assert imagenes.youtube_thumbnail_de_canal(links, "clave") == ""