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
    assert set(first["followers"]) == {
        "ig", "fb", "yt", "spotify", "tt", "beatport", "mixcloud"
    }
    assert isinstance(first["links"], list)
    assert isinstance(first["menciones"], list)
    assert first["ranking"]["indice"] is not None
    assert first["ranking"]["rank"] is not None


def test_artists_ranking_grupos(client):
    """El ranking se calcula por grupo: escena local (sin liga) y Ligas aparte.

    Cada artista tiene `ranking.total` = tamaño de su grupo, y los rangos son
    consecutivos dentro de cada grupo (no conviven la escena local y las Ligas).
    """
    datos = client.get("/api/artists").json()
    # El ranking ahora es por liga: Escena, En Ascenso, Ligas Mayores, Leyenda.
    por_liga: dict[str, list] = {}
    for a in datos:
        por_liga.setdefault(a["ranking"]["liga"], []).append(a)

    for grupo in por_liga.values():
        indices = [a["ranking"]["indice"] for a in grupo]
        assert all(i >= 0 and i <= 100 for i in indices)
        if grupo:
            assert all(a["ranking"]["total_liga"] == len(grupo) for a in grupo)
            ranks = sorted(a["ranking"]["rank_liga"] for a in grupo)
            assert ranks == list(range(1, len(grupo) + 1))


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


def test_ranking_coherente_con_nivel(client):
    """Todo catalogado muestra su posición de ranking (lista y perfil).

    Regresión del bug de caché: `nivel`/`catalogado` y el ranking deben
    salir del mismo cálculo. Antes, un artista recién ascendido (índice ≥ 50)
    podía quedar con insignia de Liga pero sin `ranking.rank` (y el chart no
    lo listaba en su chip).
    """
    datos = client.get("/api/artists").json()
    catalogados = [a for a in datos if a["catalogado"]]
    for a in catalogados:
        assert a["ranking"]["indice"] is not None, a["slug"]
        assert a["ranking"]["rank_liga"] is not None, a["slug"]
        assert a["ranking"]["total_liga"] is not None, a["slug"]
        assert a["ranking"]["rank_universal"] is not None, a["slug"]
        detalle = client.get(f"/api/artists/{a['slug']}").json()
        assert detalle["catalogado"] is True
        assert detalle["nivel"] == a["nivel"]
        assert detalle["ranking"]["rank_liga"] == a["ranking"]["rank_liga"]
        assert detalle["ranking"]["indice"] == a["ranking"]["indice"]


def test_ranking_consistente_lista_detalle(client):
    """La posición en la lista y en el perfil coinciden para TODOS."""
    datos = client.get("/api/artists").json()
    for a in datos:
        detalle = client.get(f"/api/artists/{a['slug']}").json()
        assert detalle["catalogado"] == a["catalogado"]
        assert detalle["nivel"] == a["nivel"]
        assert detalle["ranking"]["rank"] == a["ranking"]["rank"]
        assert detalle["ranking"]["total"] == a["ranking"]["total"]


def test_admin_invalidar_cache(client):
    """La invalidación de caché exige admin y limpia las claves públicas."""
    from lib.cache import get_cache

    cache = get_cache()
    cache.set("artists:prueba", {"x": 1}, ttl=300)
    cache.set("feed:prueba", {"x": 1}, ttl=300)
    cache.set("stats:prueba", {"x": 1}, ttl=300)
    cache.set("ranking:prueba", {"x": 1}, ttl=300)

    sin_token = client.post("/api/admin/cache-invalidate")
    assert sin_token.status_code == 403

    token = {"X-Admin-Token": "clave_admin_test"}
    respuesta = client.post("/api/admin/cache-invalidate", headers=token)
    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True}

    for clave in ("artists:prueba", "feed:prueba", "stats:prueba", "ranking:prueba"):
        assert cache.get(clave) is None, clave


def test_artists_links_no_busqueda(client):
    datos = client.get("/api/artists").json()
    for a in datos:
        assert all(l["url"] for l in a["links"])


# --- Alta desde el formulario (POST /api/artists) ---------------------------

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from db.database import SessionLocal
from db.models import AltaRegistro, Artist, ArtistLink


@pytest.fixture(autouse=True)
def _limpieza_test():
    """Limpia altas de prueba y registros de rate-limit antes de cada test."""
    _limpiar_altas()
    yield


@pytest.fixture(autouse=True)
def _sin_red_onboarding(monkeypatch):
    """Evita red en el onboarding (foto de perfil y feed de YouTube)."""
    monkeypatch.setattr(
        "scraper.adapters.imagenes.imagen_de_artista", lambda links: (None, None)
    )
    monkeypatch.setattr(
        "scraper.adapters.youtube.latest_videos", lambda *a, **kw: []
    )


_SLUGS_PRUEBA = (
    "banda_de_prueba",
    "banda_con_x",
    "equipo_doble",
    "equipo_doble_2",
    "equipo_tres",
    "banda_a_borrar",
    "banda_a_editar",
    "banda_a_editar_2",
    "banda_a_validar",
)


class _FakeDatetime:
    _now = datetime.utcnow()

    @classmethod
    def utcnow(cls):
        return cls._now

    @classmethod
    def avanzar(cls, minutos: int):
        cls._now += timedelta(minutes=minutos)


@pytest.fixture
def tiempo_congelado(monkeypatch):
    _FakeDatetime._now = datetime.utcnow()
    monkeypatch.setattr("lib.servicios.datetime", _FakeDatetime)
    return _FakeDatetime


def _limpiar_altas():
    sesion = SessionLocal()
    try:
        sesion.execute(
            delete(ArtistLink).where(ArtistLink.artist_id.in_(
                select(Artist.id).where(Artist.slug.in_(_SLUGS_PRUEBA))
            ))
        )
        sesion.execute(delete(Artist).where(Artist.slug.in_(_SLUGS_PRUEBA)))
        sesion.execute(delete(AltaRegistro))
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
            "generos": "Rock, Indie",
            "bio": "Una bio breve de la banda de prueba.",
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
    assert detalle["generos"] == ["Rock", "Indie"]
    assert detalle["bio"] == "Una bio breve de la banda de prueba."
    assert any(l["plataforma"] == "ig" for l in detalle["links"])
    _limpiar_altas()


def test_crear_artista_con_x_y_correo(client):
    respuesta = client.post(
        "/api/artists",
        json={
            "nombre": "Banda con X",
            "ciudad": "Reynosa",
            "categoria": "Banda",
            "redes": [
                {"plataforma": "ig", "url": "https://www.instagram.com/bandaconx/"},
                {"plataforma": "x", "url": "https://x.com/bandaconx"},
                {"plataforma": "email", "url": "contacto@bandaconx.mx"},
            ],
        },
    )
    assert respuesta.status_code == 201
    detalle = client.get("/api/artists/banda_con_x").json()
    links = {(l["plataforma"], l["url"]) for l in detalle["links"]}
    assert ("ig", "https://www.instagram.com/bandaconx/") in links
    assert ("x", "https://x.com/bandaconx") in links
    assert ("email", "mailto:contacto@bandaconx.mx") in links
    _limpiar_altas()


def test_crear_artista_slug_unico(client):
    for i, nombre in enumerate(("Equipo Doble", "Equipo Doble")):
        respuesta = client.post(
            "/api/artists",
            json={
                "nombre": nombre,
                "categoria": "Solista",
                "redes": [{"plataforma": "ig", "url": f"https://www.instagram.com/equipodoble{i}/"}],
            },
            headers={"X-Forwarded-For": f"198.51.100.{10 + i}"},
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
        "/api/artists",
        json={
            "nombre": "X",
            "categoria": "NoExiste",
            "redes": [{"plataforma": "ig", "url": "https://www.instagram.com/x/"}],
        },
    )
    assert mala_categoria.status_code == 400

    sin_redes = client.post(
        "/api/artists",
        json={"nombre": "Sin Redes", "categoria": "Banda", "redes": []},
    )
    assert sin_redes.status_code == 400
    assert "enlace" in sin_redes.json()["detail"].lower()

    demasiadas_redes = client.post(
        "/api/artists",
        json={
            "nombre": "Muchas Redes",
            "categoria": "Banda",
            "redes": [
                {"plataforma": "ig", "url": f"https://www.instagram.com/m{i}/"}
                for i in range(7)
            ],
        },
    )
    assert demasiadas_redes.status_code == 400
    assert "máximo" in demasiadas_redes.json()["detail"].lower()

    _limpiar_altas()


def test_eliminar_artista_requiere_admin(client):
    """Borrar un artista exige el token de administrador (403 sin él)."""
    alta = client.post(
        "/api/artists",
        json={
            "nombre": "Banda a Borrar",
            "categoria": "Banda",
            "redes": [{"plataforma": "ig", "url": "https://www.instagram.com/borrar/"}],
        },
    )
    assert alta.status_code == 201
    slug = alta.json()["slug"]

    sin_token = client.delete(f"/api/artists/{slug}")
    assert sin_token.status_code == 403

    existe = client.get(f"/api/artists/{slug}")
    assert existe.status_code == 200

    _limpiar_altas()


def test_editar_artista_requiere_admin(client):
    """Editar un artista exige el token de administrador (403 sin él)."""
    alta = client.post(
        "/api/artists",
        json={
            "nombre": "Banda a Editar",
            "categoria": "Banda",
            "redes": [{"plataforma": "ig", "url": "https://www.instagram.com/editar/"}],
        },
    )
    assert alta.status_code == 201
    slug = alta.json()["slug"]

    sin_token = client.put(f"/api/artists/{slug}", json={"bio": "nueva bio"})
    assert sin_token.status_code == 403

    existe = client.get(f"/api/artists/{slug}")
    assert existe.status_code == 200
    assert existe.json()["bio"] == ""

    _limpiar_altas()


def test_admin_list_requiere_admin(client):
    """El listado de administración exige el token (403 sin él)."""
    respuesta = client.get("/api/admin/artists")
    assert respuesta.status_code == 403


def test_admin_pendientes_requiere_admin(client):
    """El endpoint de proyectos sin verificar exige token de admin."""
    assert client.get("/api/admin/artists/pending").status_code == 403


def test_admin_pendientes_muestra_no_verificados_viejos(client, session):
    """El panel de revisión lista solo proyectos no verificados >60 días."""
    headers = {"X-Forwarded-For": "203.0.113.77"}
    alta = client.post(
        "/api/artists",
        json={
            "nombre": "Proyecto Viejo",
            "categoria": "Banda",
            "redes": [{"plataforma": "ig", "url": "https://www.instagram.com/viejo/"}],
        },
        headers=headers,
    )
    assert alta.status_code == 201

    # Forzar fecha de registro a 61 días atrás para que aparezca en revisión.
    from lib.repository import ArtistRepository
    artista = ArtistRepository(session).por_slug("proyecto_viejo")
    artista.fecha_registro = date.today() - timedelta(days=61)
    session.commit()

    token = {"X-Admin-Token": "clave_admin_test"}
    respuesta = client.get("/api/admin/artists/pending", headers=token)
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert any(a["slug"] == "proyecto_viejo" for a in datos)
    _limpiar_altas()


def test_editar_artista_con_token(client):
    """Con el token de admin se editan los campos y se reemplazan redes."""
    alta = client.post(
        "/api/artists",
        json={
            "nombre": "Banda a Editar 2",
            "ciudad": "Matamoros",
            "categoria": "Banda",
            "redes": [{"plataforma": "ig", "url": "https://www.instagram.com/banda2/"}],
        },
    )
    assert alta.status_code == 201
    slug = alta.json()["slug"]
    token = {"X-Admin-Token": "clave_admin_test"}

    respuesta = client.put(
        f"/api/artists/{slug}",
        json={
            "nombre": "Banda Editada",
            "ciudad": "Reynosa",
            "generos": "cumbia / norteño",
            "bio": "bio nueva",
            "notas": "nota interna",
            "logros": "un logro",
            "estado_activo": "inactivo",
            "redes": [{"plataforma": "yt", "url": "https://www.youtube.com/@banda2"}],
        },
        headers=token,
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["slug"] == slug

    detalle = client.get(f"/api/artists/{slug}").json()
    assert detalle["nombre"] == "Banda Editada"
    assert detalle["ciudad"] == "Reynosa"
    assert detalle["estado_activo"] == "inactivo"
    assert detalle["bio"] == "bio nueva"
    assert any(l["plataforma"] == "yt" for l in detalle["links"])
    assert all(l["plataforma"] != "ig" for l in detalle["links"])

    _limpiar_altas()


def test_editar_artista_validaciones(client):
    """La edición valida nombre, categoría y estado con el token de admin."""
    alta = client.post(
        "/api/artists",
        json={
            "nombre": "Banda a Validar",
            "categoria": "Banda",
            "redes": [{"plataforma": "ig", "url": "https://www.instagram.com/validar/"}],
        },
    )
    assert alta.status_code == 201
    slug = alta.json()["slug"]
    token = {"X-Admin-Token": "clave_admin_test"}

    vacio = client.put(f"/api/artists/{slug}", json={"nombre": "   "}, headers=token)
    assert vacio.status_code == 400

    mala_categoria = client.put(
        f"/api/artists/{slug}", json={"categoria": "NoExiste"}, headers=token
    )
    assert mala_categoria.status_code == 400

    mal_estado = client.put(
        f"/api/artists/{slug}", json={"estado_activo": "raro"}, headers=token
    )
    assert mal_estado.status_code == 400

    inexistente = client.put(
        "/api/artists/no_existe_xyz", json={"nombre": "X"}, headers=token
    )
    assert inexistente.status_code == 404

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


def test_crear_artista_rechaza_url_duplicada(client, tiempo_congelado):
    """No se puede dar de alta un enlace que ya pertenece a otro artista."""
    url = "https://www.instagram.com/duplicado/"
    ip = "203.0.113.10"
    headers = {"X-Forwarded-For": ip}
    primera = client.post(
        "/api/artists",
        json={
            "nombre": "Primero",
            "categoria": "Banda",
            "redes": [{"plataforma": "ig", "url": url}],
        },
        headers=headers,
    )
    assert primera.status_code == 201

    tiempo_congelado.avanzar(11)
    segunda = client.post(
        "/api/artists",
        json={
            "nombre": "Segundo",
            "categoria": "Solista",
            "redes": [{"plataforma": "ig", "url": url + "?utm_source=test"}],
        },
        headers=headers,
    )
    assert segunda.status_code == 409
    assert "ya está vinculada" in segunda.json()["detail"].lower()
    _limpiar_altas()


def test_crear_artista_rate_limit_por_ip(client, tiempo_congelado):
    """Después de 5 altas la IP se bloquea con 429."""
    ip = "203.0.113.42"
    headers = {"X-Forwarded-For": ip}
    for i in range(5):
        respuesta = client.post(
            "/api/artists",
            json={
                "nombre": f"Rate Limit {i}",
                "categoria": "Banda",
                "redes": [{"plataforma": "ig", "url": f"https://www.instagram.com/rl{i}/"}],
            },
            headers=headers,
        )
        assert respuesta.status_code == 201, f"falló en alta {i}: {respuesta.json()}"
        tiempo_congelado.avanzar(11)

    sexta = client.post(
        "/api/artists",
        json={
            "nombre": "Rate Limit 5",
            "categoria": "Banda",
            "redes": [{"plataforma": "ig", "url": "https://www.instagram.com/rl5/"}],
        },
        headers=headers,
    )
    assert sexta.status_code == 429
    _limpiar_altas()


def test_crear_artista_cooldown_entre_altas(client, tiempo_congelado):
    """La misma IP debe esperar 10 min entre altas consecutivas."""
    ip = "203.0.113.99"
    headers = {"X-Forwarded-For": ip}
    primera = client.post(
        "/api/artists",
        json={
            "nombre": "Cooldown 1",
            "categoria": "Banda",
            "redes": [{"plataforma": "ig", "url": "https://www.instagram.com/cd1/"}],
        },
        headers=headers,
    )
    assert primera.status_code == 201

    tiempo_congelado.avanzar(1)
    segunda = client.post(
        "/api/artists",
        json={
            "nombre": "Cooldown 2",
            "categoria": "Banda",
            "redes": [{"plataforma": "ig", "url": "https://www.instagram.com/cd2/"}],
        },
        headers=headers,
    )
    assert segunda.status_code == 429
    assert "espera" in segunda.json()["detail"].lower()
    _limpiar_altas()
