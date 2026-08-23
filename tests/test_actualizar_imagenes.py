"""Pruebas de la fusión de candidatas de foto entre corridas (sin red)."""

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
