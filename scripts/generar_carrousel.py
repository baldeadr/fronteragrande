#!/usr/bin/env python3
"""Genera carruseles de presentación (post 1080x1440 y reel 1080x1920)
con el sistema de diseño real de la web Frontera Grande.

Texto medido en píxeles con PIL + TTF (Archivo Black / Arial): el word-wrap
y las posiciones se calculan antes de dibujar, y un verificador anti-solape
valida los bounding boxes de cada slide.
"""
import base64
import glob
import html
import os
import subprocess
import xml.etree.ElementTree as ET

from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "carrousel")
os.makedirs(OUT, exist_ok=True)

# ── Paleta real (web/app/globals.css) ────────────────────────────────
BG = "#0b0b10"
SURFACE = "#14141b"
SURFACE2 = "#1b1b24"
LINE = "#262633"
TEXT = "#ececf1"
MUTED = "#8a8a9a"
ACCENT = "#9d4edd"
ACCENT_SOFT = "#2a1a33"

# ── Fuentes ──────────────────────────────────────────────────────────
TTF_ARCHIVO = os.path.expanduser("~/.local/share/fonts/ArchivoBlack-Regular.ttf")
TTF_ARIAL = "/usr/share/fonts/msttcore/arial.ttf"
TTF_ARIAL_BD = "/usr/share/fonts/msttcore/arialbd.ttf"
TTF_OSWALD = os.path.expanduser("~/.local/share/fonts/carrusel/Oswald.ttf")
TTF_SPACE = os.path.expanduser("~/.local/share/fonts/carrusel/SpaceGrotesk.ttf")
TTF_JET = os.path.expanduser("~/.local/share/fonts/carrusel/JetBrainsMono.ttf")
TTF_SYNE = os.path.expanduser("~/.local/share/fonts/carrusel/Syne.ttf")
TTF_ANTON = os.path.expanduser("~/.local/share/fonts/carrusel/Anton-Regular.ttf")

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(archivo: bool, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = ("a" if archivo else ("b" if bold else "r"), size)
    if key not in _font_cache:
        path = TTF_ARCHIVO if archivo else (TTF_ARIAL_BD if bold else TTF_ARIAL)
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


_ROL_TTF = {
    "titulo": TTF_OSWALD,   # Oswald para títulos (Opción C) — impacto cartel
    "cuerpo": TTF_SPACE,    # Space Grotesk para cuerpo — dinámico
    "chip": TTF_JET,        # JetBrains Mono para chips — contraste técnico
    "kicker": TTF_OSWALD,
    "display": TTF_ANTON,
}


def font_rol(rol: str, size: int) -> ImageFont.FreeTypeFont:
    key = (rol, size)
    if key not in _font_cache:
        path = _ROL_TTF.get(rol, TTF_SPACE)
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def ancho(texto: str, f: ImageFont.FreeTypeFont, spacing: float = 0) -> float:
    return f.getlength(texto) + spacing * max(len(texto) - 1, 0)


def wrap_px(texto: str, f: ImageFont.FreeTypeFont, max_w: float,
            spacing: float = 0) -> list[str]:
    lineas: list[str] = []
    for parrafo in texto.split("\n"):
        palabras = parrafo.split()
        if not palabras:
            lineas.append("")
            continue
        actual = palabras[0]
        for p in palabras[1:]:
            if ancho(actual + " " + p, f, spacing) <= max_w:
                actual += " " + p
            else:
                lineas.append(actual)
                actual = p
        lineas.append(actual)
    return lineas


FUENTES = os.path.join(ROOT, "carrousel/fuentes")


def _data_uri(ruta: str) -> str:
    ext = os.path.splitext(ruta)[1].lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    data = open(ruta, "rb").read()
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


# ── Logos embebidos (paths autocontenidos) ─────────────────────────
_logo_svg = open(os.path.join(ROOT, "web/public/logo-frontera-grande.svg"),
                 encoding="utf-8").read()
LOGO_INNER = _logo_svg.split("<svg", 1)[1].rsplit("</svg>", 1)[0].split(">", 1)[1]
_icon_svg = open(os.path.join(ROOT, "web/app/icon.svg"), encoding="utf-8").read()
LOGO_FG_INNER = _icon_svg.split("<svg", 1)[1].rsplit("</svg>", 1)[0].split(">", 1)[1]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


class Slide:
    """Lienzo con cursor vertical y registro de cajas para anti-solape."""

    def __init__(self, W: int, H: int, fondo: str):
        self.W, self.H = W, H
        self.parts: list[str] = []
        self.boxes: list[tuple[float, float, float, float, str]] = []
        grad = (
            f'<defs><linearGradient id="hero" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0%" stop-color="{ACCENT_SOFT}"/>'
            f'<stop offset="100%" stop-color="{SURFACE}"/>'
            f'</linearGradient></defs>'
        )
        fill = {"hero": "url(#hero)", "bg": BG, "surface": SURFACE}[fondo]
        self.parts.append(
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">{grad}'
            f'<rect width="{W}" height="{H}" fill="{fill}"/>'
        )

    def fondo_imagen(self, nombre: str, opacity: float = 0.32, velo: float = 0.58):
        """Imagen de fondo a pantalla completa con overlay oscuro."""
        ruta = os.path.join(FUENTES, nombre)
        if not os.path.exists(ruta):
            return
        uri = _data_uri(ruta)
        self.parts.append(
            f'<image href="{uri}" x="0" y="0" width="{self.W}" height="{self.H}" '
            f'preserveAspectRatio="xMidYMid slice" opacity="{opacity}"/>'
        )
        self.parts.append(
            f'<rect width="{self.W}" height="{self.H}" fill="{BG}" opacity="{velo}"/>'
        )

    # ── primitivas ────────────────────────────────────────────────
    def caja(self, x, y, w, h, etiqueta):
        self.boxes.append((x, y, w, h, etiqueta))

    def texto(self, x, y_baseline, linea, size, *, archivo=False, bold=False,
              color=TEXT, spacing=0, anchor="start", etiqueta="", registrar=True,
              rol: str | None = None):
        if rol:
            f = font_rol(rol, size)
            fam = {"titulo": "Oswald", "cuerpo": "Space Grotesk", "chip": "JetBrains Mono", "kicker": "Oswald", "display": "Anton"}[rol]
        else:
            f = font(archivo, size, bold)
            fam = "Archivo Black" if archivo else "Arial"
        w = ancho(linea, f, spacing)
        x_emit = x
        x_box = x
        if anchor == "middle":
            x_box = x - w / 2
        elif anchor == "end":
            x_box = x - w
        attrs = (f'font-family="{fam}, Helvetica, sans-serif" font-size="{size}" fill="{color}"')
        if rol == "titulo" or archivo or bold:
            attrs += ' font-weight="900"' if (rol == "titulo" or archivo) else ' font-weight="700"'
        if spacing:
            attrs += f' letter-spacing="{spacing}"'
        if anchor != "start":
            attrs += f' text-anchor="{anchor}"'
        # sombra suave vía duplicado (más compatible que filter de Inkscape)
        necesita_sombra = color != BG and (rol in ("titulo", "cuerpo", "kicker") or archivo) and size >= 28
        if necesita_sombra:
            # duplicado negro desplazado 0,2 con opacidad para suavizar contraste
            attrs_sombra = attrs.replace(f'fill="{color}"', 'fill="#000"')
            if 'fill="#000"' not in attrs_sombra:
                attrs_sombra += ' fill="#000"'
            attrs_sombra += ' opacity="0.42"'
            self.parts.append(f'<text x="{x_emit:.1f}" y="{y_baseline + 2:.1f}" {attrs_sombra}>{esc(linea)}</text>')
        self.parts.append(f'<text x="{x_emit:.1f}" y="{y_baseline:.1f}" {attrs}>{esc(linea)}</text>')
        if registrar and etiqueta:
            alto = size * 1.05
            self.caja(x_box, y_baseline - alto * 0.78, w, alto, etiqueta)
        return w

    def resaltar(self, x, y, w, h, rx=8, color=ACCENT):
        self.parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{color}" opacity="0.95"/>')

    def bloque(self, x, y, texto, size, max_w, *, archivo=False, bold=False,
               color=TEXT, spacing=0, line_h=1.32, anchor="start", etiqueta="",
               rol: str | None = None):
        """Texto multilínea envuelto por píxeles. Devuelve altura total."""
        f = font_rol(rol, size) if rol else font(archivo, size, bold)
        lineas = wrap_px(texto, f, max_w, spacing)
        alto_linea = size * line_h
        ancho_max = max(ancho(ln, f, spacing) for ln in lineas) if lineas else 0
        for i, ln in enumerate(lineas):
            self.texto(x, y + alto_linea * 0.78 + i * alto_linea, ln, size,
                       archivo=archivo, bold=bold, color=color, spacing=spacing,
                       anchor=anchor, etiqueta="", rol=rol)
        if etiqueta and lineas:
            x_box = x - ancho_max / 2 if anchor == "middle" else (
                x - ancho_max if anchor == "end" else x)
            self.caja(x_box, y, ancho_max, alto_linea * len(lineas), etiqueta)
        return len(lineas) * alto_linea

    def linea_h(self, x1, y, x2, color=LINE, width=2):
        self.parts.append(
            f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
            f'stroke="{color}" stroke-width="{width}"/>')

    def linea_v_path(self, cx, y, w, color=ACCENT, width=10):
        """La línea morada del logo (valle central), escalada a w y centrada."""
        s = w / 340.0
        path_w = 256 * s  # 104 + 48 + 104
        x0 = cx - path_w / 2
        d = (f"M{x0:.1f} {y}h{104*s:.1f}"
             f"c{11*s:.1f} 0 {14*s:.1f} {-8*s:.1f} {24*s:.1f} {-8*s:.1f}"
             f"s{13*s:.1f} {8*s:.1f} {24*s:.1f} {8*s:.1f}h{104*s:.1f}")
        self.parts.append(
            f'<path d="{d}" fill="none" stroke="{color}" '
            f'stroke-linecap="round" stroke-width="{width}"/>')

    def logo(self, cx, y, size):
        self.parts.append(
            f'<svg x="{cx - size/2:.1f}" y="{y}" width="{size}" height="{size}" '
            f'viewBox="18 18 476 476">{LOGO_INNER}</svg>')

    def logo_fg(self, cx, y, size):
        self.parts.append(
            f'<svg x="{cx - size/2:.1f}" y="{y}" width="{size}" height="{size}" '
            f'viewBox="0 0 512 512">{LOGO_FG_INNER}</svg>')

    def fantasma(self, digitos, size, x, y_baseline, color):
        """Número decorativo de fondo (exento del anti-solape)."""
        f = font(True, size)
        w = ancho(digitos, f)
        self.parts.append(
            f'<text x="{x}" y="{y_baseline}" font-family="Archivo Black, '
            f'Arial, sans-serif" font-weight="900" font-size="{size}" '
            f'fill="{color}">{esc(digitos)}</text>')
        return w

    def chip(self, x, y, txt, *, relleno=False, size=30, bold=True):
        """Chip rounded-full estilo web: bg-accent-soft/text-accent o borde."""
        f = font_rol("chip", size)
        pad_x, alto = size * 0.95, size * 2.1
        w = ancho(txt.upper(), f) + pad_x * 2
        if relleno:
            self.parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{alto}" '
                f'rx="{alto/2:.1f}" fill="{ACCENT_SOFT}"/>')
            color = ACCENT
        else:
            self.parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{alto}" '
                f'rx="{alto/2:.1f}" fill="none" stroke="{LINE}" stroke-width="2"/>')
            color = MUTED
        self.texto(x + pad_x, y + alto * 0.68, txt.upper(), size, bold=bold,
                   color=color, spacing=2, etiqueta=f"chip:{txt}", rol="chip")
        return w, alto

    def pill(self, cx, y, txt, *, outline=False, size=32):
        f = font_rol("cuerpo", size)
        pad_x, alto = size * 1.3, size * 2.5
        w = ancho(txt.upper(), f, 2) + pad_x * 2
        x = cx - w / 2
        if outline:
            self.parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{alto}" '
                f'rx="{alto/2:.1f}" fill="none" stroke="{ACCENT}" stroke-width="3"/>')
            color = ACCENT
        else:
            self.parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{alto}" '
                f'rx="{alto/2:.1f}" fill="{ACCENT}"/>')
            color = BG
        self.texto(cx, y + alto * 0.66, txt.upper(), size, bold=True, color=color,
                   spacing=2, anchor="middle", etiqueta=f"pill:{txt}", rol="cuerpo")
        return alto

    flecha_y = None

    def desliza(self, cy):
        """'Desliza' + flecha dibujada (sin depender de glifos)."""
        size = 28
        f = font(False, size, True)
        w_txt = ancho("Desliza", f, 1)
        total = w_txt + 56
        x0 = (self.W - total) / 2
        self.parts.append(f'<g opacity="0.9">')
        self.texto(x0, cy, "Desliza", size, bold=True, color=MUTED, spacing=1,
                   etiqueta="desliza")
        ax = x0 + w_txt + 16
        ay = cy - size * 0.32
        self.parts.append(
            f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{ax+34:.1f}" y2="{ay:.1f}" '
            f'stroke="{ACCENT}" stroke-width="4" stroke-linecap="round"/>'
            f'<polyline points="{ax+22:.1f},{ay-9:.1f} {ax+34:.1f},{ay:.1f} '
            f'{ax+22:.1f},{ay+9:.1f}" fill="none" stroke="{ACCENT}" '
            f'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
        self.parts.append('</g>')

    def footer(self, txt, y=None, dominio_grande=False):
        if y is None:
            y = self.H - 64
        if dominio_grande:
            size = 52
            self.linea_h(84, y - 74, self.W - 84)
            self.texto(self.W / 2, y, txt, size, archivo=True, color=TEXT,
                       anchor="middle", etiqueta="footer")
        else:
            size = 24
            self.linea_h(84, y - 40, self.W - 84)
            self.texto(84, y, txt.upper(), size, bold=True, color=MUTED,
                       spacing=3, etiqueta="footer")

    def verificar(self):
        """Assert de no-solape entre elementos registrados."""
        for i in range(len(self.boxes)):
            for j in range(i + 1, len(self.boxes)):
                ax, ay, aw, ah, an = self.boxes[i]
                bx, by, bw, bh, bn = self.boxes[j]
                if (ax < bx + bw and bx < ax + aw and
                        ay < by + bh and by < ay + ah):
                    raise AssertionError(
                        f"SOLAPE: '{an}' vs '{bn}' en {self.W}x{self.H}")

    def guardar(self, ruta):
        self.verificar()
        self.parts.append("</svg>")
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write("\n".join(self.parts))
        ET.parse(ruta)  # XML válido
        return ruta


# ═════════════════════════════ SLIDES ════════════════════════════════

def s_portada(W, H, reel):
    s = Slide(W, H, "hero")
    s.fondo_imagen("01-portada-bg.jpg", opacity=0.38)
    top = 300 if reel else 96
    bot = 1500 if reel else H - 60
    s.fantasma_num = None
    # número discreto
    s.texto(W - 84, top + 30, "01", 26, bold=True, color=MUTED, spacing=2,
            anchor="end", etiqueta="num")
    # composición centrada tipo cover — solo FG
    logo_sz = 230 if not reel else 250
    s.logo_fg(W / 2, top + 70, logo_sz)
    y = top + 70 + logo_sz + (110 if reel else 52)
    fs_titulo = 176 if reel else 148
    f_tit = font(True, fs_titulo)
    titulo_top = y
    for ln in ("FRONTERA", "GRANDE"):
        s.texto(W / 2, y + fs_titulo * 0.82, ln, fs_titulo, archivo=True,
                color=TEXT, anchor="middle", etiqueta="")
        y += fs_titulo * 0.96
    w_tit = max(ancho(ln, f_tit) for ln in ("FRONTERA", "GRANDE"))
    s.caja((W - w_tit) / 2, titulo_top, w_tit, y - titulo_top, "titulo")
    s.linea_v_path(W / 2, y + 22, 420, width=13)
    y += 22 + 13
    gancho_fs = 50 if reel else 44
    y += ((84 if reel else 42) + gancho_fs)
    # gancho con énfasis en color (tu frontera / tu mapa en acento)
    f_gancho = font_rol("cuerpo", gancho_fs)
    lh = gancho_fs * 1.25
    # línea 1: "La escena de tu frontera,"
    l1 = "La escena de tu frontera,"
    pref1 = "La escena de "
    hl1 = "tu frontera,"
    w_l1 = ancho(l1, f_gancho)
    w_pref1 = ancho(pref1, f_gancho)
    x1 = W / 2 - w_l1 / 2
    y1 = y + lh * 0.78
    s.texto(x1, y1, pref1, gancho_fs, rol="cuerpo", color=TEXT, etiqueta="")
    s.texto(x1 + w_pref1, y1, hl1, gancho_fs, rol="cuerpo", color=ACCENT, etiqueta="")
    # línea 2: "por fin en tu mapa."
    l2 = "por fin en tu mapa."
    pref2 = "por fin en "
    hl2 = "tu mapa."
    w_l2 = ancho(l2, f_gancho)
    w_pref2 = ancho(pref2, f_gancho)
    x2 = W / 2 - w_l2 / 2
    y2 = y + lh * 0.78 + lh
    s.texto(x2, y2, pref2, gancho_fs, rol="cuerpo", color=TEXT, etiqueta="")
    s.texto(x2 + w_pref2, y2, hl2, gancho_fs, rol="cuerpo", color=ACCENT, etiqueta="")
    # caja combinada para verificar
    max_w = max(w_l1, w_l2)
    s.caja(W / 2 - max_w / 2, y, max_w, lh * 2, "gancho")
    s.desliza(bot if reel else bot - 10)
    return s


def s_quesomos(W, H, reel):
    s = Slide(W, H, "bg")
    s.fondo_imagen("02-mapa-bg.jpg", opacity=0.58, velo=0.38)
    top = 330 if reel else 110
    ghost_size = 760 if reel else 520
    s.fantasma("02", ghost_size, W - 40, H * (0.98 if reel else 0.99), SURFACE2)
    x = 84
    s.bloque(x, top, "QUÉ SOMOS", 28, 500, rol="kicker", color=ACCENT, spacing=6,
             etiqueta="kicker")
    y = top + 44 + (70 if reel else 36)
    fs = 124 if reel else 96
    # título con "vivo" en acento — renderizado sin doble capa para evitar encimado
    f_tit = font_rol("titulo", fs)
    lh_tit = fs * 1.15
    # línea 1: "El archivo " + "vivo"
    pref_tit = "El archivo "
    hl_tit = "vivo"
    s.texto(x, y + lh_tit * 0.78, pref_tit, fs, rol="titulo", color=TEXT, etiqueta="")
    s.texto(x + ancho(pref_tit, f_tit) + 40, y + lh_tit * 0.78, hl_tit, fs, rol="titulo", color=ACCENT, etiqueta="")
    # línea 2: "de la escena"
    s.texto(x, y + lh_tit * 0.78 + lh_tit, "de la escena", fs, rol="titulo", color=TEXT, etiqueta="")
    max_w_tit = max(ancho("El archivo vivo", f_tit), ancho("de la escena", f_tit))
    s.caja(x, y, max_w_tit, lh_tit * 2, "titulo")
    y += lh_tit * 2
    y += (86 if reel else 50)
    fs_lead = 46 if reel else 40
    y += s.bloque(x, y, "La base de datos abierta de la escena musical "
                        "de la frontera grande de Tamaulipas.",
                  fs_lead, 760, color=TEXT, line_h=1.28, etiqueta="lead", rol="cuerpo")
    y += (56 if reel else 42)
    y += s.bloque(x, y, "Música: bandas, solistas, DJs, colectivos, "
                        "covers y tributos.", 32, 720, color=TEXT, line_h=1.35, etiqueta="body1", rol="cuerpo")
    y += (28 if reel else 22)
    y += s.bloque(x, y, "Directorio, feed y perfiles.", 32, 720, color=MUTED,
                  line_h=1.35, etiqueta="body2a", rol="cuerpo")
    # "próximamente agregaremos más disciplinas" en acento suave
    y_hl2 = y
    hl2_txt = "Próximamente agregaremos más disciplinas."
    w_hl2 = ancho(hl2_txt, font_rol("cuerpo", 32))
    s.resaltar(x - 6, y_hl2 - 2, w_hl2 + 12, 32 * 1.35 * 0.92, rx=8, color=ACCENT_SOFT)
    y += s.bloque(x, y, hl2_txt, 32, 720, color=ACCENT, line_h=1.35, etiqueta="body2-hl", rol="cuerpo")
    s.footer("Sin números inventados  |  Datos con fuente",
             y=(1532 if reel else None))
    return s


def _lista_con_puntos(s, x, W, y, items, etiqueta):
    size, lh, dot_r = 38, 54, 10
    max_w = W - x - 140
    for k, it in enumerate(items):
        lineas = wrap_px(it, font_rol("cuerpo", size), max_w)
        for j, ln in enumerate(lineas):
            base = y + size * 0.8 + j * lh
            # solo círculo en la PRIMERA línea de cada item
            if j == 0:
                s.parts.append(
                    f'<circle cx="{x + 10}" cy="{base - size*0.32:.1f}" '
                    f'r="{dot_r}" fill="{ACCENT}"/>')
            # primer palabra en acento para impacto rápido (solo primera línea)
            if j == 0 and " " in ln:
                first, rest = ln.split(" ", 1)
                w_first = ancho(first + " ", font_rol("cuerpo", size))
                s.texto(x + 34, base, first + " ", size, color=ACCENT,
                        rol="cuerpo", etiqueta=f"{etiqueta}{k}.{j}-hl")
                s.texto(x + 34 + w_first, base, rest, size, color=TEXT,
                        rol="cuerpo", etiqueta=f"{etiqueta}{k}.{j}")
            else:
                s.texto(x + 34, base, ln, size, color=TEXT,
                        rol="cuerpo", etiqueta=f"{etiqueta}{k}.{j}")
        y += lh * len(lineas) + 14
    return y


def s_fan(W, H, reel):
    s = Slide(W, H, "bg")
    s.fondo_imagen("03a-fan.jpg", opacity=0.35, velo=0.50)
    top = 330 if reel else 100
    ghost_size = 760 if reel else 520
    s.fantasma("03", ghost_size, W - 40, H * (0.98 if reel else 0.99), SURFACE2)
    x = 84
    s.bloque(x, top, "PARA TI", 28, 400, rol="kicker", color=ACCENT, spacing=6,
             etiqueta="kicker")
    # centrado vertical: más aire arriba para aprovechar espacio
    gap = (110 if reel else 72)
    y = top + 140 if not reel else top + 110
    _, ch = s.chip(x, y, "Si eres FAN", size=36)
    y += ch + gap
    y = _lista_con_puntos(s, x, W, y, [
        "Descubre música y artistas de la frontera",
        "Filtra por género y quién está activo",
        "Recibe avisos de tus favoritos",
        "Todo el contenido de cada artista en un sitio",
        "Escucha la playlist semanal",
    ], "fan.")
    s.footer("Explora sin registro",
             y=(1470 if reel else None))
    return s


def s_artista(W, H, reel):
    s = Slide(W, H, "bg")
    s.fondo_imagen("03b-artista.jpg", opacity=0.30)
    top = 330 if reel else 100
    ghost_size = 760 if reel else 520
    s.fantasma("04", ghost_size, W - 40, H * (0.98 if reel else 0.99), SURFACE2)
    x = 84
    s.bloque(x, top, "PARA TI", 28, 400, rol="kicker", color=ACCENT, spacing=6,
             etiqueta="kicker")
    gap = (110 if reel else 72)
    y = top + 140 if not reel else top + 110
    _, ch = s.chip(x, y, "Si eres ARTISTA", size=36)
    y += ch + gap
    y = _lista_con_puntos(s, x, W, y, [
        "Suma tu proyecto y entra a la playlist Descubrimiento Semanal",
        "Publicas en tus redes → aparece aquí y notifica a tus fans en redes",
        "Perfil verificado gratis: badge + enlaces directos a tu música",
        "Puente directo: tus fans van a tus redes sin algoritmo",
    ], "artista.")
    s.footer("Verificado con tu página  •  Gratis, sin comisiones",
             y=(1470 if reel else None))
    return s


def s_fan_artista(W, H, reel):
    # compatibilidad — no usado en build actual
    return s_fan(W, H, reel)


def s_mockup(W, H, reel):
    s = Slide(W, H, "surface")
    top = 320 if reel else 100
    x = 84
    s.bloque(x, top, "PRUEBA REAL", 26, 500, bold=True, color=MUTED,
             spacing=6, etiqueta="kicker")
    y = top + 44 + (70 if reel else 40)
    fs = 100 if reel else 88
    y += s.bloque(x, y, "La plataforma,\npor dentro", fs, 700, archivo=True,
                  line_h=1.04, etiqueta="titulo")

    # teléfono centrado
    tel_w = 470 if not reel else 520
    tel_h = 560 if not reel else 800
    tel_x = (W - tel_w) / 2
    tel_y = y + (120 if reel else 76)
    s.caja(tel_x, tel_y, tel_w, tel_h, "telefono.marco") if False else None
    s.parts.append(
        f'<rect x="{tel_x:.1f}" y="{tel_y:.1f}" width="{tel_w}" height="{tel_h}" '
        f'rx="56" fill="{SURFACE}" stroke="{LINE}" stroke-width="4"/>'
        f'<rect x="{tel_x+14:.1f}" y="{tel_y+14:.1f}" width="{tel_w-28}" '
        f'height="{tel_h-28}" rx="44" fill="{BG}"/>')
    ix, iy = tel_x + 38, tel_y + 38
    iw = tel_w - 76
    # barra superior: logo mini + buscador
    s.logo(ix + 18, iy + 6, 36)
    s.parts.append(
        f'<rect x="{ix+70:.1f}" y="{iy+8:.1f}" width="{iw-70:.1f}" height="32" '
        f'rx="10" fill="{SURFACE2}" stroke="{LINE}" stroke-width="2"/>')
    # cuadrícula de tarjetas 2x2 (aspect 4:5 como ArtistCard)
    card_gap = 18
    card_w = (iw - card_gap) / 2
    card_h = card_w * 1.25
    iniciales = [("R", "Raíces del Valle"), ("K", "Kaos Norte"),
                 ("Dj", "La Doña"), ("V", "Vértigo")]
    gy = iy + 62
    for idx, (ini, nombre) in enumerate(iniciales):
        col, row = idx % 2, idx // 2
        cx0 = ix + col * (card_w + card_gap)
        cy0 = gy + row * (card_h + card_gap)
        s.parts.append(
            f'<rect x="{cx0:.1f}" y="{cy0:.1f}" width="{card_w:.1f}" '
            f'height="{card_h:.1f}" rx="18" fill="{SURFACE}" '
            f'stroke="{LINE}" stroke-width="2"/>'
            f'<defs><linearGradient id="c{idx}{reel}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0%" stop-color="{ACCENT_SOFT}"/>'
            f'<stop offset="100%" stop-color="{SURFACE2}"/>'
            f'</linearGradient></defs>'
            f'<path d="M{cx0:.1f} {cy0+card_h*0.62:.1f}v{-card_h*0.62+18:.1f}'
            f'q0 -18 18 -18h{card_w-36:.1f}q18 0 18 18v{card_h*0.62-18:.1f}z" '
            f'fill="url(#c{idx}{reel})"/>')
        f_ini = font(True, int(card_w * 0.30))
        s.parts.append(
            f'<text x="{cx0 + card_w/2:.1f}" y="{cy0 + card_h*0.40:.1f}" '
            f'font-family="Archivo Black, Arial, sans-serif" font-weight="900" '
            f'font-size="{int(card_w*0.30)}" fill="{ACCENT}" '
            f'text-anchor="middle">{esc(ini)}</text>')
        s.texto(cx0 + 12, cy0 + card_h * 0.62 + 30, nombre[:16], 17,
                bold=True, color=TEXT, etiqueta="")
        chip_w = min(ancho("género", font(False, 12)) + 16, card_w - 24)
        s.parts.append(
            f'<rect x="{cx0+12:.1f}" y="{cy0+card_h-30:.1f}" '
            f'width="{chip_w:.1f}" height="17" rx="8.5" fill="{ACCENT_SOFT}"/>')
    # barra inferior de navegación
    nav_y = tel_y + tel_h - 38 - 46
    s.parts.append(
        f'<rect x="{ix:.1f}" y="{nav_y:.1f}" width="{iw:.1f}" height="46" '
        f'rx="14" fill="{SURFACE2}" stroke="{LINE}" stroke-width="2"/>')
    for k in range(4):
        dot_cx = ix + iw * (k + 0.5) / 4
        color = ACCENT if k == 0 else LINE
        r = 7 if k == 0 else 6
        s.parts.append(f'<circle cx="{dot_cx:.1f}" cy="{nav_y+23}" r="{r}" '
                       f'fill="{color}"/>')
    # leyenda bajo el teléfono
    ly = tel_y + tel_h + (66 if reel else 56)
    s.bloque(W / 2, ly, "Directorio, perfiles y feed en vivo desde las redes "
             "de cada artista.", 30, W - 260, color=MUTED, anchor="middle",
             etiqueta="leyenda")
    s.footer("fronteragrande.mx", y=(1478 if reel else None))
    return s


def s_links(W, H, reel):
    s = Slide(W, H, "hero")
    s.fondo_imagen("05-link.jpg", opacity=0.32)
    top = 300 if reel else 120
    s.texto(W - 84, top + 30, "05", 26, bold=True, color=MUTED, spacing=2,
            anchor="end", etiqueta="num")
    x = 84
    s.bloque(x, top, "EMPIEZA HOY", 28, 500, rol="kicker", color=MUTED,
             spacing=6, etiqueta="kicker")
    y = top + 44 + (70 if reel else 40)
    fs = 138 if reel else 124
    # título con "bio" resaltado en marcatextos
    f_tit = font_rol("titulo", fs)
    pref_tit = "Link en  "
    hl_tit = "bio"
    w_pref_tit = ancho(pref_tit, f_tit)
    w_hl_tit = ancho(hl_tit, f_tit)
    w_tit = w_pref_tit + w_hl_tit
    s.resaltar(x + w_pref_tit - 6, y - 4, w_hl_tit + 12, fs * 1.0 * 0.92, color=ACCENT)
    s.texto(x, y + fs * 0.78, pref_tit, fs, rol="titulo", color=TEXT, etiqueta="")
    s.texto(x + w_pref_tit, y + fs * 0.78, hl_tit, fs, rol="titulo", color=BG, etiqueta="")
    s.caja(x, y, w_tit, fs * 1.0, "titulo")
    y += fs * 1.0
    y += (100 if reel else 64)
    y += s.bloque(x, y, "Explora la escena y descubre a quienes suenan aquí.",
                  42, 760, color=TEXT, rol="cuerpo", etiqueta="lead")
    y += (32 if reel else 20)
    # lead2: texto que quepa en una línea con resaltes inline
    f26 = font_rol("cuerpo", 26)
    f = f26
    y_base = y + 26 * 0.78
    # "Activa "
    w_act = ancho("Activa ", f)
    s.texto(x, y_base, "Activa ", 26, rol="cuerpo", color=TEXT, etiqueta="")
    # "notificaciones" con resaltado ACCENT_SOFT
    w_not = ancho("notificaciones", f)
    s.resaltar(x + w_act - 6, y_base - 23, w_not + 8, 26 * 1.2, color=ACCENT_SOFT)
    s.texto(x + w_act, y_base, "notificaciones", 26, rol="cuerpo", color=ACCENT, etiqueta="")
    # " y sigue la playlist "
    w_mid = ancho(" y sigue la playlist ", f)
    s.texto(x + w_act + w_not, y_base, " y sigue la playlist ", 26, rol="cuerpo", color=TEXT, etiqueta="")
    # "Descubrimiento Semanal" con resaltado ACCENT
    w_ds = ancho("Descubrimiento Semanal", f)
    x_ds = x + w_act + w_not + w_mid
    s.resaltar(x_ds - 6, y_base - 23, w_ds + 8, 26 * 1.2, color=ACCENT)
    s.texto(x_ds, y_base, "Descubrimiento Semanal", 26, rol="cuerpo", color=BG, etiqueta="")
    # " Spotify"
    s.texto(x_ds + w_ds, y_base, " Spotify", 26, rol="cuerpo", color=MUTED, etiqueta="")
    # caja para verificar
    s.caja(x, y, ancho("Activa notificaciones y sigue la playlist Descubrimiento Semanal Spotify", f), 26 * 1.3, "lead2")
    y += 26 * 1.3
    y += (48 if reel else 28)
    y += s.pill(W / 2, y, "Explora la plataforma") + (40 if reel else 28)
    y += s.pill(W / 2, y, "Suma tu proyecto", outline=True) + (40 if reel else 28)
    y += s.bloque(W / 2, y, "¿Eres artista? Regístrate y verifica tu perfil "
                  "conectando tu página.", 26, W - 280, color=MUTED,
                  anchor="middle", etiqueta="cta-artista", rol="cuerpo")
    s.footer("fronteragrande.mx", y=(1480 if reel else None),
             dominio_grande=True)
    return s


# ═════════════════════════════ BUILD ═════════════════════════════════

for viejo in glob.glob(os.path.join(OUT, "*.svg")) + \
        glob.glob(os.path.join(OUT, "*.png")):
    os.remove(viejo)

FORMATOS = {
    "post": (1080, 1440),
    "reel": (1080, 1920),
}
BUILDERS = [s_portada, s_quesomos, s_fan, s_artista, s_links]
NOMBRES = ["01-portada", "02-quesomos", "03-fan", "04-artista",
           "05-links"]

generados = []
for sufijo, (W, H) in FORMATOS.items():
    for builder, nombre in zip(BUILDERS, NOMBRES):
        slide = builder(W, H, reel=(sufijo == "reel"))
        svg = slide.guardar(os.path.join(OUT, f"{nombre}-{sufijo}.svg"))
        generados.append(svg)

for svg in generados:
    png = svg[:-4] + ".png"
    r = subprocess.run(
        ["inkscape", svg, "--export-type=png",
         f"--export-filename={png}", "--export-dpi=96"],
        capture_output=True, text=True)
    if not os.path.exists(png):
        raise SystemExit(f"Inkscape falló con {svg}:\n{r.stderr}")

print(f"OK: {len(generados)} SVG + PNG en {OUT}")
