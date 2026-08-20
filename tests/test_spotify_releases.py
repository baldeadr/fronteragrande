"""Pruebas del adaptador de lanzamientos de Spotify y su filtro de ventana."""

from datetime import date

from scraper.adapters import spotify
from scripts.sync_lanzamientos import _dentro_de_ventana


def test_fecha_lanzamiento_formatos():
    assert spotify._fecha_lanzamiento("2025-09-03") == date(2025, 9, 3)
    assert spotify._fecha_lanzamiento("2025-09") == date(2025, 9, 1)
    assert spotify._fecha_lanzamiento("2025") == date(2025, 1, 1)
    assert spotify._fecha_lanzamiento(None) is None
    assert spotify._fecha_lanzamiento("") is None
    assert spotify._fecha_lanzamiento("nada") is None
    assert spotify._fecha_lanzamiento("2025-13-40") is None


class Respuesta:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "items": [
                {
                    "name": "Sencillo nuevo",
                    "album_type": "single",
                    "release_date": "2026-08-01",
                    "external_urls": {"spotify": "https://open.spotify.com/album/abc"},
                    "images": [{"url": "https://i.scdn.co/image/x"}],
                },
                {
                    "name": "Álbum sin portada",
                    "album_type": "album",
                    "release_date": "2026",
                    "external_urls": {"spotify": "https://open.spotify.com/album/def"},
                    "images": [],
                },
            ]
        }


def test_get_artist_releases_normaliza(monkeypatch):
    monkeypatch.setattr(spotify, "_token", lambda: "tok")
    monkeypatch.setattr(spotify.requests, "get", lambda *a, **k: Respuesta())

    items = spotify.get_artist_releases("abc123")

    assert len(items) == 2
    assert items[0] == {
        "titulo": "Sencillo nuevo",
        "url": "https://open.spotify.com/album/abc",
        "fecha": date(2026, 8, 1),
        "imagen": "https://i.scdn.co/image/x",
        "tipo_lanzamiento": "single",
    }
    assert items[1]["fecha"] == date(2026, 1, 1)
    assert items[1]["imagen"] == ""


def test_dentro_de_ventana():
    hoy = date(2026, 8, 19)
    assert _dentro_de_ventana(None, hoy) is True
    assert _dentro_de_ventana(date(2026, 8, 1), hoy) is True
    assert _dentro_de_ventana(date(2025, 1, 1), hoy) is True
    assert _dentro_de_ventana(date(2020, 1, 1), hoy) is False
