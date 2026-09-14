"""Tests del guard de publicación de la página FG.

Verifica que `_error_pagina_fg` y `publicar_en_fb` NUNCA publiquen cuando el
token de `FG_PAGE_TOKEN` pertenece a otra página (p. ej. Apex Ultra): el
objetivo es que no vuelva a salir un post en nombre de un artista.
"""

import os
from unittest.mock import patch

os.environ.setdefault("FG_PAGE_ID", "12345")
os.environ.setdefault("FG_PAGE_TOKEN", "tok_fg")

import lib.promo_fg as promo_mod
from lib.promo_fg import _error_pagina_fg, publicar_en_fb


class TestErrorPaginaFg:
    """El guard acepta solo la página FG (id o nombre)."""

    def setup_method(self):
        promo_mod._PAGINA_FG_INFO = None
        promo_mod.FG_PAGE_ID = "12345"
        promo_mod.FG_PAGE_TOKEN = "tok_fg"

    @patch("lib.promo_fg._info_pagina_fg")
    def test_ok_por_id(self, mock_info):
        """Coincide el id con FG_PAGE_ID aunque el nombre no sea FG."""
        mock_info.return_value = ("12345", "Cualquier nombre")
        assert _error_pagina_fg() is None

    @patch("lib.promo_fg._info_pagina_fg")
    def test_ok_por_nombre(self, mock_info):
        """Coincide el nombre aunque el id no sea FG_PAGE_ID (App ID)."""
        mock_info.return_value = ("999", "Frontera Grande Oficial")
        assert _error_pagina_fg() is None

    @patch("lib.promo_fg._info_pagina_fg")
    def test_error_pagina_equivocada(self, mock_info):
        """Un token de Apex Ultra nunca pasa el guard."""
        mock_info.return_value = ("888", "Apex Ultra")
        error = _error_pagina_fg()
        assert error is not None
        assert "Apex Ultra" in error
        assert "Frontera Grande" in error

    @patch("lib.promo_fg._info_pagina_fg")
    def test_error_token_invalido(self, mock_info):
        """Sin página resuelta (token vencido/revocado) tampoco pasa."""
        mock_info.return_value = None
        assert _error_pagina_fg() is not None


class TestPublicarEnFbGuard:
    """`publicar_en_fb` aborta antes de tocar Meta si el token es de otra página."""

    @patch("lib.promo_fg._error_pagina_fg")
    @patch("lib.promo_fg.requests.post")
    def test_aborta_con_token_equivocado(self, mock_post, mock_guard):
        mock_guard.return_value = ("FG_PAGE_TOKEN pertenece a la página "
                                   "'Apex Ultra', no a Frontera Grande")
        resultado = publicar_en_fb("caption", "https://example.com/img.png")

        assert resultado["ok"] is False
        assert "Apex Ultra" in resultado["error"]
        mock_post.assert_not_called()