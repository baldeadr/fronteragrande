"""Pruebas de suscripciones y avisos Web Push."""


def test_suscribir_y_dar_de_baja_push(client):
    endpoint = "https://push.example.test/subscription-push-1"
    payload = {
        "endpoint": endpoint,
        "keys": {"p256dh": "clave-publica", "auth": "clave-auth"},
    }

    respuesta = client.post("/api/push/subscribe", json=payload)
    assert respuesta.status_code == 201
    assert respuesta.json()["ok"] is True

    respuesta = client.post("/api/push/unsubscribe", json={"endpoint": endpoint})
    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True}


def test_broadcast_push_requiere_admin_y_devuelve_enviadas(client, monkeypatch):
    monkeypatch.setattr(
        "backend.push.notificar_todos",
        lambda repo, titulo, cuerpo, url: 3,
    )
    payload = {"titulo": "Nuevo evento", "cuerpo": "Nos vemos", "url": "/eventos"}

    respuesta = client.post("/api/push/broadcast", json=payload)
    assert respuesta.status_code == 403

    respuesta = client.post(
        "/api/push/broadcast",
        json=payload,
        headers={"X-Admin-Token": "clave_admin_test"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True, "enviadas": 3}
