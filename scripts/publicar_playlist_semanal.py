#!/usr/bin/env python3
"""Publica el anuncio de la playlist semanal en Facebook e Instagram.

Lee la selección guardada por `generar_playlist_semanal.py --output-json`,
genera una tarjeta dinámica con 3 artistas destacados, construye el copy
para FB e IG (con menciones @handle en IG), publica usando la infra
existente de `lib.promo_fg` y registra el resultado en la tabla `PromoPost`.

Uso:
    python scripts/publicar_playlist_semanal.py --dry-run   # solo genera tarjeta y copy
    python scripts/publicar_playlist_semanal.py             # publica en FB/IG
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import lib.promo_fg as promo_fg
from db.database import SessionLocal
from db.models import Artist, PromoPost
from lib.repository import ArtistRepository

SELECCION_FILE = BASE_DIR / "data" / "playlist_seleccion_semanal.json"
PROMOS_DIR = BASE_DIR / "instance" / "promos"

# Colores identidad FG (marca del sitio: violeta)
ACENTO = (157, 78, 221)         # #9d4edd violeta
ACENTO_CLARO = (224, 170, 255)  # #e0aaff lavanda
TEXTO = "#ffffff"
LIENZO = (1080, 1080)

# Paleta del fondo "radar de frontera" (violeta, coherente con la marca)
RADAR = (186, 85, 211)          # #ba55d3 orquídea/violeta medio
RADAR_OSCURO = (54, 30, 74)     # #361e4a violeta nocturno
RADAR_FONDO = (16, 10, 25)      # #100a19 base violeta profundo


def load_env():
    """Carga variables desde .env de la raíz."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _cargar_fuente(tamano: int, candidatos: list) -> "ImageFont":
    from PIL import ImageFont
    for ruta in candidatos:
        try:
            return ImageFont.truetype(str(ruta), tamano)
        except Exception:
            continue
    return ImageFont.load_default()


def _fuente(tamano: int):
    """Carga Archivo Black (display: titular y nombres; fallback y luego default)."""
    candidatos = [
        BASE_DIR / "web/public/fonts/ArchivoBlack-Regular.ttf",
        Path(os.path.expanduser("~/.local/share/fonts/carrusel/ArchivoBlack-Regular.ttf")),
    ]
    return _cargar_fuente(tamano, candidatos)


def _fuente_texto(tamano: int):
    """Carga Inter (texto: canciones, franja, botón, semana; fallback y luego default)."""
    candidatos = [
        BASE_DIR / "web/public/fonts/Inter.ttf",
        Path(os.path.expanduser("~/.local/share/fonts/carrusel/Inter.ttf")),
    ]
    return _cargar_fuente(tamano, candidatos)


def _texto_glow(lienzo, pos: tuple, texto: str, fuente, color, glow_radius: int = 6, glow_alpha: int = 160, sombra: bool = True):
    """Renderiza texto con sombra direccional + glow (halo) sobre lienzo RGBA.

    La sombra (negro, offset y blur) da separación del fondo; el glow amable
    resalta sobre el radar. Determinista.
    """
    from PIL import Image, ImageDraw, ImageFilter
    if isinstance(color, str):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        rgb = (r, g, b)
    else:
        rgb = tuple(color[:3])
    if sombra:
        capa_s = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        ImageDraw.Draw(capa_s).text((pos[0] + 3, pos[1] + 3), texto, font=fuente, fill=(0, 0, 0, 190))
        capa_s = capa_s.filter(ImageFilter.GaussianBlur(1.6))
        lienzo.alpha_composite(capa_s)
    capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
    ImageDraw.Draw(capa).text(pos, texto, font=fuente, fill=(*rgb, glow_alpha))
    capa = capa.filter(ImageFilter.GaussianBlur(glow_radius))
    lienzo.alpha_composite(capa)
    ImageDraw.Draw(lienzo).text(pos, texto, font=fuente, fill=color)


def _centrar_texto(draw, texto: str, fuente, y: int, lienzo_ancho: int, color, lienzo=None, glow: bool = True) -> int:
    """Dibuja texto centrado con glow; devuelve la altura usada."""
    caja = draw.textbbox((0, 0), texto, font=fuente)
    ancho = caja[2] - caja[0]
    alto = caja[3] - caja[1]
    x = (lienzo_ancho - ancho) // 2
    if lienzo is None and hasattr(draw, "image"):
        lienzo = draw.image
    if glow and lienzo is not None:
        _texto_glow(lienzo, (x, y), texto, fuente, color)
    elif lienzo is not None:
        _texto_glow(lienzo, (x, y), texto, fuente, color, glow_radius=2, glow_alpha=120)
    else:
        draw.text((x + 3, y + 3), texto, font=fuente, fill="#00000090")
        draw.text((x, y), texto, font=fuente, fill=color)
    return alto


def _centrar_texto_en_caja(draw, texto: str, fuente, y: int, x_inicio: int, ancho_caja: int, color, lienzo=None, glow: bool = True) -> int:
    """Dibuja texto centrado dentro de una caja con glow."""
    caja = draw.textbbox((0, 0), texto, font=fuente)
    ancho = caja[2] - caja[0]
    alto = caja[3] - caja[1]
    x = x_inicio + (ancho_caja - ancho) // 2
    if lienzo is None and hasattr(draw, "image"):
        lienzo = draw.image
    if glow and lienzo is not None:
        _texto_glow(lienzo, (x, y), texto, fuente, color)
    elif lienzo is not None:
        _texto_glow(lienzo, (x, y), texto, fuente, color, glow_radius=2, glow_alpha=120)
    else:
        draw.text((x + 3, y + 3), texto, font=fuente, fill="#00000090")
        draw.text((x, y), texto, font=fuente, fill=color)
    return alto


def _descargar_imagen(url: str):
    """Descarga una imagen desde URL; None si falla."""
    import requests
    from PIL import Image
    from io import BytesIO
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None


def _recortar_cuadrado(img, size):
    """Recorta al cuadrado centrado y redimensiona."""
    from PIL import Image
    w, h = img.size
    if w != h:
        lado = min(w, h)
        img = img.crop(((w - lado) // 2, (h - lado) // 2, (w + lado) // 2, (h + lado) // 2))
    return img.resize(size, Image.Resampling.LANCZOS)


def _pegar_monograma(lienzo, alto: int, x: int, y_eje: int, tinto=None):
    """Pega el monograma FG centrado en 'y_eje'."""
    from PIL import Image
    RUTA_MONOGRAMA = BASE_DIR / "web" / "public" / "assets" / "monograma_fg.png"
    if not RUTA_MONOGRAMA.exists():
        return
    mono = Image.open(RUTA_MONOGRAMA).convert("RGBA")
    w = int(mono.size[0] * alto / mono.size[1])
    recorte = mono.resize((w, alto), Image.LANCZOS)
    if tinto:
        lav = Image.new("RGBA", recorte.size, (*tinto, 255))
        lav.putalpha(recorte.getchannel("A"))
        recorte = lav
    lienzo.alpha_composite(recorte, (int(x), int(y_eje - alto / 2)))



def _fondo_radar_frontera() -> "Image.Image":
    """Fondo 'radar de la frontera': retícula GPS, anillos de sonar y coordenadas.

    Estilo totalmente distinto al neón degradado de los artistas verificados:
    plano oscuro azulado con cuadrícula de mapa, anillos de radar cian que
    barren alrededor del monograma y coordenadas de las ciudades de la frontera.
    Determinista (sin ruido aleatorio) para verificar la salida de forma estable.
    """
    from PIL import Image, ImageDraw

    # Supersampling 2x: se dibuja a 2160 y se reduce a 1080 para suavizar (antialiasing) líneas y anillos, y se oscurece para que resalte el contenido.
    escala = 2
    ancho = LIENZO[0] * escala
    alto = LIENZO[1] * escala
    lienzo = Image.new("RGBA", (ancho, alto), RADAR_FONDO)
    draw = ImageDraw.Draw(lienzo)

    # Retícula GPS (cuadrícula sutil de mapa)
    paso = 90 * escala
    for x in range(0, ancho, paso):
        draw.line([(x, 0), (x, alto)], fill=(*RADAR_OSCURO, 150), width=2)
    for y in range(0, alto, paso):
        draw.line([(0, y), (ancho, y)], fill=(*RADAR_OSCURO, 150), width=2)

    # Anillos de radar (sonar) alrededor del monograma
    cx, cy = 540 * escala, 445 * escala
    for i, radio in enumerate([170, 300, 430, 560, 690]):
        radio *= escala
        alfa = max(16, 85 - i * 14)
        draw.ellipse(
            (cx - radio, cy - radio, cx + radio, cy + radio),
            outline=(*RADAR, alfa), width=6 if i == 0 else 4,
        )

    # Línea de barrido del radar
    import math
    for ang in range(0, 360, 12):
        r = 690 * escala
        x1 = cx
        y1 = cy
        x2 = cx + int(r * math.cos(math.radians(ang)))
        y2 = cy + int(r * math.sin(math.radians(ang)))
        alfa = 80 if ang % 36 == 0 else 26
        draw.line([(x1, y1), (x2, y2)], fill=(*RADAR, alfa), width=4)

    # Cruz del radar (plomada central)
    draw.line([(cx - 14 * escala, cy), (cx + 14 * escala, cy)], fill=(*RADAR, 190), width=4)
    draw.line([(cx, cy - 14 * escala), (cx, cy + 14 * escala)], fill=(*RADAR, 190), width=4)

    # Coordenadas de las ciudades de la frontera como etiquetas de mapa
    _fuente_peq = _fuente_texto(20 * escala)
    for (ex, ey, etiqueta) in [
        (130, 300, "REYNOSA"), (940, 300, "McALLEN"),
        (120, 780, "MATAMOROS"), (930, 800, "BROWNSVILLE"),
        (540, 800, "NUEVO LAREDO"),
    ]:
        ex *= escala
        ey *= escala
        l, t, r, b = draw.textbbox((0, 0), etiqueta, font=_fuente_peq)
        w = r - l
        h = b - t
        draw.text((ex - w / 2, ey - h / 2), etiqueta, font=_fuente_peq, fill=(*RADAR, 130))

    # Reducir a 1080 (antialiasing real de las líneas del radar)
    lienzo = lienzo.resize(LIENZO, Image.LANCZOS)

    # Veladura muy ligera: mantiene el radar visible pero sin competir con el contenido
    velo = Image.new("RGBA", LIENZO, (*RADAR_FONDO, 12))
    lienzo.alpha_composite(velo)

    return lienzo


def _obtener_artistas_adicionales(datos: dict, seleccionados_3: list[dict]) -> list[str]:
    """Artistas de la franja: los de la selección más otros de la escena (con Spotify).

    Mantiene fijos los headliners y rellena la franja (máx. 14, en 2 líneas)
    con el resto de la escena que tienen Spotify, ya que rotan en la playlist
    semanal. Ordenado alfabéticamente para mantener la imagen determinista.
    """
    principales = {s["artista"] for s in seleccionados_3}
    adicionales = []
    for t in datos.get("tracks", []):
        if t["artista"] not in principales and t["artista"] not in adicionales:
            adicionales.append(t["artista"])
    if len(adicionales) < 14:
        from db.database import SessionLocal
        from lib.repository import ArtistRepository
        session = SessionLocal()
        try:
            for artista in sorted(ArtistRepository(session).con_spotify(), key=lambda a: a.nombre.lower()):
                if len(adicionales) >= 14:
                    break
                if artista.nombre not in principales and artista.nombre not in adicionales:
                    adicionales.append(artista.nombre)
        finally:
            session.close()
    return adicionales[:14]  # máximo 14 para la franja de 2 líneas


def _foto_circular_artista(lienzo, draw, artista_nombre, foto_x, foto_y, foto_size, estilo: str = "cards"):
    """Foto circular del artista con anillos (o placeholder si no hay foto).

    Comparte la lógica de recorte circular y anillos de acento entre los
    layouts de cards y editorial (estilo = "cards" | "editorial").
    """
    from PIL import Image, ImageDraw

    foto_url = None
    session = SessionLocal()
    try:
        artista = ArtistRepository(session).por_nombre(artista_nombre)
        foto_url = artista.imagen_perfil if artista else None
    finally:
        session.close()

    if estilo == "editorial":
        anillo, detalle = 8, 16
        grosor_a, grosor_d = 6, 3
        color_a, color_d = (*ACENTO_CLARO, 200), (*ACENTO, 100)
        placeholder = ((*ACENTO, 50), (*ACENTO_CLARO, 120), 4)
        con_detalles = True
    else:
        anillo, detalle = 6, 12
        grosor_a, grosor_d = 5, 2
        color_a, color_d = (*ACENTO_CLARO, 220), (*ACENTO, 120)
        placeholder = ((*ACENTO, 60), (*ACENTO_CLARO, 100), 3)
        con_detalles = False

    def _placeholder():
        fill, outline, w = placeholder
        draw.ellipse(
            (foto_x, foto_y, foto_x + foto_size, foto_y + foto_size),
            fill=fill, outline=outline, width=w
        )

    if not foto_url:
        _placeholder()
        return

    foto = _descargar_imagen(foto_url)
    if not foto:
        _placeholder()
        return

    foto = _recortar_cuadrado(foto, (foto_size, foto_size))

    # Supersampling (3x) para bordes suaves del círculo, anillos y detalles.
    esc = 3
    m = detalle
    bb = foto_size + 2 * m
    gran = bb * esc
    capa = Image.new("RGBA", (gran, gran), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    mG = m * esc
    fG = foto_size * esc

    # Foto circular con máscara suavizada
    mascara = Image.new("L", (fG, fG), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, fG - 1, fG - 1), fill=255)
    foto_big = foto.resize((fG, fG), Image.LANCZOS).copy()
    foto_big.putalpha(mascara)
    capa.alpha_composite(foto_big, (mG, mG))

    # Anillos
    dc.ellipse(
        (mG - anillo * esc, mG - anillo * esc, mG + fG + anillo * esc, mG + fG + anillo * esc),
        outline=(*color_a[:3], 255), width=grosor_a * esc
    )
    dc.ellipse(
        (mG - detalle * esc, mG - detalle * esc, mG + fG + detalle * esc, mG + fG + detalle * esc),
        outline=(*color_d[:3], 255), width=grosor_d * esc
    )
    if con_detalles:
        import math
        cG = foto_size * esc // 2
        for ang in [0, 90, 180, 270]:
            rad = math.radians(ang)
            dx = int((foto_size // 2 + 20) * esc * math.cos(rad))
            dy = int((foto_size // 2 + 20) * esc * math.sin(rad))
            r6 = 6 * esc
            dc.ellipse(
                (mG + cG + dx - r6, mG + cG + dy - r6, mG + cG + dx + r6, mG + cG + dy + r6),
                fill=(*ACENTO_CLARO[:3], 220)
            )

    capa = capa.resize((bb, bb), Image.LANCZOS)
    lienzo.alpha_composite(capa, (foto_x - m, foto_y - m))


def _boton_spotify(lienzo, draw, btn_y):
    """Botón visual 'Escuchar en Spotify'."""
    btn_w = 380
    btn_h = 56
    btn_x = (LIENZO[0] - btn_w) // 2
    draw.rounded_rectangle(
        (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h),
        radius=28, fill=(*ACENTO, 255)
    )
    _centrar_texto_en_caja(draw, "ESCUCHAR EN SPOTIFY", _fuente_texto(22), btn_y + 12, btn_x, btn_w, (255, 255, 255, 255))


def _marca_fg(lienzo, y_texto: int, y_dominio: int):
    """Marca Frontera Grande: monograma + dominio, centrados (sin repetir nombre)."""
    from PIL import Image, ImageDraw

    alto_mono = 58
    ruta_mono = BASE_DIR / "web" / "public" / "assets" / "monograma_fg.png"
    if ruta_mono.exists():
        m = Image.open(ruta_mono)
        w_mono = int(m.size[0] * alto_mono / m.size[1])
    else:
        w_mono = alto_mono
    mono_x = (LIENZO[0] - w_mono) // 2
    _pegar_monograma(lienzo, alto_mono, mono_x, y_texto - 2)

    dominio = "fronteragrande.mx"
    fuente = _fuente_texto(24)
    caja = ImageDraw.Draw(lienzo).textbbox((0, 0), dominio, font=fuente)
    xd = (LIENZO[0] - (caja[2] - caja[0])) // 2
    _texto_glow(lienzo, (xd, y_dominio), dominio, fuente, (*ACENTO_CLARO, 230), glow_radius=5, glow_alpha=120)


def _guardar_tarjeta(lienzo, fecha: str) -> Path:
    """Guarda el lienzo final como JPG y devuelve la ruta."""
    PROMOS_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"playlist_semanal_{fecha.replace('-', '')}"
    ruta = PROMOS_DIR / f"{slug}.jpg"
    lienzo.convert("RGB").save(ruta, "JPEG", quality=90, optimize=True)
    return ruta




def _formatear_semana(fecha: str) -> str:
    """Convierte '2026-08-31' en la semana abreviada '31 AGO, 26'."""
    from datetime import date
    try:
        anio, mes, dia = (int(p) for p in fecha.split("-")[:3])
    except (ValueError, AttributeError):
        return fecha
    meses = [
        "ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
        "JUL", "AGO", "SEP", "OCT", "NOV", "DIC",
    ]
    if not (1 <= mes <= 12):
        return f"{dia} {fecha[-2:]}"
    return f"{dia} {meses[mes - 1]}, {anio % 100:02d}"


def _generar_layout_cartel(lienzo, seleccionados_3: list[dict], total_tracks: int, fecha: str, playlist_url: str = "", datos: dict | None = None) -> Path:
    """Layout 'cartel de festival': 3 headliners con foto y canción, franja de artistas y CTA.

    Diseño único de la tarjeta semanal: tres artistas protagonistas con foto
    circular y su canción, una franja que nombra a más proyectos de la playlist
    y un botón que lleva a abrirla en Spotify.
    """
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(lienzo)

    # Titular
    _centrar_texto(draw, "DESCUBRIMIENTO SEMANAL", _fuente(64), 24, LIENZO[0], TEXTO)
    _centrar_texto(draw, "nueva rotación de la escena", _fuente_texto(28), 122, LIENZO[0], (*ACENTO_CLARO, 235))
    # Semana: subtítulo sutil, no es el foco
    _centrar_texto(draw, f"Semana del {_formatear_semana(fecha)}", _fuente_texto(20), 158, LIENZO[0], (*ACENTO_CLARO, 210))

    # 3 artistas headliner: foto grande + nombre + canción
    card_w = 340
    gap = 30
    start_x = 0
    foto_y = 212

    for i, sel in enumerate(seleccionados_3):
        x = start_x + i * (card_w + gap)
        centro_x = x + card_w // 2
        headliner_central = i == 1
        foto_size = 290 if headliner_central else 260
        nombre_tam = 42 if headliner_central else 38
        cancion_tam = 26 if headliner_central else 24
        foto_x = centro_x - foto_size // 2

        # Foto circular con anillos neón
        _foto_circular_artista(lienzo, draw, sel["artista"], foto_x, foto_y, foto_size, estilo="editorial")

        # Nombre del artista (headliner)
        nombre = sel["artista"]
        maximo = card_w - 24
        tam = nombre_tam
        while tam > 22:
            caja = draw.textbbox((0, 0), nombre, font=_fuente(tam))
            if caja[2] - caja[0] <= maximo:
                break
            tam -= 2
        _centrar_texto_en_caja(draw, nombre, _fuente(tam), foto_y + foto_size + 20, x + 12, card_w - 24, TEXTO)

        # Canción (debajo, acento claro)
        cancion = sel["titulo"]
        maximo = card_w - 24
        tamc = cancion_tam
        while tamc > 18:
            caja = draw.textbbox((0, 0), cancion, font=_fuente_texto(tamc))
            if caja[2] - caja[0] <= maximo:
                break
            tamc -= 2
        _centrar_texto_en_caja(draw, cancion, _fuente_texto(tamc), foto_y + foto_size + 68, x + 12, card_w - 24, (*ACENTO_CLARO, 235))

    # Franja "también suenan" (cuadro alto con 2 líneas de artistas)
    franja_y = 632
    franja_h = 196
    franja_margen = 50
    franja = Image.new("RGBA", (LIENZO[0] - 2 * franja_margen, franja_h), (5, 10, 20, 220))
    draw_f = ImageDraw.Draw(franja)
    draw_f.rounded_rectangle(
        (0, 0, LIENZO[0] - 2 * franja_margen, franja_h), radius=22, outline=(*ACENTO_CLARO, 150), width=2
    )
    lienzo.alpha_composite(franja, (franja_margen, franja_y - 10))

    adicionales = _obtener_artistas_adicionales(datos, seleccionados_3) if datos else []
    _centrar_texto(draw, "TAMBIÉN SUENAN", _fuente_texto(24), franja_y + 4, LIENZO[0], (*ACENTO_CLARO, 255))
    ancho_mx = LIENZO[0] - 2 * franja_margen - 70

    if adicionales:
        def _medir(lista_nombres):
            caja = draw.textbbox((0, 0), "  ·  ".join(lista_nombres), font=_fuente_texto(22))
            return caja[2] - caja[0]

        linea1 = []
        for nombre in adicionales:
            if _medir(linea1 + [nombre]) <= ancho_mx and len(linea1) < 7:
                linea1.append(nombre)
        resto = adicionales[len(linea1):]
        linea2 = []
        for nombre in resto:
            if _medir(linea2 + [nombre]) <= ancho_mx and len(linea2) < 7:
                linea2.append(nombre)

        if linea1:
            _centrar_texto(draw, "  ·  ".join(linea1), _fuente_texto(22), franja_y + 52, LIENZO[0], TEXTO)
        if linea2:
            _centrar_texto(draw, "  ·  ".join(linea2), _fuente_texto(22), franja_y + 88, LIENZO[0], TEXTO)
        vistos = len(linea1) + len(linea2)
        # Cierre: mientras haya más tracks que artistas ya mostrados, invita a descubrir
        if total_tracks > 3 + vistos:
            _centrar_texto(draw, "…y más artistas", _fuente_texto(28), franja_y + 134, LIENZO[0], (*ACENTO_CLARO, 255))
        else:
            _centrar_texto(draw, f"{total_tracks} tracks", _fuente_texto(24), franja_y + 134, LIENZO[0], (*ACENTO_CLARO, 255))
    else:
        _centrar_texto(draw, f"{total_tracks} tracks", _fuente_texto(26), franja_y + 40, LIENZO[0], (*ACENTO_CLARO, 255))

    # Botón Spotify
    _boton_spotify(lienzo, draw, 848)

    # Marca FG
    _marca_fg(lienzo, 990, 1020)

    return _guardar_tarjeta(lienzo, fecha)


def generar_tarjeta_playlist(seleccionados_3: list[dict], total_tracks: int, fecha: str, playlist_url: str = "", datos: dict | None = None) -> Path | None:
    """Genera la tarjeta 1080x1080 con 3 artistas (diseño único 'cartel de festival')."""
    lienzo = _fondo_radar_frontera()
    return _generar_layout_cartel(lienzo, seleccionados_3, total_tracks, fecha, playlist_url, datos)


def _hook_semana(fecha: str, plataforma: str) -> list[str]:
    """Elige el hook (texto de entrada) de la semana, de forma determinista.

    Rota por semana ISO del año (no es aleatorio: misma fecha ⇒ mismo hook,
    para que la tarjeta/copy sea estable y reproducible). Hay un banco propio
    por plataforma (FB sin emojis; IG con emojis y referencias de cruce).
    """
    from datetime import date

    HOOKS_FB = [
        ["🎧 Esa canción que no paras de tararear desde el lunes.",
         "La que suena distinto cuando cruzas el puente de noche."],
        ["🎵 El soundtrack de la frontera no descansa ni los lunes.",
         "Esta semana llega la rotación con nuevos sonidos de la región."],
        ["🌉 Del puente para acá hay pura buena música.",
         "La nueva rotación de la frontera ya está sonando."],
        ["🎶 Hay canciones que saben a cruzar el puente de noche.",
         "Estas semanales son de la frontera, con todo lo que eso implica."],
        ["🎸 No importa de qué lado del río estés: esto suena a hogar.",
         "La rotación de la semana ya está lista para que la escuches."],
        ["🔥 La frontera se escucha en todos los géneros.",
         "Una selección nueva, para que descubras qué hay de dónde vienes."],
    ]
    HOOKS_IG = [
        ["Esa canción que suena a cruzar el puente de noche con las ventanas abajo. 🌉",
         "La que te acompaña en el trayecto Reynosa ↔ McAllen, Matamoros ↔ Brownsville."],
        ["Hay canciones que huelen a taquería de la esquina y a carretera. 🌮",
         "La frontera suena distinto, y esta semana lo vuelve a demostrar."],
        ["De este lado del río hay de todo, y rota cada lunes. 🔄",
         "Nueva selección de la frontera para tus audífonos."],
        ["El puente une más que dos países: une playlists. 🌉",
         "La rotación de la semana es puro ritmo fronterizo."],
        ["¿Ya armaste el plan del fin de semana? Empieza con esto. 🎧",
         "La frontera tiene su propia banda sonora, y cambia cada lunes."],
        ["Si no conoces la escena de la frontera, esta semana es tu puerta. 🚪",
         "Una rotación nueva con los sonidos que nos hacen únicos."],
    ]
    try:
        _, semana, _ = date.fromisoformat(fecha).isocalendar()
    except (ValueError, TypeError):
        semana = 0
    banco = HOOKS_FB if plataforma == "fb" else HOOKS_IG
    return banco[semana % len(banco)]


def construir_copy_fb(datos: dict) -> str:
    """Construye el mensaje para Facebook."""
    sel = datos["seleccionados_3"]

    # Obtener más artistas de la lista completa (sin repetir los 3 principales)
    todos_artistas = []
    for t in datos.get("tracks", []):
        if t["artista"] not in [s["artista"] for s in sel]:
            if t["artista"] not in todos_artistas:
                todos_artistas.append(t["artista"])
    mas_artistas = todos_artistas[:8]  # hasta 8 más

    lines = [
        *(_hook_semana(datos["fecha"], "fb")),
        "",
        f'Esta semana en "Frontera Grande: Descubrimiento Semanal" rotan {datos["total_tracks"]} tracks de la frontera:',
    ]
    for s in sel:
        lines.append(f'🎵  {s["titulo"]} — {s["artista"]}')
    
    if mas_artistas:
        lines.append(f'{", ".join(mas_artistas)}... y más artistas esta semana.')
    else:
        lines.append(f'... y {datos["total_tracks"] - 3} más por descubrir.')
    
    lines.append("")
    lines.append("🎧  Escucha la playlist completa:")
    lines.append(datos["playlist_url"])
    lines.append("")
    lines.append("👉  Guárdala y no te pierdas la rotación del próximo lunes.")
    lines.append("")
    lines.append("🌐  Descubre y escucha a todos los proyectos de la frontera en fronteragrande.mx")
    lines.append("")
    lines.append("¿Tocas o produces? Suma tu proyecto a la escena: fronteragrande.mx")
    lines.append("")
    lines.append(f"Semana del {_formatear_semana(datos['fecha'])}")
    lines.append("")
    lines.append("#FronteraGrande #EscenaLocal #DescubrimientoSemanal #MusicaFronteriza")
    return "\n".join(lines)


def construir_copy_ig(datos: dict) -> str:
    """Construye el caption para Instagram con menciones @handle."""
    sel = datos["seleccionados_3"]
    menciones = [f"@{s['handle_ig']}" for s in sel if s.get("handle_ig")]
    
    # Obtener más artistas de la lista completa (sin repetir los 3 principales)
    todos_artistas = []
    for t in datos.get("tracks", []):
        if t["artista"] not in [s["artista"] for s in sel]:
            if t["artista"] not in todos_artistas:
                todos_artistas.append(t["artista"])
    mas_artistas = todos_artistas[:8]  # hasta 8 más
    
    lines = [
        *(_hook_semana(datos["fecha"], "ig")),
        "",
        f'Esta semana en "Frontera Grande: Descubrimiento Semanal" rotan {datos["total_tracks"]} tracks de la frontera:',
    ]
    for s in sel:
        lines.append(f'🎵  {s["titulo"]} — {s["artista"]}')
    
    if mas_artistas:
        lines.append(f'{", ".join(mas_artistas)}... y más artistas esta semana.')
    else:
        lines.append(f'... y {datos["total_tracks"] - 3} más por descubrir.')
    
    lines.append("")
    lines.append("🎧  Escucha completa: " + datos["playlist_url"])
    lines.append("👉  Guárdala → no te pierdas la rotación del próximo lunes.")
    lines.append("")
    lines.append("🌐 Descubre a todos los proyectos de la frontera en fronteragrande.mx")
    lines.append("")
    if menciones:
        lines.append(" ".join(menciones))
    lines.append("")
    lines.append(f"Semana del {_formatear_semana(datos['fecha'])}")
    lines.append("")
    hashtags = [
        "#FronteraGrande", "#DescubrimientoSemanal", "#EscenaLocal",
        "#MusicaIndependiente", "#Tamaulipas", "#ValleDeTexas",
        "#Reynosa", "#Matamoros", "#NuevoLaredo", "#McAllen", "#Brownsville",
        "#MusicaFronteriza", "#PuenteInternacional"
    ]
    lines.append(" ".join(hashtags))
    return "\n".join(lines)


def guardar_promo_post(artist_id: int | None, plataforma: str, post_id: str, mensaje: str, estado: str, error_detalle: str = ""):
    """Guarda el registro en la tabla PromoPost."""
    session = SessionLocal()
    try:
        promo = PromoPost(
            artist_id=artist_id,
            plataforma=plataforma,
            post_id=post_id,
            mensaje=mensaje,
            estado=estado,
            error_detalle=error_detalle,
        )
        session.add(promo)
        session.commit()
    finally:
        session.close()


def subir_tarjeta_a_api(ruta: Path, api_public_url: str) -> str | None:
    """Sube la tarjeta ya generada a la API para que Meta pueda descargarla.

    El workflow corre fuera de la API (GitHub Actions): la tarjeta existe en
    el runner pero no en el servidor, y Meta necesita una URL pública. Usa el
    endpoint `POST /api/admin/promos/upload` con `X-Admin-Token`.

    Returns:
        URL pública de la tarjeta, o None si la subida falla.
    """
    import requests

    token = os.getenv("ADMIN_PASSWORD", "").strip()
    if not token:
        print("[warn] ADMIN_PASSWORD no configurado; no se sube la tarjeta")
        return None
    try:
        with open(ruta, "rb") as f:
            r = requests.post(
                f"{api_public_url.rstrip('/')}/api/admin/promos/upload",
                data={"nombre": ruta.stem},
                files={"file": (ruta.name, f, "image/jpeg")},
                headers={"X-Admin-Token": token},
                timeout=120,
            )
        r.raise_for_status()
        url = r.json().get("url")
        print(f"  Tarjeta subida a la API: {url}")
        return url or None
    except Exception as exc:
        print(f"[warn] No se pudo subir la tarjeta a la API: {exc}")
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="genera tarjeta y copy sin publicar")
    parser.add_argument("--input-json", type=str, default=str(SELECCION_FILE), help="ruta al JSON de selección")
    args = parser.parse_args()

    load_env()

    if not SELECCION_FILE.exists() and not Path(args.input_json).exists():
        print(f"[error] No existe {args.input_json}. Ejecuta primero generar_playlist_semanal.py --output-json")
        return 1

    with open(args.input_json, encoding="utf-8") as f:
        datos = json.load(f)

    if not datos.get("seleccionados_3"):
        print("[error] No hay seleccionados_3 en el JSON")
        return 1

    print("=== Playlist Semanal ===")
    print(f'Fecha: {datos["fecha"]}')
    print(f'Playlist: {datos["playlist_url"]}')
    print(f'Total tracks: {datos["total_tracks"]}')
    print("Seleccionados para tarjeta:")
    for s in datos["seleccionados_3"]:
        print(f'  - {s["artista"]}: {s["titulo"]} (IG: @{s.get("handle_ig", "?")})')

    # Generar tarjeta
    print("\nGenerando tarjeta...")
    ruta_tarjeta = generar_tarjeta_playlist(
        datos["seleccionados_3"], datos["total_tracks"], datos["fecha"], datos["playlist_url"], datos
    )
    if not ruta_tarjeta:
        print("[error] No se pudo generar la tarjeta")
        return 1
    print(f"Tarjeta guardada en: {ruta_tarjeta}")

    # URLs públicas de la imagen (para que FB/IG la descarguen)
    api_public_url = os.getenv("API_PUBLIC_URL", "").rstrip("/")
    if not api_public_url:
        print("[warn] API_PUBLIC_URL no configurado; la publicación usará solo texto")
        imagen_url = None
        imagen_url_jpg = None
    else:
        slug = ruta_tarjeta.stem
        # El workflow corre fuera de la API: subir la tarjeta para que la URL
        # pública exista (si no, Meta devuelve 400 al no poder descargarla).
        subida = subir_tarjeta_a_api(ruta_tarjeta, api_public_url)
        if subida:
            imagen_url = subida
            imagen_url_jpg = subida  # mismo archivo JPEG
        else:
            imagen_url = f"{api_public_url}/api/promos/{slug}.jpg"
            imagen_url_jpg = imagen_url

    copy_fb = construir_copy_fb(datos)
    copy_ig = construir_copy_ig(datos)

    print("\n=== Copy Facebook ===")
    print(copy_fb)
    print("\n=== Copy Instagram ===")
    print(copy_ig)

    if args.dry_run:
        print("\n[DRY-RUN] No se publica en redes.")
        return 0

    # Verificar configuración de promo
    if not promo_fg.promo_configurado():
        print("[error] Promo no configurado: FG_PAGE_ID / FG_PAGE_TOKEN ausentes")
        return 1

    # Publicar en Facebook
    print("\nPublicando en Facebook...")
    resultado_fb = promo_fg.publicar_en_fb(copy_fb, imagen_url)
    print(f"  FB: {resultado_fb}")
    guardar_promo_post(
        artist_id=None,
        plataforma="fb",
        post_id=resultado_fb.get("post_id", ""),
        mensaje=copy_fb,
        estado="publicado" if resultado_fb.get("ok") else "error",
        error_detalle=resultado_fb.get("error", ""),
    )

    # Publicar en Instagram si está activado
    promo_ig = os.getenv("PROMO_IG", "false").lower() == "true"
    if promo_ig:
        print("Publicando en Instagram...")
        resultado_ig = promo_fg.publicar_en_ig(copy_ig, imagen_url_jpg)
        print(f"  IG: {resultado_ig}")
        guardar_promo_post(
            artist_id=None,
            plataforma="ig",
            post_id=resultado_ig.get("post_id", ""),
            mensaje=copy_ig,
            estado="publicado" if resultado_ig.get("ok") else "error",
            error_detalle=resultado_ig.get("error", ""),
        )
    else:
        print("PROMO_IG=false, saltando Instagram")

    print("\n✅ Publicación completada")
    return 0


if __name__ == "__main__":
    sys.exit(main())