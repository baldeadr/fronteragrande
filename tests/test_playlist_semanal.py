"""Contrato del generador de playlist semanal.

Protege la lógica de selección aleatoria (una canción por artista primero,
relleno hasta el tamaño) y la cadena de fuentes de canciones (top-tracks →
lanzamientos → búsqueda por nombre filtrada por ID), que debe ser resiliente a
apps de Spotify en modo desarrollo.
"""

from scripts.generar_playlist_semanal import (
    _buscar_por_nombre,
    _canciones_artista,
    seleccionar,
)


def _pool(nombres, por_artista):
    return {
        n: [{"titulo": f"{n} {i}", "uri": f"uri:{n}:{i}"} for i in range(por_artista)]
        for n in nombres
    }


def test_seleccionar_primera_ronda_una_cancion_por_artista():
    pool = _pool([f"artista_{i}" for i in range(18)], 2)
    seleccion = seleccionar(pool, 24, 2)
    assert len(seleccion) == 24
    primeros = {c["uri"] for c in seleccion}
    assert len(primeros) == 24  # sin repetir canciones
    artistas = [c["uri"].split(":")[1] for c in seleccion]
    assert len(set(artistas[:18])) == 18  # los primeros 18 son todos distintos


def test_seleccionar_respeta_por_artista():
    pool = _pool([f"artista_{i}" for i in range(5)], 1)
    seleccion = seleccionar(pool, 10, 1)
    assert len(seleccion) == 5  # solo hay 5 canciones disponibles


def test_seleccionar_respeta_tamanio():
    pool = _pool([f"artista_{i}" for i in range(30)], 2)
    seleccion = seleccionar(pool, 24, 2)
    assert len(seleccion) == 24


def test_buscar_por_nombre_filtra_por_id_exacto(monkeypatch):
    import requests

    tracks = [
        {"uri": "uri:1", "name": "De otro", "artists": [{"id": "otro", "name": "Otro"}], "album": {"name": "A"}},
        {"uri": "uri:2", "name": "La buena", "artists": [{"id": "target", "name": "Banda"}], "album": {"name": "B"}},
    ]

    class Respuesta:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"tracks": {"items": tracks}}

    def fake_get(url, params=None, headers=None, timeout=None):
        return Respuesta()

    monkeypatch.setattr(requests, "get", fake_get)
    resultado = _buscar_por_nombre("token", "Banda", "target", 5)
    assert [c["uri"] for c in resultado] == ["uri:2"]


def test_canciones_artista_fallback_hasta_busqueda(monkeypatch):
    import requests

    llamadas = []

    class Respuesta:
        def __init__(self, status, data=None):
            self.status_code = status
            self._data = data or {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"HTTP {self.status_code}")

        def json(self):
            return self._data

    def fake_get(url, params=None, headers=None, timeout=None):
        llamadas.append(url)
        if "/top-tracks" in url:
            return Respuesta(403)
        if "/albums" in url:
            return Respuesta(403)
        if "/search" in url:
            return Respuesta(
                200,
                {
                    "tracks": {
                        "items": [
                            {"uri": "uri:x", "name": "Tema", "artists": [{"id": "abc", "name": "Banda"}], "album": {"name": "A"}}
                        ]
                    }
                },
            )
        return Respuesta(500)

    monkeypatch.setattr(requests, "get", fake_get)
    canciones, errores = _canciones_artista("token", "abc", "Banda", 2)
    assert [c["uri"] for c in canciones] == ["uri:x"]
    assert len(errores) == 2  # top-tracks y lanzamientos fallaron
    assert llamadas[0].endswith("/top-tracks")
    assert llamadas[-1].endswith("/search")