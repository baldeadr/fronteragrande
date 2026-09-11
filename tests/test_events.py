"""Pruebas de eventos, stats y géneros."""

import csv


def _filas_eventos():
    with open("data/eventos.csv", encoding="utf-8") as fh:
        return [f for f in csv.DictReader(fh) if f.get("nombre", "").strip()]


def test_events_shape(client):
    respuesta = client.get("/api/events")
    assert respuesta.status_code == 200
    eventos = respuesta.json()
    assert len(eventos) >= len(_filas_eventos()) - 1
    for e in eventos:
        assert e["id"]
        assert e["nombre"]
        assert set(e) >= {
            "id", "nombre", "fecha", "lugar", "ciudad", "artistas",
            "que_demuestra", "fuente",
        }


def test_events_orden_desc(client):
    import pandas as pd

    eventos = client.get("/api/events").json()
    if len(eventos) >= 2:
        fechas = [e["fecha"] for e in eventos]
        if all(fechas):
            fechas = pd.to_datetime(fechas)
            assert list(fechas) == sorted(fechas, reverse=True)


def test_stats_shape(client):
    respuesta = client.get("/api/stats")
    assert respuesta.status_code == 200
    stats = respuesta.json()
    assert stats["total"] >= 1
    for clave in ("generos", "estados", "ciudades", "segmentos"):
        assert isinstance(stats[clave], dict)


def test_stats_panorama(client):
    """El panel trae las series e indicadores nuevos con forma correcta."""
    stats = client.get("/api/stats").json()
    assert len(stats["feed_serie"]) == 12
    assert len(stats["altas_por_mes"]) == 12
    for punto in stats["feed_serie"]:
        assert set(punto) == {"mes", "año", "conteo"}
    assert isinstance(stats["seguidores"], dict)
    assert isinstance(stats["reproducciones"], dict)
    assert isinstance(stats["cobertura"], dict)
    assert stats["posts_90dias"] >= 0
    assert isinstance(stats["por_ciudad"], list)
    for ciudad in stats["por_ciudad"]:
        assert set(ciudad) >= {"nombre", "total", "activo", "en_duda", "inactivo"}
    if stats["ultima_alta"] is not None:
        assert set(stats["ultima_alta"]) >= {"nombre", "slug", "fecha"}


def test_genres(client):
    generos = client.get("/api/genres").json()
    assert isinstance(generos, list)
    assert all(isinstance(g, str) for g in generos)