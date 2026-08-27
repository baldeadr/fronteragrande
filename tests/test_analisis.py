"""Pruebas del análisis dinámico de perfiles."""

from datetime import date

from lib.helpers import (
    dominancia_plataforma,
    patron_dominancia,
    ratio_engagement_spotify,
    ratio_social_musica,
    ratio_viralidad_yt,
)
from lib.servicios import analisis_artista, analisis_consumo


def test_analisis_detecta_oportunidad_de_puente_musical():
    resultado = analisis_artista(
        {
            "tt": {"seguidores": 100_000},
            "spotify": {"oyentes_mensuales": 5},
        },
        date(2026, 8, 16),
    )

    assert resultado["tipo"] == "puente_musical"
    assert "redes sociales" in resultado["texto"]
    assert resultado["actualizado"] == date(2026, 8, 16)


def test_analisis_no_confunde_reproducciones_con_audiencia():
    resultado = analisis_artista(
        {
            "tt": {"seguidores": 100_000},
            "spotify": {"reproducciones": 5},
        }
    )

    assert resultado["tipo"] == "presencia_social"


def test_analisis_reporta_datos_insuficientes():
    resultado = analisis_artista({"spotify": {"oyentes_mensuales": 20}})

    assert resultado["tipo"] == "datos_insuficientes"
    assert resultado["confianza"] == "baja"


def test_ratio_viralidad_yt():
    assert ratio_viralidad_yt({"yt": {"vistas": 1000, "seguidores": 100}}) == 10.0
    assert ratio_viralidad_yt({"yt": {"vistas": 500, "seguidores": 100}}) == 5.0
    assert ratio_viralidad_yt({"yt": {"seguidores": 100}}) is None
    assert ratio_viralidad_yt({}) is None


def test_ratio_engagement_spotify():
    assert ratio_engagement_spotify(
        {"spotify": {"oyentes_mensuales": 200, "seguidores": 100}}
    ) == 2.0
    assert ratio_engagement_spotify({"spotify": {"oyentes_mensuales": 50}}) is None
    assert ratio_engagement_spotify({}) is None


def test_ratio_social_musica():
    metricas = {
        "ig": {"seguidores": 1000},
        "spotify": {"oyentes_mensuales": 100},
    }
    assert ratio_social_musica(metricas) == 10.0
    assert ratio_social_musica({}) is None
    assert ratio_social_musica({"ig": {"seguidores": 100}}) is None


def test_dominancia_plataforma():
    metricas = {
        "ig": {"seguidores": 100},
        "yt": {"vistas": 300},
        "spotify": {"reproducciones": 100},
    }
    dom = dominancia_plataforma(metricas)
    assert "yt" in dom
    assert dom["yt"] == 60.0
    assert dom["ig"] == 20.0
    assert dom["spotify"] == 20.0


def test_dominancia_plataforma_sin_datos():
    assert dominancia_plataforma({}) == {}


def test_patron_dominancia_youtube():
    metricas = {"yt": {"vistas": 1000, "seguidores": 100}}
    assert patron_dominancia(metricas) == "youtube_dominante"


def test_patron_dominancia_spotify():
    metricas = {"spotify": {"oyentes_mensuales": 1000, "seguidores": 100}}
    assert patron_dominancia(metricas) == "spotify_dominante"


def test_patron_dominancia_social():
    metricas = {"ig": {"seguidores": 1000}, "fb": {"seguidores": 500}}
    assert patron_dominancia(metricas) == "social_dominante"


def test_patron_distribuido():
    metricas = {
        "ig": {"seguidores": 300},
        "yt": {"vistas": 400, "seguidores": 50},
        "spotify": {"oyentes_mensuales": 300, "seguidores": 50},
    }
    assert patron_dominancia(metricas) == "distribuido"


def test_patron_sin_datos():
    assert patron_dominancia({}) == "sin_datos"


def test_analisis_consumo_youtube_dominante():
    metricas = {"yt": {"vistas": 5000, "seguidores": 500}}
    resultado = analisis_consumo(metricas)
    assert resultado["patron"] == "youtube_dominante"
    assert resultado["ratios"]["viralidad_yt"] == 10.0
    assert "YouTube" in resultado["texto"]


def test_analisis_consumo_sin_datos():
    resultado = analisis_consumo({})
    assert resultado["patron"] == "sin_datos"
    assert resultado["ratios"]["viralidad_yt"] is None
    assert resultado["dominancia"] == {}
