"""Tests para publicación nativa en Instagram (promo FG)."""

import os
import pytest
from unittest.mock import MagicMock, patch

# Asegurar que las env vars estén disponibles para los tests
os.environ.setdefault("FG_PAGE_ID", "12345")
os.environ.setdefault("FG_PAGE_TOKEN", "fake_token_ig")

from lib.promo_fg import (
    _construir_mensaje_ig,
    _ig_de_fg,
    _extraer_username_ig,
    publicar_en_ig,
    PROMO_IG,
    _IG_FG_CACHE,
)


class TestConstruirMensajeIg:
    """Tests del caption de Instagram."""

    def test_mencion_con_handle(self):
        """Si el artista tiene IG, incluye @handle entre paréntesis."""
        artista = MagicMock()
        artista.nombre = "Apex Ultra"
        artista.ciudad = "Reynosa"
        artista.segmento = "Banda"
        artista.generos = "Rock, Electrónica"

        enlaces = {"fb": "", "ig": "https://instagram.com/apexultramusic"}

        msg = _construir_mensaje_ig(artista, enlaces)

        assert "Apex Ultra (@apexultramusic)" in msg
        assert "🎵" in msg
        assert "🎸" in msg
        assert "#FronteraGrande" in msg
        assert "#Reynosa" in msg

    def test_sin_handle(self):
        """Sin IG, el nombre va sin @handle."""
        artista = MagicMock()
        artista.nombre = "Los Nochebueno"
        artista.ciudad = None
        artista.segmento = None
        artista.generos = None

        enlaces = {"fb": "", "ig": ""}

        msg = _construir_mensaje_ig(artista, enlaces)

        assert "Los Nochebueno" in msg
        assert "@(" not in msg
        assert "se suma a la escena" in msg

    def test_ficha_sin_placeholders(self):
        """Los placeholders [PENDIENTE] no aparecen en la ficha."""
        artista = MagicMock()
        artista.nombre = "Test"
        artista.ciudad = "[PENDIENTE]"
        artista.segmento = "Banda"
        artista.generos = "[PENDIENTE]"

        enlaces = {"ig": ""}

        msg = _construir_mensaje_ig(artista, enlaces)

        assert "[PENDIENTE]" not in msg
        assert "Banda" in msg

    def test_hashtags_ciudad_dynamic(self):
        """El hashtag de ciudad se genera dinámicamente."""
        artista = MagicMock()
        artista.nombre = "Test"
        artista.ciudad = "Matamoros"
        artista.segmento = None
        artista.generos = None

        enlaces = {"ig": ""}

        msg = _construir_mensaje_ig(artista, enlaces)

        assert "#Matamoros" in msg
        assert "#EscenaLocal" in msg

    def test_limite_2200_chars(self):
        """El caption no excede el límite de 2200 chars de IG."""
        artista = MagicMock()
        artista.nombre = "A" * 100
        artista.ciudad = "Ciudad Larga"
        artista.segmento = "Colectivo"
        artista.generos = ", ".join(["Género" * 10 for _ in range(5)])

        enlaces = {"ig": ""}

        msg = _construir_mensaje_ig(artista, enlaces)

        assert len(msg) <= 2200


class TestExtraerUsernameIg:
    """Tests del extractor de username de IG."""

    def test_username_simple(self):
        url = "https://instagram.com/apexultramusic"
        assert _extraer_username_ig(url) == "apexultramusic"

    def test_username_con_slash(self):
        url = "https://instagram.com/apexultramusic/"
        assert _extraer_username_ig(url) == "apexultramusic"

    def test_username_con_query(self):
        url = "https://instagram.com/apexultramusic?igsh=abc123"
        assert _extraer_username_ig(url) == "apexultramusic"


class TestIgDeFg:
    """Tests del cache de IG de la página FG."""

    def setup_method(self):
        _IG_FG_CACHE.clear()

    def test_cache_hit(self):
        """Una vez consultado, se cachea y no vuelve a llamar."""
        _IG_FG_CACHE["id"] = "12345"
        assert _ig_de_fg() == "12345"

    @patch("lib.promo_fg.requests.get")
    def test_sin_vinculacion(self, mock_get):
        """Si la página no tiene IG vinculado, devuelve None."""
        _IG_FG_CACHE.clear()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _ig_de_fg()

        assert result is None
        assert _IG_FG_CACHE.get("id") is None

    @patch("lib.promo_fg.requests.get")
    def test_con_vinculacion(self, mock_get):
        """Si la página tiene IG vinculado, devuelve el ID."""
        _IG_FG_CACHE.clear()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "instagram_business_account": {"id": "17841436889901689"}
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = _ig_de_fg()

        assert result == "17841436889901689"


class TestPublicarEnIg:
    """Tests del flujo de publicación en IG."""

    def setup_method(self):
        _IG_FG_CACHE.clear()

    @patch("lib.promo_fg._ig_de_fg")
    def test_sin_ig_vinculada(self, mock_ig):
        """Si no hay IG vinculada, falla graceful."""
        mock_ig.return_value = None

        result = publicar_en_ig("test caption", "https://example.com/img.jpg")

        assert result["ok"] is False
        assert "vinculado" in result["error"]

    @patch("lib.promo_fg.time.sleep")
    @patch("lib.promo_fg.requests.get")
    @patch("lib.promo_fg.requests.post")
    @patch("lib.promo_fg._ig_de_fg")
    def test_flujo_exitoso(self, mock_ig, mock_post, mock_get, mock_sleep):
        """Flujo completo: contenedor → poll → publicar."""
        mock_ig.return_value = "17841436889901689"

        # Mock para crear contenedor
        mock_resp_crear = MagicMock()
        mock_resp_crear.json.return_value = {"id": "CONTAINER_123"}
        mock_resp_crear.raise_for_status = MagicMock()

        # Mock para poll status
        mock_resp_poll = MagicMock()
        mock_resp_poll.json.return_value = {"status_code": "FINISHED"}

        # Mock para publicar
        mock_resp_pub = MagicMock()
        mock_resp_pub.json.return_value = {"id": "POST_IG_123"}
        mock_resp_pub.raise_for_status = MagicMock()

        mock_post.side_effect = [mock_resp_crear, mock_resp_pub]
        mock_get.return_value = mock_resp_poll

        result = publicar_en_ig("test caption", "https://example.com/img.jpg")

        assert result["ok"] is True
        assert result["post_id"] == "POST_IG_123"

    @patch("lib.promo_fg.time.sleep")
    @patch("lib.promo_fg.requests.get")
    @patch("lib.promo_fg.requests.post")
    @patch("lib.promo_fg._ig_de_fg")
    def test_contenedor_error(self, mock_ig, mock_post, mock_get, mock_sleep):
        """Si el contenedor falla, reporta error."""
        mock_ig.return_value = "17841436889901689"

        mock_resp_crear = MagicMock()
        mock_resp_crear.json.return_value = {"id": "CONTAINER_123"}
        mock_resp_crear.raise_for_status = MagicMock()

        mock_resp_poll = MagicMock()
        mock_resp_poll.json.return_value = {"status_code": "ERROR"}

        mock_post.return_value = mock_resp_crear
        mock_get.return_value = mock_resp_poll

        result = publicar_en_ig("test caption", "https://example.com/img.jpg")

        assert result["ok"] is False
        assert "falló" in result["error"]
