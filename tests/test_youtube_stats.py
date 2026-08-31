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


RSS_MUESTRA = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
  <entry>
    <title>Video Uno</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc1"/>
    <published>2026-08-14T00:00:00+00:00</published>
    <media:group>
      <media:description>Una descripción breve</media:description>
      <media:thumbnail url="https://i.ytimg.com/abc1.jpg"/>
    </media:group>
  </entry>
  <entry>
    <title>Video Dos</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc2"/>
    <published>2026-07-11T00:00:00+00:00</published>
    <media:group>
      <media:description>Otra descripción</media:description>
      <media:thumbnail url="https://i.ytimg.com/abc2.jpg"/>
    </media:group>
  </entry>
</feed>
"""


class RespuestaRSS:
    ok = True
    status_code = 200
    url = "https://www.youtube.com/feeds/videos.xml?channel_id=UC123"
    text = RSS_MUESTRA


def test_latest_videos_usa_feed_rss_publico(monkeypatch):
    """El feed de YouTube se lee del RSS público (sin API key ni cuota)."""
    cid = ["UC123"]
    monkeypatch.setattr(
        youtube, "channel_id_from_url", lambda url: cid[0]
    )
    monkeypatch.setattr(
        youtube.requests, "get", lambda *a, **kw: RespuestaRSS()
    )

    videos = youtube.latest_videos("https://www.youtube.com/@canal", max_videos=5, api_key="ignorada")

    assert len(videos) == 2
    primero = videos[0]
    assert primero["titulo"] == "Video Uno"
    assert primero["url"] == "https://www.youtube.com/watch?v=abc1"
    assert primero["imagen"] == "https://i.ytimg.com/abc1.jpg"
    assert (primero["fecha"].strftime("%Y-%m-%d")) == "2026-08-14"
    # lambda recibió el channel_id y pidió el feed RSS (sin search.list/Data API)
    assert cid[0] == "UC123"


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
