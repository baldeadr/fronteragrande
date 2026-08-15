from scraper.adapters.spotify_public import artist_id_from_url, extraer_oyentes_html


def test_artist_id_tolera_parametros_de_spotify():
    assert artist_id_from_url(
        "https://open.spotify.com/artist/4XBDcEcl2gI595pVdJcOwh?si=abc"
    ) == "4XBDcEcl2gI595pVdJcOwh"


def test_extrae_oyentes_desde_la_descripcion_publica():
    html = '<meta property="og:description" content="Artist · 645 monthly listeners.">'
    assert extraer_oyentes_html(html) == 645


def test_extrae_oyentes_con_sufijo():
    html = '<div data-testid="monthly-listeners-label">1.2K monthly listeners</div>'
    assert extraer_oyentes_html(html) == 1200


def test_devuelve_none_sin_metrica():
    assert extraer_oyentes_html("<html>Sin métrica</html>") is None
