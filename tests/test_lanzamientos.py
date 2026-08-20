"""Pruebas de los adaptadores de lanzamientos (Bandcamp/SoundCloud/Beatport/Mixcloud)."""

from datetime import date, datetime

from scraper.adapters import bandcamp, beatport, mixcloud, soundcloud

GRID_BANDCAMP = """
<ul class="editable-grid music-grid columns-2 public">
  <li data-item-id="album-1" class="music-grid-item square">
    <a href="/album/forever-2025">
      <div class="art"><img src="https://f4.bcbits.com/img/a1_16.jpg" alt="" /></div>
      <p class="title">Forever (2025)</p>
    </a>
  </li>
  <li data-item-id="album-2" class="music-grid-item square">
    <a href="/album/exilio-2018">
      <div class="art"><img src="https://f4.bcbits.com/img/a2_16.jpg" alt="" /></div>
      <p class="title">Exilio (2018)</p>
    </a>
  </li>
  <li data-item-id="album-3" class="music-grid-item square">
    <a href="https://otro.bandcamp.com/album/a">
      <div class="art"></div><p class="title">Sin año</p>
    </a>
  </li>
</ul>
"""


def test_bandcamp_ultimos_lanzamientos(monkeypatch):
    monkeypatch.setattr(
        bandcamp, "_get", lambda url: (GRID_BANDCAMP, 200)
    )
    items = bandcamp.ultimos_lanzamientos("https://oxte.bandcamp.com/", 6)
    assert len(items) == 3
    assert items[0]["titulo"] == "Forever (2025)"
    assert items[0]["url"] == "https://oxte.bandcamp.com/album/forever-2025"
    assert items[0]["fecha"] == date(2025, 1, 1)
    assert items[0]["imagen"] == "https://f4.bcbits.com/img/a1_16.jpg"
    assert items[1]["fecha"] == date(2018, 1, 1)
    assert items[2]["fecha"] is None
    assert items[2]["url"] == "https://otro.bandcamp.com/album/a"


def test_bandcamp_sin_red_lanza_error(monkeypatch):
    monkeypatch.setattr(bandcamp, "_get", lambda url: (None, None))
    try:
        bandcamp.ultimos_lanzamientos("https://x.bandcamp.com/", 3)
        assert False
    except bandcamp.BandcampError:
        pass


def test_bandcamp_pagina_bloqueada_lanza_error(monkeypatch):
    monkeypatch.setattr(bandcamp, "_get", lambda url: ("<html>verificación</html>", 200))
    try:
        bandcamp.ultimos_lanzamientos("https://x.bandcamp.com/", 3)
        assert False
    except bandcamp.BandcampError:
        pass


def test_soundcloud_ultimas_pistas(monkeypatch):
    class Respuesta:
        ok = True

        def json(self):
            return {
                "collection": [
                    {
                        "kind": "track",
                        "title": "Tema nuevo",
                        "permalink_url": "https://soundcloud.com/oxte/tema-nuevo",
                        "created_at": "2026-08-01T12:00:00Z",
                        "artwork_url": "https://i1.sndcdn.com/art.jpg",
                    },
                    {"kind": "playlist", "title": "no entra"},
                    {
                        "kind": "track",
                        "title": "Otro",
                        "permalink_url": "",
                        "created_at": "2026-07-01T12:00:00Z",
                    },
                ]
            }

    monkeypatch.setattr(soundcloud, "_user_id", lambda url: 123)
    monkeypatch.setattr(soundcloud, "_client_id", lambda url: "cid")
    monkeypatch.setattr(
        soundcloud.requests, "get", lambda *a, **k: Respuesta()
    )
    items = soundcloud.ultimas_pistas("https://soundcloud.com/Oxte", 6)
    assert len(items) == 1
    assert items[0]["titulo"] == "Tema nuevo"
    assert items[0]["url"] == "https://soundcloud.com/oxte/tema-nuevo"
    assert items[0]["fecha"] == datetime(2026, 8, 1, 12, 0)
    assert items[0]["imagen"] == "https://i1.sndcdn.com/art.jpg"


def test_soundcloud_sin_client_id_devuelve_vacio(monkeypatch):
    monkeypatch.setattr(soundcloud, "_user_id", lambda url: 123)
    monkeypatch.setattr(soundcloud, "_client_id", lambda url: "")
    assert soundcloud.ultimas_pistas("https://soundcloud.com/Oxte", 6) == []


def test_mixcloud_ultimos_sets(monkeypatch):
    class Respuesta:
        ok = True

        def json(self):
            return {
                "data": [
                    {
                        "name": "Set oscuro",
                        "url": "https://www.mixcloud.com/xombie/set-oscuro/",
                        "created_time": "2026-05-07T06:00:45Z",
                        "pictures": {"large": "https://img.mixcloud.com/set.jpg"},
                    }
                ]
            }

    monkeypatch.setattr(
        mixcloud.requests, "get", lambda *a, **k: Respuesta()
    )
    items = mixcloud.ultimos_sets("https://www.mixcloud.com/xombie/", 6)
    assert len(items) == 1
    assert items[0]["titulo"] == "Set oscuro"
    assert items[0]["fecha"] == datetime(2026, 5, 7, 6, 0, 45)
    assert items[0]["imagen"] == "https://img.mixcloud.com/set.jpg"


def test_mixcloud_sin_usuario_devuelve_vacio():
    assert mixcloud.ultimos_sets("", 6) == []


NEXT_DATA_BEATPORT = """
<script id="__NEXT_DATA__" type="application/json">
{"props":{"pageProps":{"dehydratedState":{"queries":[
  {"state":{"data":{"results":[
    {"name":"Compilado 003","slug":"compilado-003","id":1824532,
     "publish_date":"2026-06-05","release_date":null,
     "image":{"uri":"https://geo-media.beatport.com/cover.jpg"}}
  ]}}}
]}}}}
</script>
"""


def test_beatport_ultimos_lanzamientos(monkeypatch):
    monkeypatch.setattr(beatport, "_get", lambda url: NEXT_DATA_BEATPORT)
    items = beatport.ultimos_lanzamientos("https://www.beatport.com/artist/x/318913", 6)
    assert len(items) == 1
    assert items[0]["titulo"] == "Compilado 003"
    assert items[0]["url"] == "https://www.beatport.com/release/compilado-003/1824532"
    assert items[0]["fecha"] == datetime(2026, 6, 5)
    assert items[0]["imagen"] == "https://geo-media.beatport.com/cover.jpg"


def test_beatport_sin_resultados_devuelve_vacio(monkeypatch):
    monkeypatch.setattr(
        beatport, "_get", lambda url: '<script id="__NEXT_DATA__" type="application/json">{"props":{}}</script>'
    )
    assert beatport.ultimos_lanzamientos("https://www.beatport.com/artist/x/318913", 6) == []