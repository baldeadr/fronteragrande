"""Pruebas del feed unificado."""


def test_feed_shape(client):
    respuesta = client.get("/api/feed")
    assert respuesta.status_code == 200
    items = respuesta.json()
    assert isinstance(items, list)
    if not items:
        return
    primero = items[0]
    for clave in ("fecha", "tipo", "fuente", "titulo", "url", "detalle",
                  "artista", "artista_slug", "preview"):
        assert clave in primero
    assert primero["preview"]["tipo"] in (
        "youtube", "tiktok", "instagram", "facebook", "imagen", "texto"
    )


def test_feed_fechas_desc(client):
    import pandas as pd

    items = client.get("/api/feed").json()
    if len(items) < 2:
        return
    fechas = pd.to_datetime([i["fecha"] for i in items])
    assert list(fechas) == sorted(fechas, reverse=True)


def test_ingesta_manual_eliminada(client):
    """El POST /feed (ingesta manual) ya no existe: 404."""
    respuesta = client.post(
        "/api/artists/apex_ultra/feed",
        json={"url": "https://www.youtube.com/watch?v=abcdefgh123"},
    )
    assert respuesta.status_code == 404


def test_desconectar_meta_requiere_admin(client):
    """Desconectar un perfil de Meta exige el token de administrador."""
    respuesta = client.post("/api/feed/igfb/desconectar?slug=apex_ultra")
    assert respuesta.status_code == 403
    respuesta = client.post(
        "/api/feed/igfb/desconectar?slug=apex_ultra",
        headers={"X-Admin-Token": "incorrecto"},
    )
    assert respuesta.status_code == 403