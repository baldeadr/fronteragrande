"""Pruebas de la fusión de candidatas de foto y del extractor de Spotify (sin red)."""

from scraper.adapters import imagenes
from scraper.adapters.imagenes import fusionar_candidatas


def test_conserva_plataforma_estable_que_no_respondio():
    fusion = fusionar_candidatas(
        {"spotify": "https://spotifycdn.com/a.jpg", "yt": "https://yt3/b.jpg"},
        {"yt": "https://yt3/nuevo.jpg"},
        {"spotify", "yt"},
    )
    assert fusion["spotify"] == "https://spotifycdn.com/a.jpg"
    assert fusion["yt"] == "https://yt3/nuevo.jpg"


def test_no_conserva_urls_que_caducan():
    fusion = fusionar_candidatas(
        {"fb": "https://scontent/fb.jpg", "ig": "https://cdn/ig.jpg"},
        {},
        {"fb", "ig"},
    )
    assert fusion == {}


def test_descarta_plataformas_con_enlace_quitado():
    fusion = fusionar_candidatas(
        {"bandcamp": "https://bcbits/a.jpg"},
        {},
        {"yt"},
    )
    assert fusion == {}


def test_previas_vacias_devuelve_nuevas():
    nuevas = {"soundcloud": "https://sndcloud/a.jpg"}
    assert fusionar_candidatas(None, nuevas, {"soundcloud"}) == nuevas
    assert fusionar_candidatas({}, nuevas, {"soundcloud"}) == nuevas


def test_ignora_previas_con_url_vacia():
    fusion = fusionar_candidatas({"spotify": ""}, {}, {"spotify"})
    assert fusion == {}


class _Respuesta:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json = json_data

    def json(self):
        return self._json


def test_spotify_usa_oembed_cuando_embed_no_responde(monkeypatch):
    monkeypatch.setattr(imagenes, "_spotify_api", lambda url: "")  # desactiva la Web API

    def get(url, **kw):
        if "/embed/" in url:
            return _Respuesta(status_code=403)
        return _Respuesta(
            json_data={
                "thumbnail_url": "https://image-cdn-ak.spotifycdn.com/image/ab67616100005174abc"
            }
        )

    monkeypatch.setattr(imagenes.requests, "get", get)
    url = imagenes._spotify("https://open.spotify.com/artist/5WorcyG21D1NGZ3iLoQtJi")
    assert url == "https://image-cdn-ak.spotifycdn.com/image/ab67616100005174abc"


def test_spotify_oembed_acepta_miniatura_i_scdn_co(monkeypatch):
    monkeypatch.setattr(imagenes, "_spotify_api", lambda url: "")

    def get(url, **kw):
        if "/embed/" in url:
            return _Respuesta(status_code=403)
        return _Respuesta(json_data={"thumbnail_url": "https://i.scdn.co/image/ab67616100005174abc"})

    monkeypatch.setattr(imagenes.requests, "get", get)
    url = imagenes._spotify("https://open.spotify.com/artist/5WorcyG21D1NGZ3iLoQtJi")
    assert url == "https://i.scdn.co/image/ab67616100005174abc"


def test_spotify_prefiere_foto_de_perfil_del_embed(monkeypatch):
    monkeypatch.setattr(imagenes, "_spotify_api", lambda url: "")  # desactiva la Web API

    html = (
        '<html><meta content="https://image-cdn-ak.spotifycdn.com/image/'
        'ab6761610000f178db0ae59a86330ee7bcc241cd" /></html>'
    )
    llamadas = []

    def get(url, **kw):
        llamadas.append(url)
        return _Respuesta(text=html)

    monkeypatch.setattr(imagenes.requests, "get", get)
    url = imagenes._spotify("https://open.spotify.com/artist/5WorcyG21D1NGZ3iLoQtJi")
    assert url == "https://image-cdn-ak.spotifycdn.com/image/ab6761610000f178db0ae59a86330ee7bcc241cd"
    assert len(llamadas) == 1  # no consulta oEmbed si el embed respondió


def test_spotify_prefiere_web_api_sobre_embed(monkeypatch):
    """Con la Web API disponible no toca embed ni oEmbed (resolución mayor)."""
    monkeypatch.setattr(
        imagenes, "_spotify_api", lambda url: "https://i.scdn.co/image/alta"
    )
    llamadas = []

    def get(url, **kw):
        llamadas.append(url)
        return _Respuesta(text="<html>embed</html>")

    monkeypatch.setattr(imagenes.requests, "get", get)
    url = imagenes._spotify("https://open.spotify.com/artist/5WorcyG21D1NGZ3iLoQtJi")
    assert url == "https://i.scdn.co/image/alta"
    assert llamadas == []


def test_spotify_rechaza_miniatura_ajena(monkeypatch):
    monkeypatch.setattr(imagenes, "_spotify_api", lambda url: "")  # desactiva la Web API

    def get(url, **kw):
        if "/embed/" in url:
            return _Respuesta(status_code=403)
        return _Respuesta(json_data={"thumbnail_url": "https://otro-cdn/img.jpg"})

    monkeypatch.setattr(imagenes.requests, "get", get)
    assert imagenes._spotify("https://open.spotify.com/artist/5WorcyG21D1NGZ3iLoQtJi") == ""


def test_spotify_api_elige_imagen_mayor(monkeypatch):
    """`_spotify_api` devuelve la imagen más grande de `images` (mayor a menor)."""
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "cid")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "csecret")

    import sys
    import types

    llamadas = {}

    class FakeSpotify:
        def __init__(self, auth_manager=None):
            llamadas["auth"] = auth_manager

        def artist(self, artista_id):
            llamadas["id"] = artista_id
            return {
                "images": [
                    {"width": 64, "height": 96, "url": "https://i.scdn.co/image/peq"},
                    {"width": 326, "height": 491, "url": "https://i.scdn.co/image/gran"},
                    {"width": 200, "height": 301, "url": "https://i.scdn.co/image/med"},
                ]
            }

    class FakeAuth:
        def __init__(self, **kw):
            llamadas["creds"] = kw

    fake_spotipy = types.SimpleNamespace(
        Spotify=FakeSpotify,
        oauth2=types.SimpleNamespace(SpotifyClientCredentials=FakeAuth),
    )
    monkeypatch.setitem(sys.modules, "spotipy", fake_spotipy)
    monkeypatch.setitem(sys.modules, "spotipy.oauth2", fake_spotipy.oauth2)
    url = imagenes._spotify_api("https://open.spotify.com/artist/5WorcyG21D1NGZ3iLoQtJi")
    assert url == "https://i.scdn.co/image/gran"
    assert llamadas["id"] == "5WorcyG21D1NGZ3iLoQtJi"
    assert llamadas["creds"]["client_id"] == "cid"


def test_spotify_api_sin_credenciales_no_consulta():
    import os

    guardar = {}
    for var in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"):
        guardar[var] = os.environ.get(var)
        os.environ[var] = ""
    try:
        assert imagenes._spotify_api("https://open.spotify.com/artist/5WorcyG21D1NGZ3iLoQtJi") == ""
    finally:
        for var, valor in guardar.items():
            if valor is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = valor
