"""Tests del flujo de obtención del token permanente de la página FG.

Cubre `_pagina_por_id` (buscar la página FG entre las administradas) y
`_callback_pagina_fg` (canjear el código y guardar el token en el archivo).

Se sustituyen `_intercambiar_code`, `_token_larga_duracion` y `_pagina_por_id`
para no tocar la red real de Meta.
"""

import backend.feed_meta as fm
from fastapi.responses import RedirectResponse


def test_pagina_por_id_encontrada(monkeypatch):
    """Devuelve la página cuyo id coincide con el solicitado."""
    llamadas = {}

    def fake_get(ruta, params, **kwargs):
        llamadas["ruta"], llamadas["params"] = ruta, params
        resp = type("R", (), {})()
        resp.json = lambda: {
            "data": [{"id": "999", "name": "Otra", "access_token": "tok_otra"},
                     {"id": "1567063665051085", "name": "FG", "access_token": "tok_fg"}]
        }
        resp.raise_for_status = lambda: None
        return resp

    monkeypatch.setattr(fm.requests, "get", fake_get)
    pagina = fm._pagina_por_id("user_tok", "1567063665051085")

    assert pagina is not None
    assert pagina["access_token"] == "tok_fg"
    assert "/me/accounts" in llamadas["ruta"]
    assert llamadas["params"]["access_token"] == "user_tok"


def test_pagina_por_id_no_admin_fallback(monkeypatch):
    """Si la página FG específica no está administrada, devuelve la primera
    página de la cuenta (fallback: no depende de un FG_PAGE_ID bien puesto)."""
    def fake_get(ruta, params, **kwargs):
        resp = type("R", (), {})()
        resp.json = lambda: {"data": [{"id": "999", "name": "Otra",
                                       "access_token": "tok"}]}
        resp.raise_for_status = lambda: None
        return resp

    monkeypatch.setattr(fm.requests, "get", fake_get)
    pagina = fm._pagina_por_id("user_tok", "1567063665051085")
    assert pagina is not None
    assert pagina["access_token"] == "tok"


def test_pagina_por_id_sin_paginas(monkeypatch):
    """Si la cuenta no administra ninguna página, devuelve None."""
    def fake_get(ruta, params, **kwargs):
        resp = type("R", (), {})()
        resp.json = lambda: {"data": []}
        resp.raise_for_status = lambda: None
        return resp

    monkeypatch.setattr(fm.requests, "get", fake_get)
    assert fm._pagina_por_id("user_tok", None) is None


def test_pagina_por_id_por_nombre(monkeypatch):
    """Si FG_PAGE_ID no coincide (por ser App ID), se elige la página cuyo
    nombre contiene 'Frontera Grande', aunque no sea la primera."""
    def fake_get(ruta, params, **kwargs):
        resp = type("R", (), {})()
        resp.json = lambda: {"data": [
            {"id": "999", "name": "Apex Ultra", "access_token": "tok_apex"},
            {"id": "777", "name": "Frontera Grande Oficial", "access_token": "tok_fg"},
        ]}
        resp.raise_for_status = lambda: None
        return resp

    monkeypatch.setattr(fm.requests, "get", fake_get)
    # FG_PAGE_ID (1567063665051085) no coincide con ninguna página:
    pagina = fm._pagina_por_id("user_tok", "1567063665051085",
                               preferir_nombre="Frontera Grande")
    assert pagina["access_token"] == "tok_fg"


def test_pagina_por_id_nombre_segunda_prioridad(monkeypatch):
    """El id coincide primero; el nombre solo como respaldo."""
    def fake_get(ruta, params, **kwargs):
        resp = type("R", (), {})()
        resp.json = lambda: {"data": [
            {"id": "555", "name": "Frontera Grande X", "access_token": "tok_x"},
            {"id": "777", "name": "Apex Ultra", "access_token": "tok_apex"},
        ]}
        resp.raise_for_status = lambda: None
        return resp

    monkeypatch.setattr(fm.requests, "get", fake_get)
    pagina = fm._pagina_por_id("user_tok", "777", preferir_nombre="Frontera Grande")
    assert pagina["access_token"] == "tok_apex"


def test_callback_pagina_fg_ok(monkeypatch, tmp_path):
    """Flujo feliz: guarda el token en el archivo y redirige con fg_token=ok."""
    archivo = tmp_path / "fg_token.txt"
    monkeypatch.setattr(fm, "FG_PAGE_TOKEN_FILE", str(archivo))
    monkeypatch.setenv("FG_PAGE_ID", "1567063665051085")
    monkeypatch.setattr(fm, "_intercambiar_code", lambda code: "corto")
    monkeypatch.setattr(fm, "_token_larga_duracion", lambda short: "largo")

    def fake_pagina(largo, pid, **kw):
        llamada[0] = kw.get("preferir_nombre")
        return {"id": pid, "access_token": "PERMANENTE_FG"}
    llamada = [None]
    monkeypatch.setattr(fm, "_pagina_por_id", fake_pagina)

    resp = fm._callback_pagina_fg("code123")

    assert isinstance(resp, RedirectResponse)
    assert "fg_token=ok" in resp.headers["location"]
    assert archivo.read_text(encoding="utf-8") == "PERMANENTE_FG"
    assert llamada[0] == "Frontera Grande"


def test_callback_pagina_fg_no_admin(monkeypatch, tmp_path):
    """Si no es admin de la página FG, no escribe token y avisa."""
    archivo = tmp_path / "fg_token.txt"
    monkeypatch.setattr(fm, "FG_PAGE_TOKEN_FILE", str(archivo))
    monkeypatch.setenv("FG_PAGE_ID", "1567063665051085")
    monkeypatch.setattr(fm, "_intercambiar_code", lambda code: "corto")
    monkeypatch.setattr(fm, "_token_larga_duracion", lambda short: "largo")
    monkeypatch.setattr(fm, "_pagina_por_id", lambda largo, pid, **kw: None)

    resp = fm._callback_pagina_fg("code123")

    assert isinstance(resp, RedirectResponse)
    assert "fg_token=no_admin" in resp.headers["location"]
    assert not archivo.exists() or archivo.read_text(encoding="utf-8") == ""


def test_callback_pagina_fg_sin_page_id(monkeypatch, tmp_path):
    """Sin FG_PAGE_ID configurado, redirige con fg_token=error."""
    archivo = tmp_path / "fg_token.txt"
    monkeypatch.setattr(fm, "FG_PAGE_TOKEN_FILE", str(archivo))
    monkeypatch.setenv("FG_PAGE_ID", "")

    resp = fm._callback_pagina_fg("code123")

    assert isinstance(resp, RedirectResponse)
    assert "fg_token=error" in resp.headers["location"]
    assert not archivo.exists()