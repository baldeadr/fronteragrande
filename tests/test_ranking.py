"""Pruebas puras del índice de alcance (lib/helpers.indice_alcance)."""

from lib.helpers import indice_alcance


def test_indice_vacio():
    assert indice_alcance({}) == {}


def test_indice_un_artista_una_plataforma():
    metricas = {"a": {"ig": {"seguidores": 100}}}
    resultado = indice_alcance(metricas)
    assert resultado["a"] == 30.0  # peso de Instagram (0.30) * 100


def test_indice_sin_plataforma_penaliza():
    metricas = {
        "a": {"ig": {"seguidores": 1000}},
        "b": {},
    }
    resultado = indice_alcance(metricas)
    assert resultado["a"] > resultado["b"]
    assert resultado["b"] == 0.0
    assert resultado["a"] <= 100.0


def test_indice_normalizacion_mayor_domina():
    metricas = {
        "a": {"ig": {"seguidores": 1_000_000}},
        "b": {"ig": {"seguidores": 1}},
    }
    resultado = indice_alcance(metricas)
    assert resultado["a"] == 30.0  # es el máximo en IG
    assert 0.0 < resultado["b"] < resultado["a"]


def test_indice_respeta_rango():
    metricas = {
        "a": {"ig": {"seguidores": 1}, "fb": {"seguidores": 1},
              "spotify": {"reproducciones": 1}, "yt": {"vistas": 1}},
        "b": {"tt": {"vistas": 1}, "bandcamp": {"reproducciones": 1},
              "soundcloud": {"reproducciones": 1}},
    }
    resultado = indice_alcance(metricas)
    for valor in resultado.values():
        assert 0.0 <= valor <= 100.0


def test_indice_ignora_nulos_y_no_numericos():
    metricas = {"a": {"ig": {"seguidores": None}, "fb": {"seguidores": "x"}}}
    assert indice_alcance(metricas)["a"] == 0.0