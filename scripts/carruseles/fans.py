"""Carrusel para fans: descubre la escena, playlist semanal y avisos.

7 slides con copy factual del proyecto: directorio público por género y
ciudad, feed y agenda de eventos, playlist de Spotify cada lunes,
notificaciones push e instalación de la PWA.
"""
from .sistema import (
    ACCENT, BG, MUTED, SURFACE2, TEXT, Slide, ajustar_fs, ancho, centrar,
    font_rol,
)


def f_portada(W, H, reel):
    """Slide 1: Logo + gancho al fan."""
    s = Slide(W, H, "hero")
    s.fondo_imagen("fans-portada-bg.jpg", opacity=0.4, velo=0.4)
    fs = 104 if reel else 92
    lh = fs * 1.16
    logo_sz = 250 if reel else 230
    gap_logo = 90 if reel else 64
    desliza_y = 1500 if reel else H - 70
    total = logo_sz + gap_logo + lh * 3
    top = centrar(total, 60, desliza_y - 40)
    s.logo_fg(W / 2, top, logo_sz)
    y = top + logo_sz + gap_logo
    lineas = [
        [("¿Ya conoces toda", TEXT)],
        [("la escena de", ACCENT)],
        [("tu frontera?", ACCENT)],
    ]
    for i, frags in enumerate(lineas):
        s.linea_compuesta(W / 2, y + i * lh + fs * 0.78, frags, fs, rol="anton")
    s.desliza(desliza_y)
    return s


def _slide_outcomes(s, W, H, reel, frags_list, kicker, sub=None):
    """Kicker + líneas de outcomes (+ sub opcional) centrados."""
    fs = ajustar_fs(frags_list, 76, "anton", W - 200)
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


def f_explora(W, H, reel):
    """Slide 2: El directorio es público y gratis."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("fans-explora-bg.jpg", opacity=0.35, velo=0.45)
    _slide_outcomes(
        s, W, H, reel,
        [
            [("Descubre bandas, DJ's", TEXT)],
            [("y solistas ", TEXT), ("de tu ciudad", ACCENT)],
        ],
        "EXPLORA EL DIRECTORIO",
        sub="Gratis · Sin registro",
    )
    return s


def f_enterate(W, H, reel):
    """Slide 3: Feed de posts y agenda de eventos."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("fans-toque-bg.jpg", opacity=0.35, velo=0.45)
    _slide_outcomes(
        s, W, H, reel,
        [
            [("Posts nuevos ", TEXT), ("de tus artistas", ACCENT)],
            [("Toquines ", TEXT), ("en la agenda", ACCENT)],
        ],
        "NADA SE TE PASE",
        sub="Toda la escena en un solo feed",
    )
    return s


def f_playlist(W, H, reel):
    """Slide 4: Playlist semanal en Spotify."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("fans-playlist-bg.jpg", opacity=0.35, velo=0.45)
    _slide_outcomes(
        s, W, H, reel,
        [
            [("Playlist nueva ", TEXT), ("en Spotify", ACCENT)],
            [("Solo música ", TEXT), ("de la frontera", ACCENT)],
        ],
        "CADA LUNES",
        sub="Frontera Grande · Descubrimiento Semanal",
    )
    return s


def f_avisos(W, H, reel):
    """Slide 5: Notificaciones push sin algoritmo."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("fans-alerta-bg.jpg", opacity=0.35, velo=0.45)
    _slide_outcomes(
        s, W, H, reel,
        [
            [("Te avisamos cuando", TEXT)],
            [("tu artista publica", ACCENT)],
        ],
        "SIN ALGORITMO",
        sub="Directo a tu celular",
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


def f_instala(W, H, reel):
    """Slide 6: Instala la PWA y activa las notificaciones."""
    s = Slide(W, H, "bg")
    s.fondo_imagen("fans-aviso-bg.jpg", opacity=0.35, velo=0.45)
    kick = 30
    fs = 62 if reel else 60
    r = 40 if reel else 34
    row_gap = 76 if reel else 56
    kgap = 84 if reel else 66
    fs_sub = 28 if reel else 26
    sgap = 68 if reel else 54
    pasos = ["Abre fronteragrande.mx", "Agrégala a pantalla de inicio",
             "Activa las notificaciones"]
    subs = [
        "Android: en Chrome, menú → Agrégala a pantalla de inicio",
        "iPhone: en Safari, Compartir → Agrégala a pantalla de inicio",
    ]
    f_txt = font_rol("anton", fs, 700)
    maxw = max(ancho(p, f_txt) for p in pasos)
    col_w = r * 2 + 30 + maxw
    x_left = W / 2 - col_w / 2
    cx_col = x_left + r
    x_txt = x_left + r * 2 + 30
    row_h = r * 2
    desliza_y = 1400 if reel else H - 70
    sub_lh = fs_sub * 1.6
    total = kick + kgap + row_h * 3 + row_gap * 2 + sgap + \
        sub_lh * (len(subs) - 1) + fs_sub
    top = centrar(total, 50, desliza_y - 36)
    s.texto(W / 2, top + kick * 0.8, "LLEVA LA ESCENA EN TU BOLSILLO", kick,
            bold=True, color=ACCENT, spacing=6, anchor="middle",
            etiqueta="kick", rol="anton")
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
    for i, t in enumerate(subs):
        s.texto(W / 2, ys + i * sub_lh, t, fs_sub, color=MUTED,
                anchor="middle", etiqueta=f"sub{i}", rol="space")
    s.desliza(desliza_y)
    return s


def f_cierre(W, H, reel):
    """Slide 7: Cierre — dominio + recap + CTA."""
    s = Slide(W, H, "hero")
    s.fondo_imagen("fans-cierre-bg.jpg", opacity=0.35, velo=0.45)
    fs_a = 68
    fs_dom = 70
    fs_sub = 28 if reel else 24
    g1, g2, g3 = (44, 40, 56) if reel else (40, 36, 52)
    total = fs_a * 1.1 + g1 + fs_dom * 1.06 + g2 + fs_sub * 1.3 + g3 + 72
    y = centrar(total, 80 if not reel else 160, H - 140 if not reel else 1560)
    y += s.bloque(W / 2, y, "Tu frontera suena", fs_a, W - 160,
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


CARPETA = "fans"
SLIDES = [
    ("01-portada", f_portada),
    ("02-explora", f_explora),
    ("03-enterate", f_enterate),
    ("04-playlist", f_playlist),
    ("05-avisos", f_avisos),
    ("06-instala", f_instala),
    ("07-cierre", f_cierre),
]
