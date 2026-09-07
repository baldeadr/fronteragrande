"""Pruebas de la captura síncrona de métricas en el onboarding del alta.

Cuando un artista registra su proyecto, el onboarding captura al momento:
- suscriptores/vistas de YouTube (si hay `YOUTUBE_API_KEY`),
- seguidores de SoundCloud (api-v2),
- seguidores de Mixcloud (API REST pública).

Así el perfil no queda en ceros hasta el próximo GitHub Action (cada 6 h).
"""

import pytest

from scraper.adapters import mixcloud, soundcloud


class _Respuesta:
    def __init__(self, ok=True, json_data=None, status_code=200, texto=""):
        self.ok = ok
        self._json = json_data or {}
        self.status_code = status_code
        self.text = texto

    def json(self):
        return self._json


# --- Adaptador SoundCloud ---------------------------------------------------


def test_soundcloud_seguidores(monkeypatch):
    """Lee el `followers_count` del perfil vía api-v2 (una sola llamada)."""
    def _get(url, *a, **kw):
        return _Respuesta(json_data={"id": 123, "followers_count": 4567})

    monkeypatch.setattr(soundcloud, "_user_id", lambda url: 123)
    monkeypatch.setattr(soundcloud, "_client_id", lambda url: "cid")
    monkeypatch.setattr(soundcloud.requests, "get", _get)

    assert soundcloud.seguidores("https://soundcloud.com/artista") == 4567


def test_soundcloud_seguidores_sin_client_id_lanza_error(monkeypatch):
    """Sin `client_id` no se puede leer la fuente: lanza `SoundCloudError`."""
    monkeypatch.setattr(soundcloud, "_user_id", lambda url: 123)
    monkeypatch.setattr(soundcloud, "_client_id", lambda url: "")

    with pytest.raises(soundcloud.SoundCloudError):
        soundcloud.seguidores("https://soundcloud.com/artista")


def test_soundcloud_seguidores_error_red(monkeypatch):
    """Fallo de red propaga `SoundCloudError` para no inventar un cero."""
    def _get(url, *a, **kw):
        return _Respuesta(ok=False, status_code=500)

    monkeypatch.setattr(soundcloud, "_user_id", lambda url: 123)
    monkeypatch.setattr(soundcloud, "_client_id", lambda url: "cid")
    monkeypatch.setattr(soundcloud.requests, "get", _get)

    with pytest.raises(soundcloud.SoundCloudError):
        soundcloud.seguidores("https://soundcloud.com/artista")


# --- Adaptador Mixcloud -----------------------------------------------------


def test_mixcloud_seguidores(monkeypatch):
    """Lee el `follower_count` de la API REST pública de Mixcloud."""
    def _get(url, *a, **kw):
        return _Respuesta(json_data={"name": "DJ X", "follower_count": 890})

    monkeypatch.setattr(mixcloud.requests, "get", _get)

    assert mixcloud.seguidores("https://www.mixcloud.com/djx/") == 890


def test_mixcloud_seguidores_sin_usuario(monkeypatch):
    """Sin usuario en la URL lanza `ScraperError` (sin llamar a la red)."""
    from scraper.errors import ScraperError

    with pytest.raises(ScraperError):
        mixcloud.seguidores("https://www.mixcloud.com")


def test_mixcloud_seguidores_error_red(monkeypatch):
    """Fallo de red propaga `ScraperError` para no inventar un cero."""
    from scraper.errors import ScraperError

    monkeypatch.setattr(
        mixcloud.requests, "get", lambda *a, **kw: _Respuesta(ok=False, status_code=404)
    )

    with pytest.raises(ScraperError):
        mixcloud.seguidores("https://www.mixcloud.com/djx/")


# --- Integración en el onboarding (POST /api/artists) -----------------------


def test_onboarding_captura_metrics_sincronas(client, monkeypatch):
    """Al dar de alta un artista, el onboarding llena YT/SC/Mixcloud al momento.

    Dejar deja el perfil con seguidores/vistas sin esperar al GitHub Action.
    """
    from lib.repository import ArtistRepository

    # Descarta red real en la foto y los videos del feed.
    monkeypatch.setattr(
        "scraper.adapters.imagenes.imagen_de_artista", lambda links: (None, None)
    )
    monkeypatch.setattr(
        "scraper.adapters.youtube.latest_videos", lambda *a, **kw: []
    )

    # YouTube: resuelve dos canales y suma.
    def _channel_id(url):
        return "UC-A" if "canal-a" in url else "UC-B"

    def _channel_stats(channel_id, api_key):
        if channel_id == "UC-A":
            return {"suscriptores": 5000, "vistas": 100_000, "videos": 30}
        return {"suscriptores": 2000, "vistas": 70_000, "videos": 10}

    # SoundCloud y Mixcloud: un solo perfil de cada uno.
    def _sc_seguidores(url):
        return 3333

    def _mx_seguidores(url):
        return 777

    monkeypatch.setenv("YOUTUBE_API_KEY", "clave_prueba")
    monkeypatch.setattr(
        "scraper.adapters.youtube.channel_id_from_url", _channel_id
    )
    monkeypatch.setattr(
        "scraper.adapters.youtube.channel_statistics", _channel_stats
    )
    monkeypatch.setattr("scraper.adapters.soundcloud.seguidores", _sc_seguidores)
    monkeypatch.setattr("scraper.adapters.mixcloud.seguidores", _mx_seguidores)

    respuesta = client.post(
        "/api/artists",
        json={
            "nombre": "Banda Meters",
            "categoria": "Banda",
            "ciudad": "Reynosa",
            "redes": [
                {"plataforma": "yt", "url": "https://www.youtube.com/@canal-a"},
                {"plataforma": "yt", "url": "https://www.youtube.com/@canal-b"},
                {"plataforma": "soundcloud", "url": "https://soundcloud.com/banda-meters"},
                {"plataforma": "mixcloud", "url": "https://www.mixcloud.com/banda-meters/"},
            ],
        },
    )
    assert respuesta.status_code == 201
    onboarding = respuesta.json()["onboarding"]
    assert onboarding["yt_suscriptores"] == 7000
    assert onboarding["soundcloud_seguidores"] == 3333
    assert onboarding["mixcloud_seguidores"] == 777

    detalle = client.get("/api/artists/banda_meters").json()
    assert detalle["followers"]["yt"] == 7000
    assert detalle["stats"]["yt"]["seguidores"] == 7000
    assert detalle["stats"]["yt"]["vistas"] == 170_000
    assert detalle["stats"]["soundcloud"]["seguidores"] == 3333
    assert detalle["stats"]["mixcloud"]["seguidores"] == 777

    # Limpieza de prueba (el rate-limit registra la IP de todos modos).
    from db.database import SessionLocal
    from db.models import AltaRegistro, Artist, ArtistLink
    from sqlalchemy import delete, select

    sesion = SessionLocal()
    try:
        artista = ArtistRepository(sesion).por_slug("banda_meters")
        if artista:
            sesion.execute(
                delete(ArtistLink).where(ArtistLink.artist_id == artista.id)
            )
        sesion.execute(delete(Artist).where(Artist.slug == "banda_meters"))
        sesion.execute(delete(AltaRegistro))
        sesion.commit()
    finally:
        sesion.close()


def test_onboarding_sin_api_key_yt_no_rompe(client, monkeypatch):
    """Sin `YOUTUBE_API_KEY` el onboarding sigue y no hace red a la Data API."""
    monkeypatch.setattr(
        "scraper.adapters.imagenes.imagen_de_artista", lambda links: (None, None)
    )
    monkeypatch.setattr(
        "scraper.adapters.youtube.latest_videos", lambda *a, **kw: []
    )
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)

    llamadas_stats = []

    def _channel_stats(channel_id, api_key):
        llamadas_stats.append((channel_id, api_key))
        return {"suscriptores": 1, "vistas": 1, "videos": 0}

    monkeypatch.setattr(
        "scraper.adapters.youtube.channel_statistics", _channel_stats
    )

    respuesta = client.post(
        "/api/artists",
        json={
            "nombre": "Banda Sin Key",
            "categoria": "Banda",
            "redes": [
                {"plataforma": "yt", "url": "https://www.youtube.com/@sinkey"}
            ],
        },
    )
    assert respuesta.status_code == 201
    assert llamadas_stats == []
    assert respuesta.json()["onboarding"]["yt_suscriptores"] is None

    from db.database import SessionLocal
    from db.models import AltaRegistro, Artist, ArtistLink
    from sqlalchemy import delete, select

    sesion = SessionLocal()
    try:
        sesion.execute(
            delete(ArtistLink).where(ArtistLink.artist_id.in_(
                select(Artist.id).where(Artist.slug == "banda_sin_key")
            ))
        )
        sesion.execute(delete(Artist).where(Artist.slug == "banda_sin_key"))
        sesion.execute(delete(AltaRegistro))
        sesion.commit()
    finally:
        sesion.close()