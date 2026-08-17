"""Pruebas del adaptador de estadísticas públicas de YouTube."""

import pytest

from scraper.adapters import youtube
from scraper.errors import ScraperError


class Respuesta:
    ok = True
    status_code = 200

    def json(self):
        return {
            "items": [
                {
                    "statistics": {
                        "subscriberCount": "56000",
                        "viewCount": "1234567",
                        "videoCount": "24",
                        "hiddenSubscriberCount": False,
                    }
                }
            ]
        }


def test_channel_statistics_parsea_metricas(monkeypatch):
    monkeypatch.setattr(youtube.requests, "get", lambda *args, **kwargs: Respuesta())

    assert youtube.channel_statistics("UC123", "clave") == {
        "suscriptores": 56000,
        "vistas": 1234567,
        "videos": 24,
    }


def test_channel_statistics_no_inventa_suscriptores_ocultos(monkeypatch):
    respuesta = Respuesta()
    respuesta.json = lambda: {
        "items": [{"statistics": {"hiddenSubscriberCount": True, "viewCount": "8"}}]
    }
    monkeypatch.setattr(youtube.requests, "get", lambda *args, **kwargs: respuesta)

    datos = youtube.channel_statistics("UC123", "clave")

    assert datos["suscriptores"] is None
    assert datos["vistas"] == 8


def test_channel_statistics_exige_respuesta(monkeypatch):
    respuesta = Respuesta()
    respuesta.ok = False
    respuesta.status_code = 403
    monkeypatch.setattr(youtube.requests, "get", lambda *args, **kwargs: respuesta)

    with pytest.raises(ScraperError):
        youtube.channel_statistics("UC123", "clave")
