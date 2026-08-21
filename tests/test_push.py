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


def test_vapid_config_indica_si_esta_configurado(client, monkeypatch):
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "BGf4d8i6lQ2ovnLOQ6dbHqPtj7NYvKOooLp7-X03NbCGTwbLbsNN9nSiRR-lYMkZpXmATfOJyfhxUo4IqawygcA")
    respuesta = client.get("/api/push/vapid-config")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["configurado"] is True
    assert datos["valida"] is True
    assert "public_key" in datos
    assert "private_key" not in datos
