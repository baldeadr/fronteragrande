#!/usr/bin/env python3
"""Genera 3 prototipos tipográficos para el carrusel (IG/FB).

Cada prototipo usa una combinación distinta de fuentes OFL gratuitas,
manteniendo Archivo Black solo para el logo FG.

A: Anton (titulos) + Space Grotesk (cuerpo) — Border Urban, impacto
B: Syne (titulos) + Inter (cuerpo) — Editorial moderno
C: Oswald (titulos) + Space Grotesk (cuerpo) + JetBrains Mono (chips) — Retro cartel

Genera 01 y 02 en cuadrado+reel para comparar. Salida: prototipos/{A,B,C}/
"""
import base64
import os
import subprocess
import glob
import html
import xml.etree.ElementTree as ET
from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_BASE = os.path.join(ROOT, "prototipos")
FUENTES = os.path.join(ROOT, "carrousel/fuentes")

BG = "#0b0b10"; SURFACE="#14141b"; SURFACE2="#1b1b24"; LINE="#262633"
TEXT="#ececf1"; MUTED="#8a8a9a"; ACCENT="#9d4edd"; ACCENT_SOFT="#2a1a33"

TTF_DIR = os.path.expanduser("~/.local/share/fonts/carrusel")
TTF_ARCHIVO = os.path.expanduser("~/.local/share/fonts/ArchivoBlack-Regular.ttf")
TTF_ARIAL = "/usr/share/fonts/msttcore/arial.ttf"
TTF_ARIAL_BD = "/usr/share/fonts/msttcore/arialbd.ttf"

FONT_MAP = {
    "anton": os.path.join(TTF_DIR, "Anton-Regular.ttf"),
    "spgro": os.path.join(TTF_DIR, "SpaceGrotesk.ttf"),
    "bebas": os.path.join(TTF_DIR, "BebasNeue.ttf"),
    "syne": os.path.join(TTF_DIR, "Syne.ttf"),
    "oswald": os.path.join(TTF_DIR, "Oswald.ttf"),
    "inter": os.path.join(TTF_DIR, "Inter.ttf"),
    "jet": os.path.join(TTF_DIR, "JetBrainsMono.ttf"),
}

_logo_svg = open(os.path.join(ROOT, "web/public/logo-frontera-grande.svg"), encoding="utf-8").read()
LOGO_INNER = _logo_svg.split("<svg", 1)[1].rsplit("</svg>", 1)[0].split(">", 1)[1]
_icon_svg = open(os.path.join(ROOT, "web/app/icon.svg"), encoding="utf-8").read()
LOGO_FG_INNER = _icon_svg.split("<svg", 1)[1].rsplit("</svg>", 1)[0].split(">", 1)[1]

def _data_uri(ruta):
    ext = os.path.splitext(ruta)[1].lower()
    mime = "image/jpeg" if ext in (".jpg",".jpeg") else "image/png"
    data = open(ruta,"rb").read()
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"

def esc(s): return html.escape(s, quote=True)

PALETAS = {
    "A-anton-space": {
        "titulo": ("anton", 0),  # (nombre, wght no usado, variable)
        "cuerpo": ("spgro", 0),
        "chip": ("spgro", 0),
        "kicker": ("spgro", 0),
        "desc": "Anton (tit) + Space Grotesk (cuerpo) — Urban condensado, max impacto IG",
    },
    "B-syne-inter": {
        "titulo": ("syne", 0),
        "cuerpo": ("inter", 0),
        "chip": ("inter", 0),
        "kicker": ("syne", 0),
        "desc": "Syne (tit) + Inter (cuerpo) — Editorial moderno, dinámico",
    },
    "C-oswald-jet": {
        "titulo": ("oswald", 0),
        "cuerpo": ("spgro", 0),
        "chip": ("jet", 0),
        "kicker": ("oswald", 0),
        "desc": "Oswald (tit) + Space Grotesk (cuerpo) + JetBrains Mono (chips) — Retro cartel",
    },
}

# Cache de fuentes por prototipo
_font_cache = {}
def font_for(paleta, rol, size, bold=False):
    fam = PALETAS[paleta][rol][0]
    path = FONT_MAP[fam]
    # Para variable fonts, no se especifica wght, PIL usa default
    key = (paleta, rol, size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]

def ancho(texto, f, spacing=0):
    return f.getlength(texto) + spacing * max(len(texto)-1, 0)

def wrap_px(texto, f, max_w, spacing=0):
    lineas=[]
    for parrafo in texto.split("\n"):
        palabras=parrafo.split()
        if not palabras: lineas.append(""); continue
        actual=palabras[0]
        for p in palabras[1:]:
            if ancho(actual+" "+p, f, spacing) <= max_w:
                actual += " "+p
            else:
                lineas.append(actual); actual=p
        lineas.append(actual)
    return lineas

class Slide:
    def __init__(self, W,H,fondo, paleta):
        self.W,self.H=W,H; self.paleta=paleta
        self.parts=[]; self.boxes=[]
        grad=f'<defs><linearGradient id="hero" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{ACCENT_SOFT}"/><stop offset="100%" stop-color="{SURFACE}"/></linearGradient></defs>'
        fill={"hero":"url(#hero)","bg":BG,"surface":SURFACE}[fondo]
        self.parts.append(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{grad}<rect width="{W}" height="{H}" fill="{fill}"/>')
    def fondo_imagen(self, nombre, opacity=0.32, velo=0.58):
        ruta=os.path.join(FUENTES, nombre)
        if not os.path.exists(ruta): return
        uri=_data_uri(ruta)
        self.parts.append(f'<image href="{uri}" x="0" y="0" width="{self.W}" height="{self.H}" preserveAspectRatio="xMidYMid slice" opacity="{opacity}"/>')
        self.parts.append(f'<rect width="{self.W}" height="{self.H}" fill="{BG}" opacity="{velo}"/>')
    def caja(self,x,y,w,h,eti): self.boxes.append((x,y,w,h,eti))
    def _font(self, rol, size, bold=False):
        return font_for(self.paleta, rol, size, bold)
    def texto(self, x, y_baseline, linea, size, rol="cuerpo", bold=False, color=TEXT, spacing=0, anchor="start", etiqueta="", registrar=True):
        f=self._font(rol, size, bold)
        w=ancho(linea,f,spacing)
        x_emit=x; x_box=x
        if anchor=="middle": x_box=x-w/2
        elif anchor=="end": x_box=x-w
        # familia para SVG: mapeo a nombre CSS
        fam_css={"anton":"Anton","spgro":"Space Grotesk","bebas":"Bebas Neue","syne":"Syne","oswald":"Oswald","inter":"Inter","jet":"JetBrains Mono"}[PALETAS[self.paleta][rol][0]]
        attrs=f'font-family="{fam_css}, Helvetica, sans-serif" font-size="{size}" fill="{color}"'
        if bold: attrs+=' font-weight="700"'
        # Anton/Bebas/Oswald ya son display, no necesitan weight extra pero lo dejamos
        if rol=="titulo": attrs+=' font-weight="900"'
        if spacing: attrs+=f' letter-spacing="{spacing}"'
        if anchor!="start": attrs+=f' text-anchor="{anchor}"'
        self.parts.append(f'<text x="{x_emit:.1f}" y="{y_baseline:.1f}" {attrs}>{esc(linea)}</text>')
        if registrar and etiqueta:
            alto=size*1.05
            self.caja(x_box, y_baseline-alto*0.78, w, alto, etiqueta)
        return w
    def bloque(self, x,y,texto,size,max_w, rol="cuerpo", bold=False, color=TEXT, spacing=0, line_h=1.32, anchor="start", etiqueta=""):
        f=self._font(rol,size,bold)
        lineas=wrap_px(texto,f,max_w,spacing)
        alto_linea=size*line_h
        ancho_max=max(ancho(ln,f,spacing) for ln in lineas) if lineas else 0
        for i,ln in enumerate(lineas):
            self.texto(x, y+alto_linea*0.78+i*alto_linea, ln, size, rol=rol, bold=bold, color=color, spacing=spacing, anchor=anchor, etiqueta="")
        if etiqueta and lineas:
            x_box=x-ancho_max/2 if anchor=="middle" else (x-ancho_max if anchor=="end" else x)
            self.caja(x_box,y,ancho_max,alto_linea*len(lineas),etiqueta)
        return len(lineas)*alto_linea
    def linea_v_path(self,cx,y,w,color=ACCENT,width=10):
        s=w/340.0; path_w=256*s; x0=cx-path_w/2
        d=f"M{x0:.1f} {y}h{104*s:.1f}c{11*s:.1f} 0 {14*s:.1f} {-8*s:.1f} {24*s:.1f} {-8*s:.1f}s{13*s:.1f} {8*s:.1f} {24*s:.1f} {8*s:.1f}h{104*s:.1f}"
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-linecap="round" stroke-width="{width}"/>')
    def logo_fg(self,cx,y,size):
        self.parts.append(f'<svg x="{cx-size/2:.1f}" y="{y}" width="{size}" height="{size}" viewBox="0 0 512 512">{LOGO_FG_INNER}</svg>')
    def fantasma(self,digitos,size,x,y_baseline,color):
        f=self._font("titulo",size)
        self.parts.append(f'<text x="{x}" y="{y_baseline}" font-family="Anton, Arial, sans-serif" font-weight="900" font-size="{size}" fill="{color}">{esc(digitos)}</text>')
    def chip(self,x,y,txt, relleno=False, size=34, bold=True):
        f=self._font("chip",size,bold)
        pad_x,alto=size*0.95, size*2.1
        w=ancho(txt.upper(),f)+pad_x*2
        if relleno:
            self.parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{alto}" rx="{alto/2:.1f}" fill="{ACCENT_SOFT}"/>'); color=ACCENT
        else:
            self.parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{alto}" rx="{alto/2:.1f}" fill="none" stroke="{LINE}" stroke-width="2"/>'); color=MUTED
        self.texto(x+pad_x, y+alto*0.68, txt.upper(), size, rol="chip", bold=bold, color=color, spacing=2, etiqueta=f"chip:{txt}")
        return w,alto
    def desliza(self,cy):
        size=28; f=self._font("cuerpo",size,True); w_txt=ancho("Desliza",f,1); total=w_txt+56; x0=(self.W-total)/2
        self.parts.append(f'<g opacity="0.9">')
        self.texto(x0,cy,"Desliza",size, rol="cuerpo", bold=True, color=MUTED, spacing=1, etiqueta="desliza")
        ax=x0+w_txt+16; ay=cy-size*0.32
        self.parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{ax+34:.1f}" y2="{ay:.1f}" stroke="{ACCENT}" stroke-width="4" stroke-linecap="round"/><polyline points="{ax+22:.1f},{ay-9:.1f} {ax+34:.1f},{ay:.1f} {ax+22:.1f},{ay+9:.1f}" fill="none" stroke="{ACCENT}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
        self.parts.append('</g>')
    def footer(self,txt,y=None,dominio_grande=False):
        if y is None: y=self.H-64
        if dominio_grande:
            size=52; self.parts.append(f'<line x1="84" y1="{y-74}" x2="{self.W-84}" y2="{y-74}" stroke="{LINE}" stroke-width="2"/>')
            self.texto(self.W/2,y,txt,size, rol="titulo", color=TEXT, anchor="middle", etiqueta="footer")
        else:
            size=24; self.parts.append(f'<line x1="84" y1="{y-40}" x2="{self.W-84}" y2="{y-40}" stroke="{LINE}" stroke-width="2"/>')
            self.texto(84,y,txt.upper(),size, rol="cuerpo", bold=True, color=MUTED, spacing=3, etiqueta="footer")
    def verificar(self):
        for i in range(len(self.boxes)):
            for j in range(i+1,len(self.boxes)):
                ax,ay,aw,ah,an=self.boxes[i]; bx,by,bw,bh,bn=self.boxes[j]
                if ax<bx+bw and bx<ax+aw and ay<by+bh and by<ay+ah:
                    raise AssertionError(f"SOLAPE: '{an}' vs '{bn}' en {self.W}x{self.H}")
    def guardar(self,ruta):
        self.verificar(); self.parts.append("</svg>")
        open(ruta,"w",encoding="utf-8").write("\n".join(self.parts))
        ET.parse(ruta); return ruta

# ——— slides (versión simplificada con texto nuevo) ———
def s_portada(W,H,reel,paleta):
    s=Slide(W,H,"hero",paleta); s.fondo_imagen("01-portada-bg.jpg", opacity=0.38)
    top=300 if reel else 96; bot=1500 if reel else H-60
    s.texto(W-84, top+30,"01",26, rol="cuerpo", bold=True, color=MUTED, spacing=2, anchor="end", etiqueta="num")
    logo_sz=230 if not reel else 250; s.logo_fg(W/2, top+70, logo_sz)
    y=top+70+logo_sz+ (110 if reel else 52)
    fs=176 if reel else 148
    f=s._font("titulo",fs); titulo_top=y
    for ln in ("FRONTERA","GRANDE"):
        s.texto(W/2, y+fs*0.82, ln, fs, rol="titulo", color=TEXT, anchor="middle", etiqueta=""); y+=fs*0.96
    w_tit=max(ancho(ln,f) for ln in ("FRONTERA","GRANDE")); s.caja((W-w_tit)/2,titulo_top,w_tit,y-titulo_top,"titulo")
    s.linea_v_path(W/2, y+22,420,width=13); y+=35
    gancho_fs=50 if reel else 44
    y+=((84 if reel else 42)+gancho_fs)
    s.bloque(W/2,y,"La escena de tu frontera,\npor fin en tu mapa.",gancho_fs,W-180, rol="cuerpo", color=TEXT, anchor="middle", line_h=1.25, etiqueta="gancho")
    s.desliza(bot if reel else bot-10); return s

def s_quesomos(W,H,reel,paleta):
    s=Slide(W,H,"bg",paleta); s.fondo_imagen("02-mapa-bg.jpg", opacity=0.58, velo=0.38)
    top=330 if reel else 110; ghost=760 if reel else 520
    s.fantasma("02",ghost,W-40,H*(0.98 if reel else 0.99),SURFACE2)
    x=84; s.bloque(x,top,"QUÉ SOMOS",28,400, rol="kicker", bold=True, color=MUTED, spacing=6, etiqueta="kicker")
    y=top+44+(70 if reel else 36)
    fs=124 if reel else 96
    y+=s.bloque(x,y,"El mapa vivo\nde la escena",fs,700, rol="titulo", line_h=1.02, etiqueta="titulo")
    y+=(86 if reel else 50)
    y+=s.bloque(x,y,"Una base de datos abierta de los proyectos de la frontera grande de Tamaulipas.",46 if reel else 40,760, rol="cuerpo", color=TEXT, line_h=1.28, etiqueta="lead")
    y+=(56 if reel else 42)
    y+=s.bloque(x,y,"Hoy, música: bandas, solistas, DJs, colectivos, covers y tributos. Mañana, otras disciplinas.",32,720, rol="cuerpo", color=TEXT, line_h=1.35, etiqueta="body1")
    y+=(28 if reel else 22)
    y+=s.bloque(x,y,"Directorio, feed y perfiles con enlaces directos a donde realmente están.",32,720, rol="cuerpo", color=MUTED, line_h=1.35, etiqueta="body2")
    s.footer("Sin números inventados  |  Datos con fuente", y=(1532 if reel else None)); return s

# Generación
for paleta in PALETAS:
    out = os.path.join(OUT_BASE, paleta)
    for viejo in glob.glob(os.path.join(out,"*")):
        os.remove(viejo)
    os.makedirs(out, exist_ok=True)
    generados=[]
    for sufijo,(W,H) in [("post",(1080,1440)),("reel",(1080,1920))]:
        for builder,nombre in [(s_portada,"01-portada"),(s_quesomos,"02-quesomos")]:
            slide=builder(W,H, reel=(sufijo=="reel"), paleta=paleta)
            svg=slide.guardar(os.path.join(out, f"{nombre}-{sufijo}.svg"))
            generados.append(svg)
    for svg in generados:
        png=svg[:-4]+".png"
        r=subprocess.run(["inkscape", svg, "--export-type=png", f"--export-filename={png}", "--export-dpi=96"], capture_output=True, text=True)
        if not os.path.exists(png):
            raise SystemExit(f"Inkscape falló {svg}:\n{r.stderr}")
    print(f"OK {paleta}: {len(generados)} SVG+PNG en {out} — {PALETAS[paleta]['desc']}")
