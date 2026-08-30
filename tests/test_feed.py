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
                  "artista", "artista_slug", "nivel", "preview"):
        assert clave in primero
    assert primero["preview"]["tipo"] in (
        "youtube", "tiktok", "instagram", "facebook", "imagen", "texto"
    )


def test_feed_expone_nivel(client):
    """El feed trae el nivel calculado del artista en cada ítem."""
    items = client.get("/api/feed").json()
    if not items:
        return
    artistas = client.get("/api/artists").json()
    nivel_por_slug = {
        a["slug"]: (a.get("nivel") or "")
        for a in artistas
        if a.get("slug")
    }
    for item in items:
        assert "nivel" in item
        slug = item.get("artista_slug") or ""
        assert (item.get("nivel") or "") == nivel_por_slug.get(slug, "")


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


def test_editar_perfil_propio_requiere_sesion(client):
    """PUT /{slug}/perfil sin la sesión del propietario se rechaza (403)."""
    respuesta = client.put(
        "/api/feed/igfb/apex_ultra/perfil",
        json={"bio": "nueva bio"},
    )
    assert respuesta.status_code == 403
    respuesta = client.put(
        "/api/feed/igfb/apex_ultra/perfil",
        json={"bio": "nueva bio"},
        headers={"X-Meta-Owner": "token-falso"},
    )
    assert respuesta.status_code == 403


def test_editar_perfil_propio_aplica_campos(client, monkeypatch):
    """El propietario verificado edita su bio, ciudad, géneros y logros."""
    import backend.feed_meta as feed_meta

    monkeypatch.setattr(feed_meta, "APP_SECRET", "secreto-meta-test")
    token = feed_meta._crear_sesion_propietario("apex_ultra")
    respuesta = client.put(
        "/api/feed/igfb/apex_ultra/perfil",
        json={
            "ciudad": "Matamoros",
            "generos": "Electrónica, Industrial",
            "bio": "Bio escrita por el propio artista",
            "logros": "Un logro propio",
        },
        headers={"X-Meta-Owner": token},
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True, "slug": "apex_ultra"}

    detalle = client.get("/api/artists/apex_ultra").json()
    assert detalle["ciudad"] == "Matamoros"
    assert detalle["generos"] == ["Electrónica", "Industrial"]
    assert detalle["bio"] == "Bio escrita por el propio artista"
    assert detalle["logros"] == "Un logro propio"


def test_editar_perfil_propio_no_cambia_nombre(client, monkeypatch):
    """El propietario no puede renombrarse (la identidad la decide el admin)."""
    import backend.feed_meta as feed_meta

    monkeypatch.setattr(feed_meta, "APP_SECRET", "secreto-meta-test")
    token = feed_meta._crear_sesion_propietario("apex_ultra")
    respuesta = client.put(
        "/api/feed/igfb/apex_ultra/perfil",
        json={"nombre": "Otro Nombre"},
        headers={"X-Meta-Owner": token},
    )
    assert respuesta.status_code == 403
    detalle = client.get("/api/artists/apex_ultra").json()
    assert detalle["nombre"] == "Apex Ultra"


def test_editar_perfil_propio_de_otro_artista_rechazada(client, monkeypatch):
    """La sesión de un artista no edita el perfil de otro."""
    import backend.feed_meta as feed_meta

    monkeypatch.setattr(feed_meta, "APP_SECRET", "secreto-meta-test")
    token = feed_meta._crear_sesion_propietario("apex_ultra")
    respuesta = client.put(
        "/api/feed/igfb/vaale/perfil",
        json={"bio": "hack"},
        headers={"X-Meta-Owner": token},
    )
    assert respuesta.status_code == 403
    detalle = client.get("/api/artists/vaale").json()
    assert detalle["bio"] != "hack"


def test_editar_perfil_propio_conserva_fb_verificado(client, monkeypatch):
    """El propietario debe conservar su página de Facebook al cambiar URLs."""
    import backend.feed_meta as feed_meta

    monkeypatch.setattr(feed_meta, "APP_SECRET", "secreto-meta-test")
    token = feed_meta._crear_sesion_propietario("apex_ultra")

    # Conserva su FB verificado y añade YouTube.
    ok = client.put(
        "/api/feed/igfb/apex_ultra/perfil",
        json={
            "redes": [
                {"plataforma": "fb", "url": "https://www.facebook.com/apexultramusic"},
                {"plataforma": "yt", "url": "https://www.youtube.com/@apexultramusic"},
            ]
        },
        headers={"X-Meta-Owner": token},
    )
    assert ok.status_code == 200

    # Quitar el FB verificado se rechaza (400).
    sin_fb = client.put(
        "/api/feed/igfb/apex_ultra/perfil",
        json={
            "redes": [
                {"plataforma": "yt", "url": "https://www.youtube.com/@otrocanal"}
            ]
        },
        headers={"X-Meta-Owner": token},
    )
    assert sin_fb.status_code == 400

    # Cambiarlo por el FB de otro proyecto también se rechaza (400).
    otro_fb = client.put(
        "/api/feed/igfb/apex_ultra/perfil",
        json={
            "redes": [
                {"plataforma": "fb", "url": "https://www.facebook.com/otrajente"}
            ]
        },
        headers={"X-Meta-Owner": token},
    )
    assert otro_fb.status_code == 400
