#!/usr/bin/env python3
"""Genera tarjetas de tips para redes sociales con Pillow.

Uso:
    python scripts/generar_tarjeta_tip.py
    python scripts/generar_tarjeta_tip.py --formato story

Salida en carrousel/tips/
"""
import argparse
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "carrousel", "tips")

# Paleta
BG = "#0b0b10"
SURFACE = "#14141b"
ACCENT = "#9d4edd"
ACCENT_SOFT = "#2a1a33"
TEXT = "#ececf1"
MUTED = "#8a8a9a"
LINE = "#262633"

# Fuentes
TTF_ANTON = os.path.expanduser("~/.local/share/fonts/carrusel/Anton-Regular.ttf")
TTF_SPACE = os.path.expanduser("~/.local/share/fonts/carrusel/SpaceGrotesk.ttf")
TTF_ARCHIVO = os.path.expanduser("~/.local/share/fonts/ArchivoBlack-Regular.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


def draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def slide_gancho(W, H):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Barra decorativa superior
    draw.rectangle([0, 0, W, 8], fill=ACCENT)

    # Badge "TIP PARA ARTISTAS"
    badge_font = font(TTF_SPACE, 28)
    badge_text = "TIP PARA ARTISTAS"
    bw = badge_font.getlength(badge_text) + 40
    bx = (W - bw) / 2
    by = 140
    draw_rounded_rect(draw, (bx, by, bx + bw, by + 52), 26, ACCENT_SOFT)
    draw.text((bx + 20, by + 8), badge_text, font=badge_font, fill=ACCENT)

    # Título principal
    title_font = font(TTF_ANTON, 72)
    line1 = "¿TU CUENTA DE"
    line2 = "INSTAGRAM"
    line3 = "ES PROFESIONAL?"

    # Centrar cada línea
    for text, y_offset in [(line1, 260), (line2, 340), (line3, 420)]:
        tw = title_font.getlength(text)
        draw.text(((W - tw) / 2, y_offset), text, font=title_font, fill=TEXT)

    # Subtítulo
    sub_font = font(TTF_SPACE, 34)
    sub = "Por qué importa para tu música"
    sw = sub_font.getlength(sub)
    draw.text(((W - sw) / 2, 540), sub, font=sub_font, fill=MUTED)

    # Línea decorativa
    draw.rectangle([W // 2 - 40, 610, W // 2 + 40, 614], fill=ACCENT)

    # Logo FG (texto)
    logo_font = font(TTF_ARCHIVO, 36)
    logo_text = "FRONTERA GRANDE"
    lw = logo_font.getlength(logo_text)
    draw.text(((W - lw) / 2, H - 120), logo_text, font=logo_font, fill=MUTED)

    # Dominio
    dom_font = font(TTF_SPACE, 24)
    dom = "FRONTERAGRANDE.MX"
    dw = dom_font.getlength(dom)
    draw.text(((W - dw) / 2, H - 70), dom, font=dom_font, fill=ACCENT)

    return img


def slide_beneficios(W, H):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Barra decorativa superior
    draw.rectangle([0, 0, W, 8], fill=ACCENT)

    # Título
    title_font = font(TTF_ANTON, 52)
    title = "BENEFICIOS DE"
    title2 = "CUENTA PROFESIONAL"
    tw1 = title_font.getlength(title)
    tw2 = title_font.getlength(title2)
    draw.text(((W - tw1) / 2, 100), title, font=title_font, fill=TEXT)
    draw.text(((W - tw2) / 2, 165), title2, font=title_font, fill=ACCENT)

    # Beneficios
    beneficios = [
        ("📊", "Estadísticas reales", "Quién ve tu contenido,\nde dónde son, cuándo conectan"),
        ("📞", "Botón de contacto", "Que te llamen, escriban\no manden email directo"),
        ("📅", "Programar posts", "Publica cuando tu\naudiencia esté en línea"),
        ("🔍", "Aparecer en recommends", "El algoritmo favorece\ncuentas profesionales"),
    ]

    y_start = 280
    spacing = 170
    left_margin = 100

    num_font = font(TTF_ANTON, 48)
    title_f = font(TTF_SPACE, 34)
    desc_f = font(TTF_SPACE, 24)

    for i, (emoji, titulo, desc) in enumerate(beneficios):
        y = y_start + i * spacing

        # Número circular
        cx, cy = left_margin, y + 40
        draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=ACCENT_SOFT)
        num_text = str(i + 1)
        num_w = num_font.getlength(num_text)
        draw.text((cx - num_w / 2, cy - 22), num_text, font=num_font, fill=ACCENT)

        # Texto
        text_x = left_margin + 60
        draw.text((text_x, y), titulo, font=title_f, fill=TEXT)
        draw.text((text_x, y + 44), desc, font=desc_f, fill=MUTED)

        # Separador
        if i < len(beneficios) - 1:
            draw.rectangle(
                [left_margin, y + spacing - 15, W - left_margin, y + spacing - 13],
                fill=LINE,
            )

    # CTA
    cta_font = font(TTF_SPACE, 28)
    cta = "Toma 2 minutos · No pierdes nada"
    cw = cta_font.getlength(cta)
    draw.text(((W - cw) / 2, H - 140), cta, font=cta_font, fill=TEXT)

    # Logo FG
    logo_font = font(TTF_ARCHIVO, 28)
    logo_text = "FRONTERA GRANDE"
    lw = logo_font.getlength(logo_text)
    draw.text(((W - lw) / 2, H - 80), logo_text, font=logo_font, fill=MUTED)

    # Dominio
    dom_font = font(TTF_SPACE, 22)
    dom = "FRONTERAGRANDE.MX"
    dw = dom_font.getlength(dom)
    draw.text(((W - dw) / 2, H - 40), dom, font=dom_font, fill=ACCENT)

    return img


def main():
    parser = argparse.ArgumentParser(description="Genera tarjeta de tip para RRSS")
    parser.add_argument(
        "--formato",
        choices=["cuadrado", "story"],
        default="cuadrado",
        help="Formato de salida (default: cuadrado 1080x1080)",
    )
    args = parser.parse_args()

    os.makedirs(OUT, exist_ok=True)

    formatos = {
        "cuadrado": (1080, 1080),
        "story": (1080, 1920),
    }
    W, H = formatos[args.formato]

    slides = [
        ("04-cuentas-profesionales-gancho", slide_gancho),
        ("04-cuentas-profesionales-beneficios", slide_beneficios),
    ]

    for name, builder in slides:
        img = builder(W, H)
        path = os.path.join(OUT, f"{name}.png")
        img.save(path, "PNG")
        print(f"  → {path}")

    print(f"OK: {len(slides)} tarjetas en {OUT}")


if __name__ == "__main__":
    main()
