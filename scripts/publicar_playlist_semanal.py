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
import random
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

# Colores identidad FG
BG = "#0b0b10"
ACENTO = (157, 78, 221)         # #9d4edd
ACENTO_CLARO = (224, 170, 255)  # #e0aaff
VIOLETA = (123, 44, 191)        # #7b2cbf
TEXTO = "#ffffff"
LIENZO = (1080, 1080)


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


def _fuente(tamano: int):
    """Carga Archivo Black (fallback a la fuente por defecto)."""
    try:
        from PIL import ImageFont
        FUENTE_PATH = BASE_DIR / "web/public/fonts/ArchivoBlack-Regular.ttf"
        return ImageFont.truetype(str(FUENTE_PATH), tamano)
    except Exception:
        from PIL import ImageFont
        return ImageFont.load_default()


def _centrar_texto(draw, texto: str, fuente, y: int, lienzo_ancho: int, color, sombra: str = "#00000090") -> int:
    """Dibuja texto centrado con sombra sutil; devuelve la altura usada."""
    caja = draw.textbbox((0, 0), texto, font=fuente)
    ancho = caja[2] - caja[0]
    alto = caja[3] - caja[1]
    x = (lienzo_ancho - ancho) // 2
    draw.text((x + 3, y + 3), texto, font=fuente, fill=sombra)
    draw.text((x, y), texto, font=fuente, fill=color)
    return alto


def _centrar_texto_en_caja(draw, texto: str, fuente, y: int, x_inicio: int, ancho_caja: int, color, sombra: str = "#00000090") -> int:
    """Dibuja texto centrado dentro de una caja [x_inicio, x_inicio + ancho_caja]."""
    caja = draw.textbbox((0, 0), texto, font=fuente)
    ancho = caja[2] - caja[0]
    alto = caja[3] - caja[1]
    x = x_inicio + (ancho_caja - ancho) // 2
    draw.text((x + 3, y + 3), texto, font=fuente, fill=sombra)
    draw.text((x, y), texto, font=fuente, fill=color)
    return alto


def _fondo_gradiente(size):
    """Degradado diagonal violeta→negro (identidad FG)."""
    from PIL import Image
    tope = Image.new("RGB", size, VIOLETA)
    base = Image.new("RGB", size, BG)
    grad = Image.linear_gradient("L").rotate(135, expand=True).resize(size)
    return Image.composite(tope, base, grad).convert("RGBA")


def _brillo_radial(size, centro, radio, color, alpha, desenfoque):
    """Halo suave (neón)."""
    from PIL import Image, ImageDraw, ImageFilter
    capa = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(capa).ellipse(
        (centro[0] - radio, centro[1] - radio, centro[0] + radio, centro[1] + radio),
        fill=(*color, alpha),
    )
    return capa.filter(ImageFilter.GaussianBlur(desenfoque))


def _esquinas_redondeadas(img, radio: int = 40):
    """Aplica máscara de esquinas redondeadas."""
    from PIL import Image, ImageDraw
    mascara = Image.new("L", img.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle(
        (0, 0, img.size[0] - 1, img.size[1] - 1), radius=radio, fill=255
    )
    salida = img.copy()
    salida.putalpha(mascara)
    return salida


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


def _fondo_playlist() -> "Image.Image":
    """Fondo personalizado para la playlist semanal: degradado + grid sutil + acento."""
    from PIL import Image, ImageDraw
    
    # Base: degradado diagonal violeta→negro
    lienzo = _fondo_gradiente(LIENZO)
    
    # Capa de "grid" sutil (patrón de líneas finas estilo equalizador)
    grid = Image.new("RGBA", LIENZO, (0, 0, 0, 0))
    draw_grid = ImageDraw.Draw(grid)
    for y in range(0, 1080, 60):
        alpha = 12 if (y // 60) % 2 == 0 else 8
        draw_grid.line([(0, y), (1080, y)], fill=(*ACENTO_CLARO, alpha), width=1)
    for x in range(0, 1080, 60):
        alpha = 12 if (x // 60) % 2 == 0 else 8
        draw_grid.line([(x, 0), (x, 1080)], fill=(*ACENTO_CLARO, alpha), width=1)
    lienzo.alpha_composite(grid)
    
    # Halo central suave
    lienzo.alpha_composite(_brillo_radial(LIENZO, (540, 500), 400, ACENTO, 80, 150))
    lienzo.alpha_composite(_brillo_radial(LIENZO, (540, 500), 250, ACENTO_CLARO, 50, 100))
    
    # Línea divisoria decorativa bajo el título
    draw = ImageDraw.Draw(lienzo)
    draw.line(
        [(240, 155), (840, 155)],
        fill=(*ACENTO_CLARO, 100),
        width=2
    )
    # Puntitos en la línea
    for x in range(240, 841, 40):
        draw.ellipse(
            [(x - 3, 152), (x + 3, 158)],
            fill=(*ACENTO, 180)
        )
    
    return lienzo


def _fondo_playlist_editorial() -> "Image.Image":
    """Fondo estilo editorial/revista: bloques de color, tipografía grande, textura."""
    from PIL import Image, ImageDraw, ImageFilter
    import random
    
    # Base oscura con textura de grano
    lienzo = Image.new("RGBA", LIENZO, "#08080c")
    draw = ImageDraw.Draw(lienzo)
    
    # Grano/fine noise sutil
    noise = Image.new("RGBA", LIENZO, (0, 0, 0, 0))
    import random
    for _ in range(8000):
        x = random.randint(0, 1079)
        y = random.randint(0, 1079)
        alpha = random.randint(3, 12)
        noise.putpixel((x, y), (255, 255, 255, alpha))
    noise = noise.filter(ImageFilter.GaussianBlur(0.5))
    lienzo.alpha_composite(noise)
    
    # Bloque superior izquierdo - acento violeta grande
    draw.rounded_rectangle(
        [(-200, -100), (500, 400)],
        radius=300,
        fill=(*VIOLETA, 60)
    )
    draw.rounded_rectangle(
        [(-100, 50), (450, 300)],
        radius=200,
        fill=(*ACENTO, 40)
    )
    
    # Bloque inferior derecho - acento claro
    draw.rounded_rectangle(
        [(700, 700), (1300, 1200)],
        radius=350,
        fill=(*ACENTO_CLARO, 25)
    )
    
    # Línea diagonal decorativa cruzando
    for i in range(15):
        x1 = 100 + i * 60
        y1 = 980 - i * 60
        x2 = x1 + 40
        y2 = y1 - 40
        alpha = 30 + i * 10
        draw.line(
            [(x1, y1), (x2, y2)],
            fill=(*ACENTO_CLARO, alpha),
            width=3
        )
    
    # Círculos decorativos dispersos (burbujas)
    for (cx, cy, r, a) in [
        (180, 850, 80, 15),
        (950, 180, 120, 12),
        (800, 850, 60, 18),
        (200, 200, 40, 20),
        (900, 600, 100, 10),
    ]:
        draw.ellipse(
            [(cx - r, cy - r), (cx + r, cy + r)],
            outline=(*ACENTO_CLARO, a),
            width=2
        )
    
    # Barra lateral izquierda con patrón
    draw.rectangle(
        [(0, 0), (8, 1080)],
        fill=(*ACENTO, 180)
    )
    for y in range(40, 1080, 80):
        draw.rectangle(
            [(0, y), (8, y + 30)],
            fill=(*ACENTO_CLARO, 200)
        )
    
    return lienzo


def _generar_layout_cards(lienzo, seleccionados_3: list[dict], total_tracks: int, fecha: str, draw=None) -> Path | None:
    """Layout original: 3 cards horizontales."""
    from PIL import Image, ImageDraw
    
    if draw is None:
        draw = ImageDraw.Draw(lienzo)

    # Título principal
    _centrar_texto(draw, "DESCUBRIMIENTO SEMANAL", _fuente(58), 48, LIENZO[0], TEXTO)
    _centrar_texto(draw, "Nueva selección del lunes", _fuente(26), 112, LIENZO[0], (*ACENTO_CLARO, 235))

    # 3 cards de artistas
    card_w = 300
    card_h = 440
    gap = 40
    start_x = (LIENZO[0] - (3 * card_w + 2 * gap)) // 2
    card_y = 175

    for i, sel in enumerate(seleccionados_3):
        x = start_x + i * (card_w + gap)
        
        # Card con glassmorphism sutil
        card_bg = Image.new("RGBA", (card_w, card_h), (8, 5, 18, 180))
        draw_card = ImageDraw.Draw(card_bg)
        draw_card.rounded_rectangle(
            (0, 0, card_w - 1, card_h - 1), radius=28, outline=(*ACENTO_CLARO, 60), width=2
        )
        draw_card.line(
            [(20, 2), (card_w - 20, 2)],
            fill=(*ACENTO_CLARO, 40),
            width=3
        )
        lienzo.alpha_composite(card_bg, (x, card_y))

        # Foto del artista
        session = SessionLocal()
        try:
            artista = ArtistRepository(session).por_nombre(sel["artista"])
            foto_url = artista.imagen_perfil if artista else None
        finally:
            session.close()

        foto_size = 180  # más pequeño
        foto_x = x + (card_w - foto_size) // 2
        foto_y = card_y + 25
        
        if foto_url:
            foto = _descargar_imagen(foto_url)
            if foto:
                foto = _recortar_cuadrado(foto, (foto_size, foto_size))
                from PIL import Image, ImageDraw
                mascara = Image.new("L", (foto_size, foto_size), 0)
                ImageDraw.Draw(mascara).ellipse((0, 0, foto_size - 1, foto_size - 1), fill=255)
                foto.putalpha(mascara)
                
                draw.ellipse(
                    (foto_x - 6, foto_y - 6, foto_x + foto_size + 6, foto_y + foto_size + 6),
                    outline=(*ACENTO_CLARO, 220), width=5
                )
                draw.ellipse(
                    (foto_x - 12, foto_y - 12, foto_x + foto_size + 12, foto_y + foto_size + 12),
                    outline=(*ACENTO, 120), width=2
                )
                lienzo.alpha_composite(foto, (foto_x, foto_y))
            else:
                draw.ellipse(
                    (foto_x, foto_y, foto_x + foto_size, foto_y + foto_size),
                    fill=(*ACENTO, 60), outline=(*ACENTO_CLARO, 100), width=3
                )
        else:
            draw.ellipse(
                (foto_x, foto_y, foto_x + foto_size, foto_y + foto_size),
                fill=(*ACENTO, 60), outline=(*ACENTO_CLARO, 100), width=3
            )

        # Track (GRANDE - protagonista) - subido más arriba
        track = sel["titulo"]
        maximo = card_w - 40
        tam = 26
        while tam > 18:
            caja = draw.textbbox((0, 0), track, font=_fuente(tam))
            if caja[2] - caja[0] <= maximo:
                break
            tam -= 2
        _centrar_texto_en_caja(draw, track, _fuente(tam), card_y + 225, x + 20, card_w - 40, TEXTO)

        # Artista (pequeño, debajo)
        nombre = sel["artista"]
        maximo = card_w - 40
        tam = 18
        while tam > 14:
            caja = draw.textbbox((0, 0), nombre, font=_fuente(tam))
            if caja[2] - caja[0] <= maximo:
                break
            tam -= 2
        _centrar_texto_en_caja(draw, nombre, _fuente(tam), card_y + 270, x + 20, card_w - 40, (*ACENTO_CLARO, 200))

    # Footer MÁS VISIBLE - movido arriba, más grande, color destacado
    footer_y = 630
    # Fondo semi-transparente para el footer
    footer_bg = Image.new("RGBA", (LIENZO[0] - 120, 90), (8, 5, 18, 200))
    draw_footer = ImageDraw.Draw(footer_bg)
    draw_footer.rounded_rectangle(
        (0, 0, LIENZO[0] - 120, 90), radius=16, outline=(*ACENTO_CLARO, 80), width=2
    )
    lienzo.alpha_composite(footer_bg, (60, footer_y - 5))
    
    _centrar_texto(draw, f"{total_tracks} tracks  ·  Actualizada cada lunes", _fuente(26), footer_y + 5, LIENZO[0], (*ACENTO_CLARO, 255))
    _centrar_texto(draw, f"Semana del {fecha}", _fuente(22), footer_y + 40, LIENZO[0], TEXTO)

    # Botón visual "Escuchar en Spotify"
    btn_y = 750
    btn_w = 380
    btn_h = 56
    btn_x = (LIENZO[0] - btn_w) // 2
    # Fondo botón
    draw.rounded_rectangle(
        (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h),
        radius=28, fill=(*ACENTO, 255)
    )
    # Texto botón
    _centrar_texto_en_caja(draw, "🎧 ESCUCHAR EN SPOTIFY", _fuente(22), btn_y + 12, btn_x, btn_w, (255, 255, 255, 255))

    _pegar_monograma(lienzo, 58, 56, 1016)
    draw.text((56 + 58 + 24, 1006), "FRONTERA GRANDE", font=_fuente(34), fill=(255, 255, 255, 255))
    draw.text((LIENZO[0] - 200, 1014), "fronteragrande.mx", font=_fuente(24), fill=(*ACENTO_CLARO, 230))

    PROMOS_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"playlist_semanal_{fecha.replace('-', '')}"
    ruta = PROMOS_DIR / f"{slug}.jpg"
    lienzo.convert("RGB").save(ruta, "JPEG", quality=90, optimize=True)
    return ruta


def _generar_layout_editorial(lienzo, seleccionados_3: list[dict], total_tracks: int, fecha: str, draw=None) -> Path | None:
    """Layout editorial: apilado vertical, estilo revista, foto a la izquierda, info a la derecha."""
    from PIL import Image, ImageDraw
    
    if draw is None:
        draw = ImageDraw.Draw(lienzo)

    # Título grande estilo revista (alineado a la izquierda, con barra lateral)
    _centrar_texto(draw, "DESCUBRIMIENTO SEMANAL", _fuente(64), 50, LIENZO[0], TEXTO)
    # Subtítulo con línea decorativa
    _centrar_texto(draw, "nueva selección del lunes", _fuente(28), 125, LIENZO[0], (*ACENTO_CLARO, 200))
    
    # Línea separadora gruesa
    draw.line(
        [(80, 175), (1000, 175)],
        fill=(*ACENTO, 180),
        width=4
    )
    draw.line(
        [(80, 177), (1000, 177)],
        fill=(*ACENTO_CLARO, 100),
        width=1
    )

    # 3 bloques verticales apilados
    bloque_y = 200
    bloque_h = 240
    gap_v = 25
    foto_size = 180  # más pequeño
    margin_left = 80
    info_x = margin_left + foto_size + 40
    info_w = LIENZO[0] - info_x - 80

    for i, sel in enumerate(seleccionados_3):
        y = bloque_y + i * (bloque_h + gap_v)
        
        # Foto circular grande a la izquierda
        foto_x = margin_left
        foto_y = y + (bloque_h - foto_size) // 2
        
        session = SessionLocal()
        try:
            artista = ArtistRepository(session).por_nombre(sel["artista"])
            foto_url = artista.imagen_perfil if artista else None
        finally:
            session.close()
        
        if foto_url:
            foto = _descargar_imagen(foto_url)
            if foto:
                foto = _recortar_cuadrado(foto, (foto_size, foto_size))
                from PIL import Image, ImageDraw
                mascara = Image.new("L", (foto_size, foto_size), 0)
                ImageDraw.Draw(mascara).ellipse((0, 0, foto_size - 1, foto_size - 1), fill=255)
                foto.putalpha(mascara)
                
                # Doble anillo estilo editorial
                draw.ellipse(
                    (foto_x - 8, foto_y - 8, foto_x + foto_size + 8, foto_y + foto_size + 8),
                    outline=(*ACENTO_CLARO, 200), width=6
                )
                draw.ellipse(
                    (foto_x - 16, foto_y - 16, foto_x + foto_size + 16, foto_y + foto_size + 16),
                    outline=(*ACENTO, 100), width=3
                )
                # Pequeños detalles en el anillo exterior
                for ang in [0, 90, 180, 270]:
                    import math
                    rad = math.radians(ang)
                    cx = foto_x + foto_size // 2 + int((foto_size // 2 + 20) * math.cos(rad))
                    cy = foto_y + foto_size // 2 + int((foto_size // 2 + 20) * math.sin(rad))
                    draw.ellipse(
                        [(cx - 6, cy - 6), (cx + 6, cy + 6)],
                        fill=(*ACENTO_CLARO, 220)
                    )
                
                lienzo.alpha_composite(foto, (foto_x, foto_y))
            else:
                draw.ellipse(
                    (foto_x, foto_y, foto_x + foto_size, foto_y + foto_size),
                    fill=(*ACENTO, 50), outline=(*ACENTO_CLARO, 120), width=4
                )
        else:
            draw.ellipse(
                (foto_x, foto_y, foto_x + foto_size, foto_y + foto_size),
                fill=(*ACENTO, 50), outline=(*ACENTO_CLARO, 120), width=4
            )
        
        # Número grande de posición (estilo revista)
        # Track (GRANDE - protagonista)
        track = sel["titulo"]
        tam = 38
        while tam > 24:
            caja = draw.textbbox((0, 0), track, font=_fuente(tam))
            if caja[2] - caja[0] <= info_w:
                break
            tam -= 2
        draw.text(
            (info_x, y + 20),
            track,
            font=_fuente(tam),
            fill=TEXTO
        )
        
        # Artista (pequeño, debajo)
        nombre = sel["artista"]
        tam = 22
        while tam > 16:
            caja = draw.textbbox((0, 0), nombre, font=_fuente(tam))
            if caja[2] - caja[0] <= info_w:
                break
            tam -= 2
        draw.text(
            (info_x, y + 80),
            nombre,
            font=_fuente(tam),
            fill=(*ACENTO_CLARO, 200)
        )
        
        # Línea decorativa bajo artista
        draw.line(
            [(info_x, y + 120), (info_x + 200, y + 120)],
            fill=(*ACENTO, 180),
            width=3
        )
        
        # Barra de progreso visual (decorativa)
        draw.rounded_rectangle(
            [(info_x, y + 185), (info_x + 300, y + 195)],
            radius=5, fill=(*ACENTO, 60)
        )
        # Progreso aleatorio
        import hashlib
        prog_seed = int(hashlib.sha256(f"{sel['artista']}{fecha}".encode()).hexdigest(), 16) % 100
        prog_w = int(300 * prog_seed / 100)
        draw.rounded_rectangle(
            [(info_x, y + 185), (info_x + prog_w, y + 195)],
            radius=5, fill=(*ACENTO_CLARO, 255)
        )

# Footer estilo editorial - MÁS VISIBLE
    footer_y = 890
    # Fondo semi-transparente
    footer_bg = Image.new("RGBA", (LIENZO[0] - 160, 80), (8, 5, 18, 200))
    draw_footer = ImageDraw.Draw(footer_bg)
    draw_footer.rounded_rectangle(
        (0, 0, LIENZO[0] - 160, 80), radius=16, outline=(*ACENTO_CLARO, 80), width=2
    )
    lienzo.alpha_composite(footer_bg, (80, footer_y - 10))
    
    _centrar_texto(draw, f"{total_tracks} tracks  ·  actualizada cada lunes  ·  semana del {fecha}", 
                   _fuente(26), footer_y + 10, LIENZO[0], (*ACENTO_CLARO, 255))
    
    # CTA minimalista
    draw.text(
        (80, footer_y + 50),
        "▶  escuchar en spotify",
        font=_fuente(26),
        fill=(*ACENTO_CLARO, 255)
    )
    
    # Flecha
    draw.polygon(
        [(380, footer_y + 56), (396, footer_y + 66), (380, footer_y + 76)],
        fill=(*ACENTO_CLARO, 255)
    )

    # Marca FG
    _pegar_monograma(lienzo, 58, 56, 1016)
    draw.text((56 + 58 + 24, 1006), "FRONTERA GRANDE", font=_fuente(34), fill=(255, 255, 255, 255))
    draw.text((LIENZO[0] - 200, 1014), "fronteragrande.mx", font=_fuente(24), fill=(*ACENTO_CLARO, 230))

    PROMOS_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"playlist_semanal_{fecha.replace('-', '')}"
    ruta = PROMOS_DIR / f"{slug}.jpg"
    lienzo.convert("RGB").save(ruta, "JPEG", quality=90, optimize=True)
    return ruta


def generar_tarjeta_playlist(seleccionados_3: list[dict], total_tracks: int, fecha: str) -> Path | None:
    """Genera la tarjeta 1080x1080 con 3 artistas — diseño EDITORIAL (vertical apilado)."""
    from PIL import Image, ImageDraw
    
    # Elegir diseño aleatorio pero estable por semana
    import hashlib
    semilla = int(hashlib.sha256(fecha.encode()).hexdigest(), 16)
    usar_editorial = (semilla % 2) == 0  # 50% cada uno
    
    if usar_editorial:
        lienzo = _fondo_playlist_editorial()
        return _generar_layout_editorial(lienzo, seleccionados_3, total_tracks, fecha, draw=None)
    else:
        lienzo = _fondo_playlist()
        return _generar_layout_cards(lienzo, seleccionados_3, total_tracks, fecha, draw=None)


def construir_copy_fb(datos: dict) -> str:
    """Construye el mensaje para Facebook."""
    sel = datos["seleccionados_3"]
    lines = [
        "Cada lunes, una selección fresca de la escena musical de la frontera",
        "norte de Tamaulipas y el Valle de Texas.",
        "",
        f'Esta semana en "Frontera Grande: Descubrimiento Semanal" suenan:',
    ]
    for s in sel:
        lines.append(f'{s["titulo"]} — {s["artista"]}')
    lines.append(f'... y {datos["total_tracks"] - 3} temas más.')
    lines.append("")
    lines.append(f'🎧 Escucha y sigue la playlist:')
    lines.append(datos["playlist_url"])
    lines.append("")
    lines.append("La rotación cambia cada lunes. ¿Tu proyecto ya tiene Spotify?")
    lines.append("Regístralo en fronteragrande.mx y puede rotar la próxima semana.")
    lines.append("")
    lines.append("#FronteraGrande #EscenaLocal #DescubrimientoSemanal")
    return "\n".join(lines)


def construir_copy_ig(datos: dict) -> str:
    """Construye el caption para Instagram con menciones @handle."""
    sel = datos["seleccionados_3"]
    lines = [
        "Nueva semana, nuevos sonidos de la frontera 🎵",
        "",
        'Esta semana en "Frontera Grande: Descubrimiento Semanal":',
    ]
    menciones = []
    for s in sel:
        lines.append(f'{s["titulo"]} — {s["artista"]}')
        if s.get("handle_ig"):
            menciones.append(f"@{s['handle_ig']}")
    lines.append(f'... y {datos["total_tracks"] - 3} tracks más de la escena.')
    lines.append("")
    lines.append("🎧 Escucha completa: " + datos["playlist_url"])
    lines.append("👉 Síguela para que no te pierdas la rotación del próximo lunes.")
    lines.append("")
    if menciones:
        lines.append(" ".join(menciones))
    lines.append("")
    hashtags = [
        "#FronteraGrande", "#DescubrimientoSemanal", "#EscenaLocal",
        "#MusicaIndependiente", "#Tamaulipas", "#ValleDeTexas",
        "#Reynosa", "#Matamoros", "#NuevoLaredo", "#McAllen", "#Brownsville"
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
        datos["seleccionados_3"], datos["total_tracks"], datos["fecha"]
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
        imagen_url = f"{api_public_url}/api/promos/{slug}.jpg"
        imagen_url_jpg = imagen_url  # mismo archivo JPEG

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