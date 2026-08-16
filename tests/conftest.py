"""Configuración de pytest.

Crea una base SQLite temporal aislada ANTES de importar la app, para que las
pruebas nunca toquen `instance/local_scene.db`. El seed se corre una vez por
sesión (los tests que mutan limpian lo suyo).
"""

import os
import tempfile

_TMPDIR = tempfile.mkdtemp(prefix="escena_tests_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMPDIR}/test.db"
os.environ["ADMIN_PASSWORD"] = "clave_admin_test"

import pytest
from fastapi.testclient import TestClient

from db.database import SessionLocal
from db.seed import seed


@pytest.fixture(scope="session", autouse=True)
def _bd_sembrada():
    seed()
    yield


@pytest.fixture(scope="session")
def client(_bd_sembrada):
    with TestClient(_importar_app()) as c:
        yield c


@pytest.fixture(scope="session")
def session(_bd_sembrada):
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture(autouse=True)
def _sin_red(monkeypatch):
    """Evita llamadas de red a oEmbed (TikTok/Mixcloud) en las pruebas."""
    monkeypatch.setattr("lib.plataformas.tiktok_oembed", lambda url: None)
    monkeypatch.setattr("lib.plataformas.mixcloud_oembed", lambda url: None)
    yield


def _importar_app():
    from backend.main import app

    return app