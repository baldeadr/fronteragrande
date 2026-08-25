"""Carrusel de presentación de Frontera Grande (5 slides).

Migrado tal cual desde `generar_carrousel_v2.py`; el copy es outcome-focused
y neutro (fans + artistas), estilo nativo IG/FB.
"""
from .sistema import ACCENT, MUTED, TEXT, Slide, ajustar_fs, centrar


def s_portada(W, H, reel):
    """Slide 1: Logo + promesa."""
    s = Slide(W, H, "hero")
    s.fondo_imagen("01-portada-bg.jpg", opacity=0.4, velo=0.4)
    fs = 104 if reel else 92
    lh = fs * 1.16
    logo_sz = 250 if reel else 230
    gap_logo = 90 if reel else 64
    desliza_y = 1500 if reel else H - 70
    total = logo_sz + gap_logo + lh * 2
    top = centrar(total, 60, desliza_y - 40)
    s.logo_fg(W / 2, top, logo_sz)
    y = top + logo_sz + gap_logo
    lineas = [
        [("¿Quién está sonando", TEXT)],
        [("en ", TEXT), ("tu ciudad?", ACCENT)],
    ]
    for i, frags in enumerate(lineas):
        s.linea_compuesta(W / 2, y + i * lh + fs * 0.78, frags, fs, rol="anton")
    s.desliza(desliza_y)
    return s


def s_que_es(W, H, reel):
    """Slide 2: Qué es — solo tipografía (publicación neutra)."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("02-mapa-bg.jpg", opacity=0.5, velo=0.2)
    fs = ajustar_fs(
        [
            [("Frontera Grande", TEXT)],
            [("es el directorio de artistas", TEXT)],
            [("de la frontera norte", TEXT)],
            [("de Tamaulipas y el Valle de Texas", TEXT)],
        ],
        68, "anton", W - 200,
    )
    lh = fs * 1.22
    fs_sub = 28 if reel else 24
    g1, g2 = (56, 42) if reel else (50, 38)
    desliza_y = 1400 if reel else H - 70
    total = lh * 4 + g1 + g2
    top = centrar(total, 50, desliza_y - 36)
    s.texto(W / 2, top + fs * 0.78, "Frontera Grande", fs,
            color=ACCENT, anchor="middle", etiqueta="h1", rol="anton")
    s.texto(W / 2, top + lh + fs * 0.78, "es el directorio de artistas", fs,
            color=TEXT, anchor="middle", etiqueta="h2", rol="anton")
    s.texto(W / 2, top + lh * 2 + fs * 0.78, "de la frontera norte", fs,
            color=TEXT, anchor="middle", etiqueta="h3", rol="anton")
    s.texto(W / 2, top + lh * 3 + fs * 0.78, "de Tamaulipas y el Valle de Texas", fs,
            color=TEXT, anchor="middle", etiqueta="h4", rol="anton")
    ys = top + lh * 4 + g1
    s.texto(W / 2, ys, "Busca por género y por ciudad", fs_sub,
            color=MUTED, anchor="middle", etiqueta="s1", rol="space")
    s.texto(W / 2, ys + g2, "Si suenan, aparecen aquí", fs_sub,
            color=MUTED, anchor="middle", etiqueta="s2", rol="space")
    s.desliza(desliza_y)
    return s


def _slide_outcomes(s, W, H, reel, frags_list, kicker):
    """Kicker de audiencia + líneas de outcomes — neutro, sin artistas."""
    fs = ajustar_fs(frags_list, 64, "anton", W - 200)
    lh = fs * 1.24
    kick = 28
    kick_to_lines = 70 if reel else 64
    desliza_y = 1400 if reel else H - 70
    total = kick_to_lines + lh * len(frags_list)
    top = centrar(total, 50, desliza_y - 36)
    s.texto(W / 2, top + kick * 0.8, kicker, kick, bold=True, color=ACCENT,
            spacing=6, anchor="middle", etiqueta="kick", rol="anton")
    y = top + kick_to_lines
    for i, frags in enumerate(frags_list):
        s.linea_compuesta(W / 2, y + i * lh + fs * 0.78, frags, fs, rol="anton")
    s.desliza(desliza_y)


def s_para_fans(W, H, reel):
    """Slide 3: Para fans."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("03a-fan.jpg", opacity=0.35, velo=0.45)
    _slide_outcomes(
        s, W, H, reel,
        [
            [("Descubres música ", TEXT), ("de tu ciudad", ACCENT)],
            [("Te avisan ", TEXT), ("cuando tu artista publica", ACCENT)],
            [("La playlist semanal ", TEXT), ("la arman ellos", ACCENT)],
        ],
        "PARA LOS FANS",
    )
    return s


def s_para_artistas(W, H, reel):
    """Slide 4: Para artistas."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("03b-artista.jpg", opacity=0.35, velo=0.45)
    _slide_outcomes(
        s, W, H, reel,
        [
            [("Sumas tu proyecto ", TEXT), ("al directorio", ACCENT)],
            [("Tus posts llegan solos ", TEXT), ("a tus fans", ACCENT)],
            [("Gratis. ", TEXT), ("Sin algoritmo.", ACCENT), (" Tú mandas.", TEXT)],
        ],
        "PARA LOS ARTISTAS",
    )
    return s


def s_cierre(W, H, reel):
    """Slide 5: Cierre unificado — dominio + recap de ofertas + CTA único."""
    s = Slide(W, H, "hero")
    s.fondo_imagen("05-link.jpg", opacity=0.35, velo=0.45)
    fs_a = 68
    fs_dom = 70
    fs_sub = 28 if reel else 24
    g1, g2, g3 = (44, 40, 56) if reel else (40, 36, 52)
    total = fs_a * 1.1 + g1 + fs_dom * 1.06 + g2 + fs_sub * 1.3 + g3 + 72
    y = centrar(total, 80 if not reel else 160, H - 140 if not reel else 1560)
    y += s.bloque(W / 2, y, "La escena de tu frontera", fs_a, W - 160,
                  color=TEXT, anchor="middle", line_h=1.1, etiqueta="c1",
                  rol="anton")
    y += g1
    s.texto(W / 2, y + fs_dom * 0.8, "FRONTERAGRANDE.MX", fs_dom,
            color=ACCENT, anchor="middle", etiqueta="dominio", rol="archivo")
    y += fs_dom * 1.06
    y += g2
    s.texto(W / 2, y, "Directorio · Eventos · Playlist cada lunes", fs_sub,
            color=MUTED, anchor="middle", etiqueta="recap", rol="space")
    y += g3
    s.pill(W / 2, y, "Link en bio")
    return s


CARPETA = "presentacion"
SLIDES = [
    ("01-portada", s_portada),
    ("02-que-es", s_que_es),
    ("03-para-fans", s_para_fans),
    ("04-para-artistas", s_para_artistas),
    ("05-cierre", s_cierre),
]
