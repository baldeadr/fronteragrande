"""Pruebas doradas de endpoints básicos.

El objetivo de la Fase 0 es fijar el comportamiento actual para poder
refactorizar sin romperlo (contrato de la API estable).
"""

import csv


def _filas_csv(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return [f for f in csv.DictReader(fh) if f.get("id", "").strip()]


def test_health(client):
    respuesta = client.get("/api/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_artists_shape(client):
    respuesta = client.get("/api/artists")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert isinstance(datos, list)
    assert len(datos) == len(_filas_csv("data/escena_local.csv"))
    first = datos[0]
    assert first["slug"]
    assert first["nombre"]
    assert first["segmento"]
    assert first["ciudad"]
    assert isinstance(first["generos"], list)
    assert first["estado_activo"] in ("activo", "en_duda", "inactivo")
    assert "color_estado" in first and first["color_estado"].startswith("#")
    assert isinstance(first["followers"], dict)
    assert set(first["followers"]) == {"ig", "fb", "yt", "spotify", "tt"}
    assert isinstance(first["links"], list)
    assert isinstance(first["menciones"], list)
    assert first["ranking"]["total"] == len(datos)
    assert first["ranking"]["indice"] is not None
    assert first["ranking"]["rank"] is not None


def test_artists_ranking_completo(client):
    datos = client.get("/api/artists").json()
    ranks = [a["ranking"]["rank"] for a in datos]
    indices = [a["ranking"]["indice"] for a in datos]
    assert sorted(ranks) == list(range(1, len(datos) + 1))
    assert all(i >= 0 and i <= 100 for i in indices)


def test_artists_filtros(client):
    datos = client.get("/api/artists").json()
    segmento = datos[0]["segmento"]
    solo = client.get("/api/artists", params={"segmento": segmento}).json()
    assert solo
    assert all(a["segmento"] == segmento for a in solo)

    con_q = client.get("/api/artists", params={"q": datos[0]["nombre"][:4]}).json()
    assert any(
        datos[0]["nombre"].lower() in a["nombre"].lower() for a in con_q
    )

    sin_resultados = client.get(
        "/api/artists", params={"segmento": "no-existe-xyz"}
    ).json()
    assert sin_resultados == []


def test_artists_links_no_busqueda(client):
    datos = client.get("/api/artists").json()
    for a in datos:
        assert all(l["url"] for l in a["links"])


# --- Alta desde el formulario (POST /api/artists) ---------------------------

import pytest
from sqlalchemy import delete, select

from db.database import SessionLocal
from db.models import Artist, ArtistLink


@pytest.fixture(autouse=True)
def _sin_red_onboarding(monkeypatch):
    """Evita red en el onboarding (foto de perfil y feed de YouTube)."""
    monkeypatch.setattr(
        "scraper.adapters.imagenes.imagen_de_artista", lambda links: (None, None)
    )
    monkeypatch.setattr(
        "scraper.adapters.youtube.latest_videos", lambda *a, **kw: []
    )


_SLUGS_PRUEBA = ("banda_de_prueba", "equipo_doble", "equipo_doble_2", "equipo_tres")


def _limpiar_altas():
    sesion = SessionLocal()
    try:
        sesion.execute(
            delete(ArtistLink).where(ArtistLink.artist_id.in_(
                select(Artist.id).where(Artist.slug.in_(_SLUGS_PRUEBA))
            ))
        )
        sesion.execute(delete(Artist).where(Artist.slug.in_(_SLUGS_PRUEBA)))
        sesion.commit()
    finally:
        sesion.close()


def test_crear_artista_formulario(client):
    respuesta = client.post(
        "/api/artists",
        json={
            "nombre": "Banda de Prueba",
            "ciudad": "Matamoros",
            "categoria": "Banda",
            "redes": [
                {"plataforma": "ig", "url": "https://www.instagram.com/bandadeprueba/"}
            ],
        },
    )
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["slug"] == "banda_de_prueba"
    assert datos["nombre"] == "Banda de Prueba"
    assert datos["onboarding"]["estado"] in ("activo", "en_duda", "inactivo")

    detalle = client.get("/api/artists/banda_de_prueba").json()
    assert detalle["segmento"] == "Banda"
    assert detalle["ciudad"] == "Matamoros"
    assert any(l["plataforma"] == "ig" for l in detalle["links"])
    _limpiar_altas()


def test_crear_artista_slug_unico(client):
    for nombre in ("Equipo Doble", "Equipo Doble"):
        respuesta = client.post(
            "/api/artists", json={"nombre": nombre, "categoria": "Solista"}
        )
        assert respuesta.status_code == 201

    slugs = [a["slug"] for a in client.get("/api/artists").json()
             if a["slug"] in _SLUGS_PRUEBA]
    assert slugs == ["equipo_doble", "equipo_doble_2"]
    _limpiar_altas()


def test_crear_artista_validaciones(client):
    sin_nombre = client.post("/api/artists", json={"nombre": "   "})
    assert sin_nombre.status_code == 400
    assert "nombre" in sin_nombre.json()["detail"].lower()

    mala_categoria = client.post(
        "/api/artists", json={"nombre": "X", "categoria": "NoExiste"}
    )
    assert mala_categoria.status_code == 400

    _limpiar_altas()


def test_crear_artista_con_spotify(client, monkeypatch):
    """Alta con enlace de Spotify: el onboarding crea su snapshot sin romper."""
    monkeypatch.setattr(
        "scraper.adapters.spotify_public.obtener_oyentes", lambda url: 1234
    )
    respuesta = client.post(
        "/api/artists",
        json={
            "nombre": "Equipo Tres",
            "categoria": "Solista",
            "ciudad": "Matamoros",
            "redes": [
                {
                    "plataforma": "spotify",
                    "url": "https://open.spotify.com/artist/equipotres",
                }
            ],
        },
    )
    assert respuesta.status_code == 201
    slug = respuesta.json()["slug"]
    assert slug == "equipo_tres"
    assert respuesta.json()["onboarding"]["spotify_oyentes"] == 1234

    detalle = client.get(f"/api/artists/{slug}").json()
    assert any(l["plataforma"] == "spotify" for l in detalle["links"])
    _limpiar_altas()