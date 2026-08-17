"""Pruebas del análisis dinámico de perfiles."""

from datetime import date

from lib.servicios import analisis_artista


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
