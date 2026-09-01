"""Pruebas del endpoint de subida de tarjetas promocionales (admin).

El workflow de la playlist genera la tarjeta fuera de la API (GitHub
Actions) y la sube aquí para que Meta pueda descargarla desde una URL pública.
"""

import os
from pathlib import Path

import pytest

import backend.main as main_mod
import lib.promo_fg

TOKEN = {"X-Admin-Token": "clave_admin_test"}

_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


@pytest.fixture
def promos_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(lib.promo_fg, "PROMOS_DIR", tmp_path)
    return tmp_path


def test_subir_promo_requiere_admin(client, promos_dir):
    r = client.post(
        "/api/admin/promos/upload",
        data={"nombre": "playlist_x"},
        files={"file": ("x.jpg", _JPEG, "image/jpeg")},
    )
    assert r.status_code == 403


def test_subir_promo_ok(client, promos_dir):
    r = client.post(
        "/api/admin/promos/upload",
        data={"nombre": "playlist_semanal_20260901"},
        files={"file": ("x.jpg", _JPEG, "image/jpeg")},
        headers=TOKEN,
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert (promos_dir / "playlist_semanal_20260901.jpg").exists()
    r2 = client.get("/api/promos/playlist_semanal_20260901.jpg")
    assert r2.status_code == 200
    assert r2.content == _JPEG


def test_subir_promo_rechaza_no_jpeg(client, promos_dir):
    r = client.post(
        "/api/admin/promos/upload",
        data={"nombre": "bad"},
        files={"file": ("x.jpg", b"no es jpeg", "image/jpeg")},
        headers=TOKEN,
    )
    assert r.status_code == 400


def test_subir_promo_rechaza_nombre_peligroso(client, promos_dir):
    r = client.post(
        "/api/admin/promos/upload",
        data={"nombre": "../../etc/passwd"},
        files={"file": ("x.jpg", _JPEG, "image/jpeg")},
        headers=TOKEN,
    )
    assert r.status_code == 400
