"""Pruebas del CRUD de eventos (admin) y de la ingesta Meta de eventos.

Los tests que mutan la BD comparten la base sembrada: guardan y restauran el
estado de actividad de todos los artistas para no dejar señales artificiales.
"""

from datetime import date, datetime

from backend import feed_meta
from backend.feed_meta import pagina_eventos
from lib.repository import ArtistRepository, EventRepository
from lib.servicios import actualizar_ultimo_evento, recalcular_actividad

TOKEN = {"X-Admin-Token": "clave_admin_test"}


def _snapshot_estados(session):
    return {a.id: (a.estado_activo, a.ultimo_evento) for a in ArtistRepository(session).todos()}


def _restaurar_estados(session, snap):
    for a in ArtistRepository(session).todos():
        a.estado_activo, a.ultimo_evento = snap[a.id]
    session.commit()


def test_pagina_eventos_normaliza(monkeypatch):
    def _grafo(ruta, params):
        assert ruta == "123/events"
        assert params["fields"]
        return {
            "data": [
                {
                    "id": "ev1",
                    "name": "Tocada en la plaza",
                    "start_time": "2026-09-15T20:00:00-0600",
                    "place": {"name": "Plaza Hidalgo"},
                    "description": "Con todas las bandas.",
                },
                {"id": "ev2", "name": "Sin fecha", "start_time": None},
            ]
        }

    monkeypatch.setattr(feed_meta, "_grafo", _grafo)
    items = pagina_eventos("123", "token")
    assert len(items) == 1
    assert items[0]["id"] == "ev1"
    assert items[0]["nombre"] == "Tocada en la plaza"
    assert items[0]["fecha"] == datetime(2026, 9, 15, 20, 0)
    assert items[0]["lugar"] == "Plaza Hidalgo"
    assert items[0]["descripcion"] == "Con todas las bandas."


def test_crear_editar_eliminar_evento_admin(client, session):
    snap = _snapshot_estados(session)
    try:
        nombre = "Evento de prueba admin"
        alta = client.post(
            "/api/admin/events",
            json={
                "nombre": nombre,
                "fecha": "2099-12-31",
                "lugar": "Plaza",
                "ciudad": "Reynosa",
                "artistas": "Nadie En Particular",
            },
            headers=TOKEN,
        )
        assert alta.status_code == 200
        evento_id = alta.json()["id"]
        assert any(
            e["id"] == evento_id and e["nombre"] == nombre
            for e in client.get("/api/events").json()
        )

        editado = client.put(
            f"/api/admin/events/{evento_id}", json={"lugar": "Auditorio"}, headers=TOKEN
        )
        assert editado.status_code == 200
        detalle = next(
            e for e in client.get("/api/events").json() if e["id"] == evento_id
        )
        assert detalle["lugar"] == "Auditorio"

        assert client.delete(f"/api/admin/events/{evento_id}", headers=TOKEN).status_code == 200
        assert not any(
            e["id"] == evento_id for e in client.get("/api/events").json()
        )
    finally:
        _restaurar_estados(session, snap)


def test_eventos_admin_requieren_token(client):
    respuesta = client.post(
        "/api/admin/events", json={"nombre": "Sin permiso"}
    )
    assert respuesta.status_code == 403


def test_repositorio_eventos(session):
    repo = EventRepository(session)
    evento = repo.crear(
        "Repo test", date(2030, 1, 1), "Lugar", "Ciudad", "Cartel", "Q", "fuente-unica-xyz"
    )
    session.flush()
    try:
        assert repo.por_fuente("fuente-unica-xyz") is evento
        assert repo.por_fuente("otra") is None
        repo.actualizar(evento, {"lugar": "Nuevo lugar"})
        session.flush()
        assert evento.lugar == "Nuevo lugar"
        repo.actualizar(evento, {"ciudad": None, "nombre": "Renombrado"})
        session.flush()
        assert evento.nombre == "Renombrado"
    finally:
        repo.eliminar(evento.id)
        session.commit()


def test_actualizar_ultimo_evento_avanza_y_no_regresa(session):
    repo = EventRepository(session)
    artista = ArtistRepository(session).todos()[0]
    original = artista.ultimo_evento
    futuro = repo.crear(
        "Evento prueba actividad", date(2099, 1, 1), "", "", artista.nombre, "", ""
    )
    viejo = repo.crear(
        "Evento viejo", date(2000, 1, 1), "", "", artista.nombre, "", ""
    )
    session.flush()
    try:
        actualizar_ultimo_evento(session, artista)
        assert artista.ultimo_evento == date(2099, 1, 1)
        actualizar_ultimo_evento(session, artista)
        assert artista.ultimo_evento == date(2099, 1, 1)
    finally:
        repo.eliminar(futuro.id)
        repo.eliminar(viejo.id)
        artista.ultimo_evento = original
        session.commit()


def test_recalcular_actividad_funciona(session):
    snap = _snapshot_estados(session)
    try:
        cambios = recalcular_actividad(session)
        session.commit()
        assert isinstance(cambios, list)
    finally:
        _restaurar_estados(session, snap)