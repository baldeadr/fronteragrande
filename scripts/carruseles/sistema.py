"""Motor de generación de carruseles (SVG → PNG) compartido por todos.

Extraído de `generar_carrousel_v2.py` sin cambios funcionales: paleta real
de la web, fuentes TTF medidas con PIL, clase `Slide` con verificador
anti-solape y render final vía Inkscape.
"""
import base64
import html
import os
import subprocess
import xml.etree.ElementTree as ET

from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "carrousel")

# ── Paleta real (web/app/globals.css) ────────────────────────────────
BG = "#0b0b10"
SURFACE = "#14141b"
SURFACE2 = "#1b1b24"
LINE = "#262633"
TEXT = "#ececf1"
MUTED = "#8a8a9a"
ACCENT = "#9d4edd"
ACCENT_SOFT = "#2a1a33"

# Sombra de texto (sin filtros SVG): duplicado desplazado
SOMBRA_COLOR = "#000000"
SOMBRA_OPACIDAD = "0.45"

# ── Fuentes ──────────────────────────────────────────────────────────
TTF_DIR = os.path.expanduser("~/.local/share/fonts/carrusel")
TTF_ARCHIVO = os.path.expanduser("~/.local/share/fonts/ArchivoBlack-Regular.ttf")
TTF_ARIAL = "/usr/share/fonts/msttcore/arial.ttf"
TTF_ARIAL_BD = "/usr/share/fonts/msttcore/arialbd.ttf"

FONT_MAP = {
    "archivo": TTF_ARCHIVO,
    "arial": TTF_ARIAL,
    "arial_bd": TTF_ARIAL_BD,
    "oswald": os.path.join(TTF_DIR, "Oswald.ttf"),
    "space": os.path.join(TTF_DIR, "SpaceGrotesk.ttf"),
    "jet": os.path.join(TTF_DIR, "JetBrainsMono.ttf"),
    "anton": os.path.join(TTF_DIR, "Anton-Regular.ttf"),
    "syne": os.path.join(TTF_DIR, "Syne.ttf"),
    "inter": os.path.join(TTF_DIR, "Inter.ttf"),
}

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

def font_rol(rol: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    """Fuente con la misma instancia de peso que renderizará Inkscape
    (las TTF son variables: sin esto se mide Regular y se renderiza Bold)."""
    if weight is None:
        weight = 900 if rol in ("archivo", "oswald") else 400
    key = (rol, size, weight)
    if key not in _font_cache:
        path = FONT_MAP.get(rol, FONT_MAP["space"])
        f = ImageFont.truetype(path, size)
        try:
            f.set_variation_by_axes([weight])
        except (OSError, ValueError):
            pass
        _font_cache[key] = f
    return _font_cache[key]

def ancho(texto: str, f: ImageFont.FreeTypeFont, spacing: float = 0) -> float:
    return f.getlength(texto) + spacing * max(len(texto) - 1, 0)

def wrap_px(texto: str, f: ImageFont.FreeTypeFont, max_w: float, spacing: float = 0) -> list[str]:
    lineas = []
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

# ── Logos embebidos ──────────────────────────────────────────────────
_logo_svg = open(os.path.join(ROOT, "web/public/logo-frontera-grande.svg"), encoding="utf-8").read()
LOGO_INNER = _logo_svg.split("<svg", 1)[1].rsplit("</svg>", 1)[0].split(">", 1)[1]
_icon_svg = open(os.path.join(ROOT, "web/app/icon.svg"), encoding="utf-8").read()
LOGO_FG_INNER = _icon_svg.split("<svg", 1)[1].rsplit("</svg>", 1)[0].split(">", 1)[1]

FUENTES_DIR = os.path.join(ROOT, "carrousel/fuentes")

FORMATOS = {
    "post": (1080, 1440),
    "reel": (1080, 1920),
}

def data_uri(ruta: str) -> str:
    ext = os.path.splitext(ruta)[1].lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    data = open(ruta, "rb").read()
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"

def esc(s: str) -> str:
    return html.escape(s, quote=True)

def centrar(total: float, zona_top: float, zona_bot: float) -> float:
    """Y superior para centrar un bloque de `total` px en la zona vertical."""
    return zona_top + (zona_bot - zona_top - total) / 2

def ajustar_fs(lineas: list[list[tuple[str, str]]], fs: int, rol: str,
               max_w: float) -> int:
    """Mayor tamaño ≤ fs cuya línea más ancha cabe en max_w.

    Garantiza márgenes laterales uniformes sin recortar copy a mano.
    """
    cache: dict[int, ImageFont.FreeTypeFont] = {}

    def ancho_linea(frags: list[tuple[str, str]], size: int) -> float:
        f = cache.setdefault(size, font_rol(rol, size, 700))
        return sum(ancho(t, f) for t, _ in frags)

    while fs > 24 and max(ancho_linea(frags, fs) for frags in lineas) > max_w:
        fs -= 2
    return fs


class Slide:
    def __init__(self, W: int, H: int, fondo: str = "bg"):
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

    def fondo_imagen(self, nombre: str, opacity: float = 0.35, velo: float = 0.45):
        ruta = os.path.join(FUENTES_DIR, nombre)
        if not os.path.exists(ruta):
            return
        uri = data_uri(ruta)
        self.parts.append(
            f'<image href="{uri}" x="0" y="0" width="{self.W}" height="{self.H}" '
            f'preserveAspectRatio="xMidYMid slice" opacity="{opacity}"/>'
        )
        self.parts.append(
            f'<rect width="{self.W}" height="{self.H}" fill="{BG}" opacity="{velo}"/>'
        )

    def caja(self, x, y, w, h, etiqueta):
        self.boxes.append((x, y, w, h, etiqueta))

    def forma(self, fragmento: str):
        """Fuga de escape para SVG crudo (paths, círculos, clips...)."""
        self.parts.append(fragmento)

    def circulo(self, cx, cy, r, *, fill="none", stroke=None, stroke_w=0, opacity=1):
        attrs = f'cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"'
        if stroke:
            attrs += f' stroke="{stroke}" stroke-width="{stroke_w}"'
        self.forma(f"<circle {attrs}/>")

    def rect(self, x, y, w, h, *, rx=0, fill=SURFACE, stroke=None, stroke_w=0, opacity=1):
        attrs = (f'x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'rx="{rx}" fill="{fill}" opacity="{opacity}"')
        if stroke:
            attrs += f' stroke="{stroke}" stroke-width="{stroke_w}"'
        self.forma(f"<rect {attrs}/>")

    def _halo(self, x, y_baseline, base, size, inner_plano):
        """Sombra centrada semi-blureada: 3 capas de stroke concéntricas
        (los filtros SVG se pierden en el PNG de Inkscape)."""
        k = float(SOMBRA_OPACIDAD) / 0.45
        for sw_mult, op in ((0.20, 0.07), (0.12, 0.10), (0.06, 0.14)):
            self.parts.append(
                f'<text x="{x:.1f}" y="{y_baseline:.1f}" {base} '
                f'fill="{SOMBRA_COLOR}" stroke="{SOMBRA_COLOR}" '
                f'stroke-width="{size * sw_mult:.1f}" stroke-linejoin="round" '
                f'opacity="{min(0.6, op * k):.3f}">{inner_plano}</text>')

    def texto(self, x, y_baseline, linea, size, *, archivo=False, bold=False,
              color=TEXT, spacing=0, anchor="start", etiqueta="", registrar=True,
              rol: str | None = None):
        if rol:
            peso = None if rol in ("archivo", "oswald") else (700 if bold else 400)
            f = font_rol(rol, size, peso)
            fam = {"archivo": "Archivo Black", "oswald": "Oswald", "space": "Space Grotesk",
                   "jet": "JetBrains Mono", "anton": "Anton", "syne": "Syne", "inter": "Inter"}[rol]
        else:
            f = font_rol("space" if not archivo else "archivo", size,
                         700 if (bold and not archivo) else None)
            fam = "Archivo Black" if archivo else "Space Grotesk"
        w = ancho(linea, f, spacing)
        x_emit = x
        x_box = x
        if anchor == "middle":
            x_box = x - w / 2
        elif anchor == "end":
            x_box = x - w
        base = f'font-family="{fam}, Helvetica, sans-serif" font-size="{size}"'
        if rol in ("archivo", "oswald") or archivo:
            base += ' font-weight="900"' if archivo else ' font-weight="700"'
        elif bold:
            base += ' font-weight="700"'
        if spacing:
            base += f' letter-spacing="{spacing}"'
        if anchor != "start":
            base += f' text-anchor="{anchor}"'
        plano = esc(linea)
        self._halo(x_emit, y_baseline, base, size, plano)
        self.parts.append(
            f'<text x="{x_emit:.1f}" y="{y_baseline:.1f}" {base} '
            f'fill="{color}">{plano}</text>')
        if registrar and etiqueta:
            alto = size * 1.05
            self.caja(x_box, y_baseline - alto * 0.78, w, alto, etiqueta)
        return w

    def resaltar(self, x, y, w, h, rx=8, color=ACCENT, opacity=0.95):
        self.rect(x, y, w, h, rx=rx, fill=color, opacity=opacity)

    def linea_compuesta(self, cx, y_baseline, frags, size, rol="oswald"):
        """Línea de fragmentos (texto, color): un solo <text> con <tspan>;
        el renderer SVG centra y fluye los avances exactos (sin encimar)."""
        fam = {"archivo": "Archivo Black", "oswald": "Oswald", "anton": "Anton",
               "space": "Space Grotesk",
               "jet": "JetBrains Mono"}[rol]
        base = (f'font-family="{fam}, Helvetica, sans-serif" font-size="{size}" '
                f'font-weight="700" text-anchor="middle" xml:space="preserve"')
        tspans = "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for t, c in frags)
        plano = esc("".join(t for t, _ in frags))
        self._halo(cx, y_baseline, base, size, plano)
        self.parts.append(
            f'<text x="{cx:.1f}" y="{y_baseline:.1f}" {base}>{tspans}</text>')

    def bloque(self, x, y, texto, size, max_w, *, color=TEXT, spacing=0,
               line_h=1.35, anchor="start", etiqueta="", rol: str | None = None):
        f = font_rol(rol, size) if rol else font_rol("space", size)
        lineas = wrap_px(texto, f, max_w, spacing)
        alto_linea = size * line_h
        ancho_max = max(ancho(ln, f, spacing) for ln in lineas) if lineas else 0
        for i, ln in enumerate(lineas):
            self.texto(x, y + alto_linea * 0.78 + i * alto_linea, ln, size,
                       color=color, spacing=spacing, anchor=anchor, etiqueta="", rol=rol)
        if etiqueta and lineas:
            x_box = x - ancho_max / 2 if anchor == "middle" else (
                x - ancho_max if anchor == "end" else x)
            self.caja(x_box, y, ancho_max, alto_linea * len(lineas), etiqueta)
        return len(lineas) * alto_linea

    def logo_fg(self, cx, y, size):
        self.parts.append(
            f'<svg x="{cx - size/2:.1f}" y="{y}" width="{size}" height="{size}" '
            f'viewBox="0 0 512 512">{LOGO_FG_INNER}</svg>'
        )

    def pill(self, cx, y, txt, *, outline=False, size=30):
        f = font_rol("space", size, 700)
        pad_x, alto = size * 1.2, size * 2.4
        w = ancho(txt.upper(), f, 2) + pad_x * 2
        x = cx - w / 2
        if outline:
            self.rect(x, y, w, alto, rx=alto/2, fill="none", stroke=ACCENT, stroke_w=3)
            color = ACCENT
        else:
            self.rect(x, y, w, alto, rx=alto/2, fill=ACCENT)
            color = BG
        self.texto(cx, y + alto * 0.66, txt.upper(), size, bold=True, color=color,
                   spacing=2, anchor="middle", etiqueta=f"pill:{txt}", rol="space")
        return alto

    def desliza(self, cy):
        size = 26
        f = font_rol("space", size, 700)
        w_txt = ancho("Desliza", f, 1)
        total = w_txt + 50
        x0 = (self.W - total) / 2
        self.forma('<g opacity="0.9">')
        self.texto(x0, cy, "Desliza", size, bold=True, color=MUTED, spacing=1,
                   etiqueta="desliza", rol="space")
        ax = x0 + w_txt + 16
        ay = cy - size * 0.32
        self.parts.append(
            f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{ax+34:.1f}" y2="{ay:.1f}" '
            f'stroke="{ACCENT}" stroke-width="4" stroke-linecap="round"/>'
            f'<polyline points="{ax+22:.1f},{ay-9:.1f} {ax+34:.1f},{ay:.1f} '
            f'{ax+22:.1f},{ay+9:.1f}" fill="none" stroke="{ACCENT}" '
            f'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
        self.forma('</g>')

    def footer(self, txt, y=None, dominio_grande=False):
        if y is None:
            y = self.H - 64
        if dominio_grande:
            size = 48
            self.parts.append(f'<line x1="84" y1="{y-74}" x2="{self.W-84}" y2="{y-74}" stroke="{LINE}" stroke-width="2"/>')
            self.texto(self.W / 2, y, txt, size, archivo=True, color=TEXT,
                       anchor="middle", etiqueta="footer")
        else:
            size = 22
            self.parts.append(f'<line x1="84" y1="{y-40}" x2="{self.W-84}" y2="{y-40}" stroke="{LINE}" stroke-width="2"/>')
            self.texto(84, y, txt.upper(), size, bold=True, color=MUTED,
                       spacing=3, etiqueta="footer", rol="space")

    def verificar(self):
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
        ET.parse(ruta)
        return ruta


# ═════════════════════════════ RENDER ════════════════════════════════

def render(slides: list[tuple[str, object]], carpeta: str,
           formatos: dict[str, tuple[int, int]] | None = None) -> list[str]:
    """Genera SVG + PNG de una lista de slides en carrousel/<carpeta>/.

    Limpia antes únicamente los archivos de los formatos solicitados.
    """
    out_dir = os.path.join(OUT, carpeta)
    os.makedirs(out_dir, exist_ok=True)
    formatos = formatos or FORMATOS

    objetivos = [f"{nombre}-{sufijo}"
                 for sufijo in formatos
                 for nombre, _ in slides]
    for prefijo in objetivos:
        for ext in (".svg", ".png"):
            ruta = os.path.join(out_dir, prefijo + ext)
            if os.path.exists(ruta):
                os.remove(ruta)

    generados = []
    for sufijo, (W, H) in formatos.items():
        for nombre, builder in slides:
            slide = builder(W, H, reel=(sufijo == "reel"))
            svg = slide.guardar(os.path.join(out_dir, f"{nombre}-{sufijo}.svg"))
            generados.append(svg)

    for svg in generados:
        png = svg[:-4] + ".png"
        r = subprocess.run(
            ["inkscape", svg, "--export-type=png",
             f"--export-filename={png}", "--export-dpi=96"],
            capture_output=True, text=True)
        if not os.path.exists(png):
            raise SystemExit(f"Inkscape falló con {svg}:\n{r.stderr}")

    print(f"OK [{carpeta}]: {len(generados)} SVG + PNG en {out_dir}")
    return generados
