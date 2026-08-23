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
    """Sin sesión del propietario, desconectar exige el token de administrador."""
    respuesta = client.post("/api/feed/igfb/desconectar?slug=apex_ultra")
    assert respuesta.status_code == 403
    respuesta = client.post(
        "/api/feed/igfb/desconectar?slug=apex_ultra",
        headers={"X-Admin-Token": "incorrecto"},
    )
    assert respuesta.status_code == 403


def test_desconectar_meta_acepta_sesion_del_propietario(client, monkeypatch):
    """La sesión firmada emitida por Meta permite desconectar el perfil."""
    import backend.feed_meta as feed_meta

    monkeypatch.setattr(feed_meta, "APP_SECRET", "secreto-meta-test")
    token = feed_meta._crear_sesion_propietario("apex_ultra")
    respuesta = client.post(
        "/api/feed/igfb/desconectar?slug=apex_ultra",
        cookies={feed_meta.OWNER_COOKIE: token},
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True}


def test_desconectar_meta_acepta_sesion_en_header(client, monkeypatch):
    """La sesión también puede viajar en header entre dominios distintos."""
    import backend.feed_meta as feed_meta

    monkeypatch.setattr(feed_meta, "APP_SECRET", "secreto-meta-test")
    token = feed_meta._crear_sesion_propietario("apex_ultra")
    respuesta = client.post(
        "/api/feed/igfb/desconectar?slug=apex_ultra",
        headers={"X-Meta-Owner": token},
    )
    assert respuesta.status_code == 200


def test_foto_propia_requiere_sesion_del_propietario(client):
    """PUT /{slug}/photo sin sesión firmada se rechaza con 403."""
    respuesta = client.put(
        "/api/feed/igfb/apex_ultra/photo",
        json={"imagen_perfil": "https://example.com/foto.jpg"},
    )
    assert respuesta.status_code == 403
    respuesta = client.put(
        "/api/feed/igfb/apex_ultra/photo",
        json={"imagen_perfil": "https://example.com/foto.jpg"},
        headers={"X-Meta-Owner": "token-falso"},
    )
    assert respuesta.status_code == 403


def test_foto_propia_con_sesion_en_header(client, monkeypatch):
    """El artista verificado elige su foto enviando la sesión en header."""
    import backend.feed_meta as feed_meta

    monkeypatch.setattr(feed_meta, "APP_SECRET", "secreto-meta-test")
    token = feed_meta._crear_sesion_propietario("apex_ultra")
    respuesta = client.put(
        "/api/feed/igfb/apex_ultra/photo",
        json={
            "imagen_perfil": "https://example.com/foto.jpg",
            "imagen_origen": "manual",
        },
        headers={"X-Meta-Owner": token},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is True
    assert cuerpo["imagen_perfil"] == "https://example.com/foto.jpg"
    assert cuerpo["imagen_origen"] == "manual"

    detalle = client.get("/api/artists/apex_ultra").json()
    assert detalle["imagen_perfil"] == "https://example.com/foto.jpg"


def test_foto_propia_de_otro_artista_rechazada(client, monkeypatch):
    """La sesión de un artista no sirve para editar la foto de otro."""
    import backend.feed_meta as feed_meta

    monkeypatch.setattr(feed_meta, "APP_SECRET", "secreto-meta-test")
    token = feed_meta._crear_sesion_propietario("apex_ultra")
    respuesta = client.put(
        "/api/feed/igfb/vaale/photo",
        json={"imagen_perfil": "https://example.com/foto.jpg"},
        headers={"X-Meta-Owner": token},
    )
    assert respuesta.status_code == 403
