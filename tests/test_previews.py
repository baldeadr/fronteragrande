"""Pruebas puras de previews y utilidades de plataformas.

Se ejercita la lógica sin red: para TikTok se sustituye el oEmbed por `None`
(fixture `_sin_red` de conftest), cayendo en el fallback del ID de video.
"""

from lib.plataformas import detectar_plataforma, preview_feed


def testdetectar_plataforma():
    assert detectar_plataforma("https://www.instagram.com/p/AbC/") == "ig"
    assert detectar_plataforma("https://www.facebook.com/x/posts/1") == "fb"
    assert detectar_plataforma("https://www.tiktok.com/@x/video/123") == "tt"
    assert detectar_plataforma("https://youtu.be/abcdefgh123") == "yt"
    assert detectar_plataforma("https://open.spotify.com/artist/x") is None


def test_detectar_plataforma_djs():
    assert detectar_plataforma("https://www.beatport.com/artist/x/123") == "beatport"
    assert detectar_plataforma("https://www.mixcloud.com/x/sets/y/") == "mixcloud"


def test_preview_youtube():
    preview = preview_feed(
        {"url": "https://www.youtube.com/watch?v=abcdefgh123", "fuente": "yt"}
    )
    assert preview["tipo"] == "youtube"
    assert preview["embed_url"] == "https://www.youtube.com/embed/abcdefgh123"
    assert preview["thumbnail"].startswith("https://i.ytimg.com/vi/abcdefgh123/")


def test_preview_instagram():
    preview = preview_feed(
        {"url": "https://www.instagram.com/p/AbCdEfGhIjK/", "fuente": "ig"}
    )
    assert preview["tipo"] == "instagram"
    assert "AbCdEfGhIjK" in preview["embed_url"]


def test_preview_facebook():
    preview = preview_feed(
        {"url": "https://www.facebook.com/x/posts/123", "fuente": "fb"}
    )
    assert preview["tipo"] == "facebook"
    assert "plugins/post.php" in preview["embed_url"]


def test_preview_tiktok_sin_oembed():
    preview = preview_feed(
        {"url": "https://www.tiktok.com/@x/video/123456789", "fuente": "tt"}
    )
    assert preview["tipo"] == "tiktok"
    assert preview["video_id"] == "123456789"
    assert preview["embed_url"] == "https://www.tiktok.com/embed/v2/123456789"


def test_preview_mixcloud(monkeypatch):
    monkeypatch.setattr(
        "lib.plataformas.mixcloud_oembed",
        lambda url: {
            "title": "Darkwave 9",
            "author_name": "Xombie",
            "thumbnail_url": "https://img.mixcloud.com/x.jpg",
        },
    )
    monkeypatch.setattr(
        "lib.plataformas.mixcloud_embed_url",
        lambda url: "https://www.mixcloud.com/widget/iframe/?feed=x",
    )
    preview = preview_feed(
        {"url": "https://www.mixcloud.com/xombie/sets/darkwave-9/", "fuente": "mixcloud"}
    )
    assert preview["tipo"] == "mixcloud"
    assert preview["title"] == "Darkwave 9"
    assert preview["thumbnail"] == "https://img.mixcloud.com/x.jpg"


def test_preview_beatport_texto():
    preview = preview_feed(
        {"url": "https://www.beatport.com/artist/x/123", "fuente": "beatport"}
    )
    assert preview["tipo"] == "texto"


def test_preview_texto():
    preview = preview_feed({"url": "https://x.com/y", "fuente": "web"})
    assert preview["tipo"] == "texto"


def test_preview_con_imagen():
    preview = preview_feed(
        {"url": "https://x.com/y", "fuente": "web", "imagen": "https://img.com/a.jpg"}
    )
    assert preview["tipo"] == "imagen"
    assert preview["thumbnail"] == "https://img.com/a.jpg"


def test_preview_url_nula():
    preview = preview_feed({"url": None, "fuente": "escena"})
    assert preview["tipo"] == "texto"