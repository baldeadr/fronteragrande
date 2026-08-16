"""Pruebas de la conexión TikTok (backend/feed_tiktok.py) sin red.

Se sustituyen `_post_token`/`_api` (requests) por respuestas de muestra; se
verifica el parseo de tokens, seguidores y videos, y los endpoints del router.
"""

import backend.feed_tiktok as tt
import pytest
from backend.feed_tiktok import refrescar, tiktok_configurado, user_info, video_list


def test_tiktok_configurado_sin_credenciales():
    assert tiktok_configurado() is False


def test_refrescar(monkeypatch):
    monkeypatch.setattr(
        tt,
        "_post_token",
        lambda params: {
            "access_token": "ACC-1",
            "refresh_token": "REF-2",
            "open_id": "OPEN-9",
        },
    )
    datos = refrescar("REF-1")
    assert datos == {
        "access_token": "ACC-1",
        "refresh_token": "REF-2",
        "open_id": "OPEN-9",
    }


def test_user_info(monkeypatch):
    monkeypatch.setattr(
        tt,
        "_api",
        lambda ruta, method, token, params=None, body=None: {
            "data": {
                "user": {
                    "open_id": "OPEN-9",
                    "display_name": "Oxte",
                    "follower_count": "1234",
                    "avatar_url": "https://p16-va.tiktokcdn.com/av.jpg",
                }
            },
            "error": {"code": "ok"},
        },
    )
    info = user_info("ACC")
    assert info["open_id"] == "OPEN-9"
    assert info["display_name"] == "Oxte"
    assert info["follower_count"] == 1234


def test_video_list(monkeypatch):
    monkeypatch.setattr(
        tt,
        "_api",
        lambda ruta, method, token, params=None, body=None: {
            "data": {
                "videos": [
                    {
                        "id": "7222222222222",
                        "title": "Teaser nuevo",
                        "cover_image_url": "https://p16-tiktokcdn.com/c.jpg",
                        "create_time": 1700000000,
                        "share_url": "https://www.tiktok.com/@oxte/video/7222222222222",
                    },
                    {"id": "7333333333333", "title": "", "create_time": 0},
                ]
            },
            "error": {"code": "ok"},
        },
    )
    items = video_list("ACC", limite=20)
    assert len(items) == 2
    assert items[0]["titulo"] == "Teaser nuevo"
    assert items[0]["imagen"].startswith("https://p16-tiktokcdn.com")
    assert items[0]["fecha"] is not None
    assert items[1]["url"] == "https://www.tiktok.com/@user/video/7333333333333"


def test_video_list_falla_con_video_sin_url(monkeypatch):
    monkeypatch.setattr(
        tt,
        "_api",
        lambda ruta, method, token, params=None, body=None: {
            "data": {"videos": [{"id": "", "title": "sin url"}]},
            "error": {"code": "ok"},
        },
    )
    assert video_list("ACC") == []


def test_login_sin_configurar(client):
    respuesta = client.get("/api/feed/tiktok/login?slug=oxte")
    assert respuesta.status_code == 503


def test_login_incluye_pkce(client, monkeypatch):
    from urllib.parse import parse_qs, urlparse

    monkeypatch.setattr(tt, "CLIENT_KEY", "clave")
    monkeypatch.setattr(tt, "CLIENT_SECRET", "secreto")
    respuesta = client.get(
        "/api/feed/tiktok/login?slug=oxte", follow_redirects=False
    )
    assert respuesta.status_code == 307
    params = parse_qs(urlparse(respuesta.headers["location"]).query)
    assert params["code_challenge_method"] == ["S256"]
    assert "code_challenge" in params
    assert params["state"] == [respuesta.headers["location"].split("state=")[1].split("&")[0]]
    # el challenge en la URL debe corresponder al verifier empaquetado en state
    slug, verifier = tt._decode_state(params["state"][0])
    assert slug == "oxte"
    assert tt._code_challenge(verifier) == params["code_challenge"][0]


def test_callback_envia_code_verifier(client, monkeypatch):
    capturado = {}
    from db.database import SessionLocal
    from lib.repository import ArtistRepository

    s = SessionLocal()
    try:
        oxte = ArtistRepository(s).por_slug("oxte")
        original = (oxte.tt_user_id, oxte.tt_refresh_token, oxte.estado_registro)
    finally:
        s.close()

    def falso_token(params):
        capturado.update(params)
        return {
            "access_token": "ACC",
            "refresh_token": "REF",
            "open_id": "OPEN-1",
        }

    monkeypatch.setattr(tt, "_post_token", falso_token)
    state = tt._encode_state("oxte", "VERIFICADOR")
    respuesta = client.get(
        f"/api/feed/tiktok/callback?code=CODIGO&state={state}",
        follow_redirects=False,
    )
    assert respuesta.status_code == 307
    assert capturado["code_verifier"] == "VERIFICADOR"
    assert capturado["grant_type"] == "authorization_code"
    assert capturado["code"] == "CODIGO"
    # limpia la conexión escrita en la BD compartida para no contaminar otros tests
    s = SessionLocal()
    try:
        oxte = ArtistRepository(s).por_slug("oxte")
        oxte.tt_user_id = original[0]
        oxte.tt_refresh_token = original[1]
        oxte.estado_registro = original[2]
        s.commit()
    finally:
        s.close()


def test_api_no_trata_ok_como_error(monkeypatch):
    """El código de éxito de TikTok es 'ok' (truthy): no debe lanzar error."""
    class Respuesta:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {"user": {"open_id": "X"}}, "error": {"code": "ok", "message": ""}}

    monkeypatch.setattr(tt.requests, "get", lambda *a, **k: Respuesta())
    datos = tt._api("user/info/", "GET", "tok")
    assert datos["error"]["code"] == "ok"


def test_api_error_real_lanza_runtimeerror(monkeypatch):
    class Respuesta:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {}, "error": {"code": "scope_not_authorized", "message": "no autorizado"}}

    monkeypatch.setattr(tt.requests, "get", lambda *a, **k: Respuesta())
    with pytest.raises(RuntimeError, match="no autorizado"):
        tt._api("user/info/", "GET", "tok")


def test_pkce_state_roundtrip():
    verifier = tt._nuevo_verifier()
    slug, ver = tt._decode_state(tt._encode_state("apex_ultra", verifier))
    assert slug == "apex_ultra"
    assert ver == verifier
    # el challenge es base64url sin padding, de 43 caracteres
    assert len(tt._code_challenge(verifier)) == 43


def test_desconectar_requiere_admin(client):
    respuesta = client.post("/api/feed/tiktok/desconectar?slug=oxte")
    assert respuesta.status_code == 403


def test_detalle_expone_estado_tiktok(client):
    respuesta = client.get("/api/artists/oxte")
    assert respuesta.status_code == 200
    tiktok = respuesta.json()["tiktok"]
    assert tiktok["configurado"] is False
    assert tiktok["conectado"] is False