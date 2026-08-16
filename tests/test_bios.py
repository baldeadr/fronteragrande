"""Pruebas de los detectores de bio/géneros y sus utilidades.

Se ejercita la lógica de parseo con HTML/JSON de muestra (sin red) y los
filtros puros de `lib/helpers.py`.
"""

from lib.helpers import es_bio_clara, generos_desde_texto
from scraper.adapters.bandcamp import _parse_bio, _parse_tags
from scraper.adapters.soundcloud import _parse_bio as _parse_soundcloud_bio
from scraper.adapters.youtube import _parse_about

HTML_BANDCAMP = """
<html><head>
<meta property="og:description" content="Post-punk desde la frontera.">
</head><body>
<div id="bio-text">
  <p>Banda de post-punk y coldwave de Reynosa.</p>
  <div class="read-more"><span>more</span></div>
</div>
<a class="tag">post-punk</a>
<a class="tag">darkwave</a>
<a class="tag">frontera</a>
</body></html>
"""


def test_bandcamp_bio_desde_bio_text():
    assert _parse_bio(HTML_BANDCAMP) == "Banda de post-punk y coldwave de Reynosa."


def test_bandcamp_bio_fallback_og():
    html = '<meta property="og:description" content="Una banda de la frontera.">'
    assert _parse_bio(html) == "Una banda de la frontera."


def test_bandcamp_bio_vacia():
    assert _parse_bio("<html></html>") == ""


def test_bandcamp_tags():
    assert _parse_tags(HTML_BANDCAMP) == ["post-punk", "darkwave", "frontera"]


HTML_SOUNDCLOUD = """
<script>window.__sc_hydration = [
  {"hydratable":"user","data":{"username":"dj-vikingo",
    "description":"DJ de darkwave y techno en Matamoros. Set mensual en radio."}},
  {"hydratable":"other","data":{}}
];</script>
"""


def test_soundcloud_bio():
    assert (
        _parse_soundcloud_bio(HTML_SOUNDCLOUD)
        == "DJ de darkwave y techno en Matamoros. Set mensual en radio."
    )


def test_soundcloud_bio_vacia():
    assert _parse_soundcloud_bio("<html></html>") == ""


HTML_YOUTUBE = """
<script>var ytInitialData = {
  "metadata": {
    "channelMetadataRenderer": {
      "description": "Banda de rock alternativo e industrial desde la frontera."
    }
  }
};</script>
"""


def test_youtube_about_desde_yt_initial():
    assert (
        _parse_about(HTML_YOUTUBE)
        == "Banda de rock alternativo e industrial desde la frontera."
    )


def test_youtube_about_fallback_og():
    html = '<meta content="DJ de la escena." property="og:description">'
    assert _parse_about(html) == "DJ de la escena."


def test_youtube_about_vacia():
    assert _parse_about("<html></html>") == ""


def test_es_bio_clara():
    assert es_bio_clara("") is False
    assert es_bio_clara("Texto corto") is False
    assert es_bio_clara("Share your videos with friends, family, and the world") is False
    assert (
        es_bio_clara("Banda de post-punk y coldwave desde Reynosa, Tamaulipas.")
        is True
    )


def test_generos_desde_texto():
    assert generos_desde_texto("Banda de post-punk y coldwave de la frontera") == [
        "post-punk",
        "coldwave",
    ]
    assert generos_desde_texto("DJ de house y techno") == ["house", "techno"]
    assert generos_desde_texto("Sin géneros visibles") == []