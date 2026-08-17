"""Pruebas del detalle de artista (perfil completo)."""


def test_detalle_shape(client):
    datos = client.get("/api/artists").json()
    slug = datos[0]["slug"]
    respuesta = client.get(f"/api/artists/{slug}")
    assert respuesta.status_code == 200
    perfil = respuesta.json()

    assert perfil["slug"] == slug
    assert perfil["nombre"]
    assert perfil["segmento"]
    assert perfil["ciudad"]
    assert isinstance(perfil["generos"], list)
    assert perfil["estado_activo"] in ("activo", "en_duda", "inactivo")
    assert isinstance(perfil["estado_registro"], str)
    assert isinstance(perfil["verificado"], bool)
    assert isinstance(perfil["followers"], dict)
    assert "yt" in perfil["followers"]
    assert isinstance(perfil["stats"], dict)
    assert set(perfil["stats"].keys()) >= {
        "ig", "fb", "yt", "tt", "spotify", "bandcamp", "soundcloud",
        "beatport", "mixcloud",
    }
    assert isinstance(perfil["ranking"], dict)
    assert isinstance(perfil["menciones"], list)
    assert set(perfil["analisis"]) == {
        "texto", "tipo", "confianza", "actualizado",
    }
    assert perfil["analisis"]["texto"]
    assert isinstance(perfil["links"], list)
    assert isinstance(perfil["eventos"], list)
    assert isinstance(perfil["feed"], list)
    assert "igfb" in perfil
    assert set(perfil["igfb"]) == {"configurado", "conectado", "pagina_fb", "ig"}


def test_detalle_no_existe_404(client):
    assert client.get("/api/artists/artista-que-no-existe").status_code == 404


def test_detalle_stats_shapes(client):
    datos = client.get("/api/artists").json()
    perfil = client.get(f"/api/artists/{datos[0]['slug']}").json()
    for plataforma, metricas in perfil["stats"].items():
        assert isinstance(metricas, dict)
        for tipo, valor in metricas.items():
            assert tipo in ("seguidores", "vistas", "reproducciones")
            assert valor is None or isinstance(valor, int)


def test_detalle_evento_conyuge(client, session):
    """Un artista con evento en el cartel debe exponerlo en su perfil."""
    from db.models import Event

    eventos = session.query(Event).all()
    if not eventos:
        return
    cartel = next((e.artistas for e in eventos if e.artistas), None)
    if not cartel:
        return
    nombre = cartel.split(",")[0].strip()
    datos = client.get("/api/artists").json()
    slug = next(
        (a["slug"] for a in datos if a["nombre"].lower() in cartel.lower()), None
    )
    if not slug:
        return
    perfil = client.get(f"/api/artists/{slug}").json()
    assert any(nombre.lower() in e["artistas"].lower() for e in perfil["eventos"])
