"""Carrusel para artistas: verificación de cuenta y beneficios.

7 slides con copy factual del proyecto: alta voluntaria, verificación por
conexión OAuth (FB/IG/TikTok), sync automático de contenido, promo en redes,
playlist semanal, push a fans y tarjeta OpenGraph.
"""
from .sistema import (
    ACCENT, BG, MUTED, SURFACE2, TEXT, Slide, ajustar_fs, ancho, centrar,
    font_rol,
)


def a_portada(W, H, reel):
    """Slide 1: Logo + gancho directo al artista."""
    s = Slide(W, H, "hero")
    s.fondo_imagen("art-portada-bg.jpg", opacity=0.4, velo=0.4)
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
        [("¿Haces música", TEXT)],
        [("en ", TEXT), ("la frontera?", ACCENT)],
    ]
    for i, frags in enumerate(lineas):
        s.linea_compuesta(W / 2, y + i * lh + fs * 0.78, frags, fs, rol="anton")
    s.desliza(desliza_y)
    return s


def _slide_outcomes(s, W, H, reel, frags_list, kicker, sub=None):
    """Kicker + líneas de outcomes (+ sub opcional) centrados."""
    fs = ajustar_fs(frags_list, 64, "anton", W - 200)
    lh = fs * 1.24
    kick = 28
    kgap = 70 if reel else 64
    desliza_y = 1400 if reel else H - 70
    fs_sub = 28 if reel else 24
    sgap = 52 if reel else 44
    total = kgap + lh * len(frags_list) + (sgap + fs_sub if sub else 0)
    top = centrar(total, 50, desliza_y - 36)
    s.texto(W / 2, top + kick * 0.8, kicker, kick, bold=True, color=ACCENT,
            spacing=6, anchor="middle", etiqueta="kick", rol="anton")
    y = top + kgap
    for i, frags in enumerate(frags_list):
        s.linea_compuesta(W / 2, y + i * lh + fs * 0.78, frags, fs, rol="anton")
    if sub:
        ys = y + lh * len(frags_list) + sgap
        s.texto(W / 2, ys, sub, fs_sub, color=MUTED, anchor="middle",
                etiqueta="sub", rol="space")
    s.desliza(desliza_y)


def a_perfil(W, H, reel):
    """Slide 2: Perfil gratis — qué obtienes al sumarte."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("art-directorio-bg.jpg", opacity=0.5, velo=0.2)
    fs = 76 if reel else 72
    lh = fs * 1.22
    kick = 30
    kgap = 74 if reel else 64
    fs_sub = 28 if reel else 24
    g1 = 56 if reel else 48
    g2 = 44 if reel else 38
    desliza_y = 1400 if reel else H - 70
    total = kick + kgap + lh * 3 + g1 + g2
    top = centrar(total, 50, desliza_y - 36)
    s.texto(W / 2, top + kick * 0.8, "PARA BANDAS, SOLISTAS Y DJ'S", kick,
            bold=True, color=ACCENT, spacing=6, anchor="middle",
            etiqueta="kick", rol="anton")
    y = top + kick + kgap
    lineas = [
        [("Tu perfil profesional", TEXT)],
        [("en el directorio", ACCENT)],
        [("de tu escena", TEXT)],
    ]
    for i, frags in enumerate(lineas):
        s.linea_compuesta(W / 2, y + i * lh + fs * 0.78, frags, fs, rol="anton")
    ys = y + lh * 3 + g1
    s.texto(W / 2, ys, "Gratis · Tarda 2 minutos", fs_sub, color=MUTED,
            anchor="middle", etiqueta="sub1", rol="space")
    s.texto(W / 2, ys + g2, "Basta una red social para empezar", fs_sub,
            color=MUTED, anchor="middle", etiqueta="sub2", rol="space")
    s.desliza(desliza_y)
    return s


def a_buscate(W, H, reel):
    """Slide 3: Dos caminos — reclamarse del directorio o registrarse."""
    s = Slide(W, H, "hero")
    s.fondo_imagen("art-busqueda-bg.jpg", opacity=0.3, velo=0.5)
    _slide_outcomes(
        s, W, H, reel,
        [
            [("Búscate ", ACCENT), ("y reclama tu perfil", TEXT)],
            [("¿No apareces? ", TEXT), ("Regístralo gratis", ACCENT)],
        ],
        "¿YA ESTÁS EN EL DIRECTORIO?",
        sub="Estamos mapeando toda la escena de la frontera",
    )
    return s


def _check_path(s, cx, cy, r):
    d = (f"M{cx - r*0.5:.1f} {cy:.1f} "
         f"L{cx - r*0.12:.1f} {cy + r*0.36:.1f} "
         f"L{cx + r*0.55:.1f} {cy - r*0.4:.1f}")
    s.forma(
        f'<path d="{d}" fill="none" stroke="{BG}" stroke-width="{r*0.26:.1f}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )


def a_pasos(W, H, reel):
    """Slide 3: Verifica tu cuenta en 3 pasos."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("art-check.jpg", opacity=0.35, velo=0.45)
    kick = 30
    fs = 54 if reel else 52
    r = 40 if reel else 34
    row_gap = 66 if reel else 48
    kgap = 84 if reel else 66
    fs_sub = 26 if reel else 24
    sgap = 68 if reel else 54
    pasos = ["Abre tu perfil", "Conecta tus redes", "Obtén tu check"]
    f_txt = font_rol("anton", fs, 700)
    maxw = max(ancho(p, f_txt) for p in pasos)
    col_w = r * 2 + 30 + maxw
    x_left = W / 2 - col_w / 2
    cx_col = x_left + r
    x_txt = x_left + r * 2 + 30
    row_h = r * 2
    desliza_y = 1400 if reel else H - 70
    total = kick + kgap + row_h * 3 + row_gap * 2 + sgap + fs_sub
    top = centrar(total, 50, desliza_y - 36)
    s.texto(W / 2, top + kick * 0.8, "VERIFICA TU PERFIL", kick, bold=True,
            color=ACCENT, spacing=6, anchor="middle", etiqueta="kick",
            rol="anton")
    y0 = top + kick + kgap
    for i, p in enumerate(pasos):
        cy = y0 + row_h / 2 + i * (row_h + row_gap)
        ultimo = i == len(pasos) - 1
        if ultimo:
            s.circulo(cx_col, cy, r, fill=ACCENT)
            _check_path(s, cx_col, cy, r)
        else:
            s.circulo(cx_col, cy, r, fill=SURFACE2, stroke=ACCENT, stroke_w=3)
            s.texto(cx_col, cy + 14, str(i + 1), 40, color=ACCENT,
                    anchor="middle", rol="anton", registrar=False)
        s.caja(x_left, cy - row_h / 2, col_w, row_h, f"paso{i}")
        s.texto(x_txt, cy + fs * 0.37, p, fs, color=TEXT, rol="anton",
                registrar=False)
    ys = y0 + row_h * 3 + row_gap * 2 + sgap
    s.texto(W / 2, ys, "Conecta tu Facebook o Instagram", fs_sub,
            color=MUTED, anchor="middle", etiqueta="sub", rol="space")
    s.desliza(desliza_y)
    return s


def a_contenido(W, H, reel):
    """Slide 4: Tu contenido de redes, dentro de la app."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("art-feed.jpg", opacity=0.35, velo=0.45)
    _slide_outcomes(
        s, W, H, reel,
        [
            [("Tus posts llegan solos", TEXT)],
            [("al feed de la app", ACCENT)],
            [("Tus toquines entran", TEXT)],
            [("a la agenda de eventos", ACCENT)],
        ],
        "TU CONTENIDO, AUTOMÁTICO",
        sub="Facebook · Instagram",
    )
    return s


def a_promo(W, H, reel):
    """Slide 5: Promoción y alcance extra por verificarte."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("art-playlist.jpg", opacity=0.35, velo=0.45)
    _slide_outcomes(
        s, W, H, reel,
        [
            [("Te promovemos ", TEXT), ("en nuestras redes", ACCENT)],
            [("Entras a la playlist ", TEXT), ("semanal", ACCENT)],
            [("Notificaciones ", TEXT), ("a tus fans", ACCENT)],
        ],
        "MÁS ALCANCE PARA TI",
        sub="Playlist en Spotify cada lunes",
    )
    return s


def a_cierre(W, H, reel):
    """Slide 7: Cierre — dominio + recap + CTA."""
    s = Slide(W, H, "hero")
    s.fondo_imagen("art-cierre-bg.jpg", opacity=0.35, velo=0.45)
    fs_a = 68
    fs_dom = 70
    fs_sub = 28 if reel else 24
    g1, g2, g3 = (44, 40, 56) if reel else (40, 36, 52)
    total = fs_a * 1.1 + g1 + fs_dom * 1.06 + g2 + fs_sub * 1.3 + g3 + 72
    y = centrar(total, 80 if not reel else 160, H - 140 if not reel else 1560)
    y += s.bloque(W / 2, y, "La escena te está esperando", fs_a, W - 160,
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
    s.pill(W / 2, y, "Suma tu proyecto")
    return s


CARPETA = "artistas-verifica"
SLIDES = [
    ("01-portada", a_portada),
    ("02-perfil-gratis", a_perfil),
    ("03-buscate", a_buscate),
    ("04-verifica-pasos", a_pasos),
    ("05-contenido-app", a_contenido),
    ("06-promocion", a_promo),
    ("07-cierre", a_cierre),
]
