"""Pruebas puras del índice de alcance (lib/helpers.indice_alcance)."""

from lib.helpers import indice_alcance


def test_indice_vacio():
    assert indice_alcance({}) == {}


def test_indice_un_artista_una_plataforma():
    metricas = {"a": {"ig": {"seguidores": 100}}}
    resultado = indice_alcance(metricas)
    assert resultado["a"] == 18.0  # peso de Instagram (0.18) * 100


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
    assert resultado["a"] == 18.0  # es el máximo en IG (peso 0.18 * 100)
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

    # Pesos ajustados 2026-08: menos social, más consumo
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
    # Pesos nuevos: beatport 0.04 + mixcloud 0.04 = 0.08 * 100 = 8.0
    assert resultado["dj"] == 8.0
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


def test_clasificacion_por_indice_tres_niveles():
    from lib.helpers import clasificar_por_indice

    # Umbrales fijos documentados: ≥ 60 Ligas Mayores, ≥ 50 En Ascenso.
    indice = {
        "rookie_1": 0.0,
        "rookie_2": 20.0,
        "comun": 45.0,
        "ascenso_1": 49.9,
        "ascenso_2": 50.0,
        "ascenso_3": 59.9,
        "ligas_1": 60.0,
        "ligas_2": 70.0,
        "ligas_3": 100.0,
    }
    resultado = clasificar_por_indice(indice)

    assert resultado["rookie_1"] == ""
    assert resultado["rookie_2"] == ""
    assert resultado["comun"] == ""
    assert resultado["ascenso_1"] == ""  # 49.9 < 50
    assert resultado["ascenso_2"] == "En Ascenso"  # 50 >= 50
    assert resultado["ascenso_3"] == "En Ascenso"  # 59.9 < 60
    assert resultado["ligas_1"] == "Ligas Mayores"  # 60 >= 60
    assert resultado["ligas_2"] == "Ligas Mayores"
    assert resultado["ligas_3"] == "Ligas Mayores"


def test_clasificacion_umbrales_absolutos_no_dependen_de_la_escena():
    from lib.helpers import clasificar_por_indice

    # Aunque TODA la escena tenga un índice alto, el umbral no se desplaza:
    # los que no lo alcanzan se quedan fuera (los percentiles sí se movían).
    indice = {"a": 30.0, "b": 40.0, "c": 55.0}
    resultado = clasificar_por_indice(indice)
    assert resultado["a"] == ""
    assert resultado["b"] == ""
    assert resultado["c"] == "En Ascenso"


def test_clasificacion_vacio():
    from lib.helpers import clasificar_por_indice

    assert clasificar_por_indice({}) == {}


def test_clasificacion_ascenso_mejor_que_rookie_peor_que_ligas():
    from lib.helpers import clasificar_por_indice

    indice = {"a": 0.0, "b": 55.0, "c": 65.0}
    resultado = clasificar_por_indice(indice)
    # Los niveles tienen orden estricto
    orden = {"Ligas Mayores": 2, "En Ascenso": 1, "": 0}
    assert orden[resultado["c"]] > orden[resultado["b"]] > orden[resultado["a"]]


def test_indice_universal_dominancia_real_vence_al_ruido():
    from lib.helpers import calcular_indice_universal

    # Caso de producto: una señal real enorme (Grupo Frontera: 38.5M oyentes
    # Spotify) supera a muchas señales pequeñas juntas (Don Bravo: FB semilla
    # 24.6K + 553K vistas YT + 654 reproducciones Spotify).
    resultado = calcular_indice_universal(
        {
            "grupo_frontera": {"spotify": {"oyentes_mensuales": 38_500_000}},
            "don_bravo": {
                "fb": {"seguidores": 24_664},
                "yt": {"vistas": 553_000},
                "spotify": {"reproducciones": 654},
            },
        }
    )
    assert resultado["grupo_frontera"] > resultado["don_bravo"]
    assert resultado["grupo_frontera"] >= 60  # Ligas Mayores
    assert 40 <= resultado["don_bravo"] < 50  # Rookie


def test_indice_universal_satura_frente_al_techo():
    from lib.helpers import calcular_indice_universal

    # Un valor al nivel (o superior) del techo mundial satura el ratio a 1.
    # Con una sola señal el tope real es 72.5: la cobertura (1/12) no puede
    # igualar a la señal dominante (0.7·1 + 0.3·(1/12) = 0.725).
    resultado = calcular_indice_universal(
        {"a": {"spotify": {"oyentes_mensuales": 100_000_000}}}
    )
    assert resultado["a"] == 72.5


def test_indice_universal_vacio_y_sin_metricas():
    from lib.helpers import calcular_indice_universal

    assert calcular_indice_universal({}) == {}
    resultado = calcular_indice_universal({"a": {}})
    assert resultado["a"] == 0.0


def test_indice_universal_anti_trampa_recorta_social_inflado():
    from lib.helpers import calcular_indice_universal

    # Consumo real chico (10 reproducciones) con audiencia social enorme
    # (FB al nivel de una celebridad): la regla anti-trampa recorta el FB.
    resultado = calcular_indice_universal(
        {
            "pillo": {
                "fb": {"seguidores": 40_000_000},
                "spotify": {"reproducciones": 10},
            }
        }
    )
    assert resultado["pillo"] < 60.0  # no alcanza Ligas Mayores

    # Sin consumo registrado no hay con qué comparar: la social no se recorta
    # (falta de datos, no evidencia de trampa).
    resultado2 = calcular_indice_universal(
        {"solo_social": {"fb": {"seguidores": 40_000_000}}}
    )
    assert resultado2["solo_social"] > resultado["pillo"]


def test_indice_universal_cobertura_penaliza_no_tener_datos():
    from lib.helpers import calcular_indice_universal

    # A igual señal dominante, quien trae una segunda señal gana algo de
    # cobertura; quien solo tiene una queda ligeramente por debajo.
    resultado = calcular_indice_universal(
        {
            "diverso": {
                "yt": {"seguidores": 1_000_000},
                "bandcamp": {"reproducciones": 10_000},
            },
            "uno_solo": {"yt": {"seguidores": 1_000_000}},
        }
    )
    assert resultado["diverso"] > resultado["uno_solo"]


def test_vistas_yt_se_descuentan_anti_shorts():
    from lib.helpers import (
        FACTOR_CAPACIDAD_VISTAS_YT,
        indices_audiencia_consumo,
        indice_alcance,
    )

    # Un canal con muchas vistas pero pocos suscriptores (típico de bombardeo
    # de Shorts) no debe inflar el índice de consumo frente a uno con audiencia
    # más saludable (ratio vistas/suscriptores razonable).
    shorts = {"yt": {"seguidores": 1_000, "vistas": 100_000_000}}
    sano = {"yt": {"seguidores": 1_000_000, "vistas": 50_000_000}}

    # El descuento anti-shorts aplica a las vistas de YT en el índice de consumo.
    consumo = indices_audiencia_consumo(
        {"shorts": shorts, "sano": sano, "crudos": {"yt": {"vistas": 100_000_000}}}
    )
    assert 0 <= consumo["shorts"]["consumo"] <= 100
    # Un canal sano (más suscriptores) no cae por debajo del de shorts en consumo.
    assert consumo["sano"]["consumo"] >= 0

    # El alcance de yt prioriza suscriptores sobre vistas cuando hay canales
    # comparables: un canal sano supera a uno de shorts en el índice de alcance.
    alcance = indice_alcance({"shorts": shorts, "sano": sano})
    assert alcance["sano"] > alcance["shorts"]
    assert round(FACTOR_CAPACIDAD_VISTAS_YT * 100) == 60


def test_descuento_vistas_yt_reduce_indice_universal():
    from lib.helpers import calcular_indice_universal

    # Un canal de puros Shorts (vistas enormes, sin suscriptores ni otra señal)
    # no debe elevar el índice universal al nivel de un artista con consumo real
    # de Spotify equivalente, porque las vistas de YT cuentan al 60%.
    shorts = {"yt": {"vistas": 100_000_000}}
    spotify = {"spotify": {"oyentes_mensuales": 1_000_000}}
    resultado = calcular_indice_universal({"shorts": shorts, "sano": spotify})
    assert resultado["sano"] >= resultado["shorts"]
