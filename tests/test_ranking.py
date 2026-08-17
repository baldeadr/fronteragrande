"""Pruebas puras del índice de alcance (lib/helpers.indice_alcance)."""

from lib.helpers import indice_alcance


def test_indice_vacio():
    assert indice_alcance({}) == {}


def test_indice_un_artista_una_plataforma():
    metricas = {"a": {"ig": {"seguidores": 100}}}
    resultado = indice_alcance(metricas)
    assert resultado["a"] == 29.0  # peso de Instagram (0.29) * 100


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
    assert resultado["a"] == 29.0  # es el máximo en IG
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


def test_pesos_suman_uno():
    from lib.helpers import PESOS_ALCANCE

    assert round(sum(PESOS_ALCANCE.values()), 3) == 1.0


def test_beatport_y_mixcloud_aportan_alcance():
    from lib.helpers import PESOS_ALCANCE

    assert "beatport" in PESOS_ALCANCE
    assert "mixcloud" in PESOS_ALCANCE
    metricas = {
        "dj": {"beatport": {"seguidores": 1000}, "mixcloud": {"seguidores": 1000}},
        "sin_dj": {},
    }
    resultado = indice_alcance(metricas)
    assert resultado["dj"] == 5.0  # (0.03 + 0.02) * 100
    assert resultado["sin_dj"] == 0.0


def test_indices_separan_audiencia_y_consumo_youtube():
    from lib.helpers import indices_audiencia_consumo

    resultado = indices_audiencia_consumo(
        {
            "a": {"yt": {"seguidores": 100, "vistas": 10}},
            "b": {"yt": {"seguidores": 10, "vistas": 1000}},
        }
    )

    assert resultado["a"]["audiencia"] > resultado["b"]["audiencia"]
    assert resultado["b"]["consumo"] > resultado["a"]["consumo"]
    assert 0 <= resultado["a"]["indice"] <= 100


def test_indices_spotify_prefiere_oyentes_sobre_reproducciones():
    from lib.helpers import indices_audiencia_consumo

    resultado = indices_audiencia_consumo(
        {
            "a": {"spotify": {"oyentes_mensuales": 100}},
            "b": {"spotify": {"reproducciones": 10}},
        }
    )

    assert resultado["a"]["consumo"] > resultado["b"]["consumo"]
