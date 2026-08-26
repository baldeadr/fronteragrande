"""Publicación automática de bienvenida en la página de Frontera Grande.

Cuando un artista verifica su perfil (conecta su página FB/IG), se publica
en la página oficial un post con **tarjeta promocional generada** (foto del
artista con marco de marca FG) etiquetando al artista para darle visibilidad.

La tarjeta se genera con Pillow al vuelo, se guarda en `instance/promos/`
y se sirve públicamente vía `GET /api/promos/{slug}.png`; Facebook la descarga
de esa URL al crear el post (`POST /{page_id}/photos` con `url` + `caption`).
"""

import logging
import os
import hashlib
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from db.models import Artist, PromoPost

logger = logging.getLogger(__name__)

API_VERSION = os.getenv("META_API_VERSION", "v22.0")
FG_PAGE_ID = os.getenv("FG_PAGE_ID", "")
FG_PAGE_TOKEN = os.getenv("FG_PAGE_TOKEN", "")
PROMO_AUTO_PUBLISH = os.getenv("PROMO_AUTO_PUBLISH", "false").lower() == "true"
PROMO_IG = os.getenv("PROMO_IG", "false").lower() == "true"
WEB_URL = os.getenv("WEB_URL", "https://fronteragrande.mx")
RUTA_MONOGRAMA = Path(__file__).resolve().parent.parent / "web" / "public" / "assets" / "monograma_fg.png"
_MONO_CACHE: dict = {}
API_PUBLIC_URL = os.getenv("API_PUBLIC_URL", "").rstrip("/")
GRAF_API = f"https://graph.facebook.com/{API_VERSION}"

RAIZ = Path(__file__).resolve().parent.parent
FUENTE_PATH = RAIZ / "web/public/fonts/ArchivoBlack-Regular.ttf"
PROMOS_DIR = RAIZ / "instance/promos"

BG = "#0b0b10"
ACENTO = (157, 78, 221)        # #9d4edd
ACENTO_CLARO = (224, 170, 255)  # #e0aaff
VIOLETA = (123, 44, 191)       # #7b2cbf (tope del degradado)
TEXTO = "#ffffff"

LIENZO = (1080, 1080)


def promo_configurado() -> bool:
    """True si están configuradas las credenciales de la página FG."""
    return bool(FG_PAGE_ID and FG_PAGE_TOKEN)


def _obtener_enlaces_artista(artista: Artist) -> dict[str, str]:
    """Extrae URLs de FB e IG del artista para mencionar en el post."""
    enlaces = {"fb": "", "ig": ""}
    for link in artista.links:
        if link.plataforma == "fb" and link.url:
            enlaces["fb"] = link.url.strip()
        elif link.plataforma == "ig" and link.url:
            enlaces["ig"] = link.url.strip()
    return enlaces


def _extraer_username_fb(url: str) -> str:
    """Extrae el username o ID de una URL de Facebook."""
    url = url.rstrip("/")
    if "profile.php?id=" in url:
        return url.split("id=")[-1].split("&")[0]
    return url.rsplit("/", 1)[-1]


def _extraer_username_ig(url: str) -> str:
    """Extrae el username de una URL de Instagram."""
    return url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]


def _dato_real(valor: str | None) -> str:
    """Texto utilizable del dato: vacío si falta o es el marcador [PENDIENTE]."""
    texto = (valor or "").strip()
    return "" if texto.lower() == "[pendiente]" else texto


def _construir_mensaje(artista: Artist, enlaces: dict[str, str]) -> str:
    """Construye el mensaje del post de bienvenida."""
    lineas = [
        "🎵 ¡Nuevo artista verificado en Frontera Grande!",
        "",
        f"Bienvenid@ {artista.nombre} a la escena musical de la frontera grande de Tamaulipas.",
        "",
        f"🔗 Escúchalo y sígelo en: {WEB_URL}/artistas/{artista.slug}",
        "",
        "#FronteraGrande #EscenaLocal #Tamaulipas #MúsicaIndependiente",
    ]
    ficha = " · ".join(
        p for p in (
            _dato_real(getattr(artista, "segmento", None)),
            _dato_real(getattr(artista, "ciudad", None)),
            _dato_real(artista.generos),
        ) if p
    )
    if ficha:
        lineas.insert(4, f"🎸 {ficha}")
    handles: list[str] = []
    if enlaces.get("fb"):
        handles.append(_extraer_username_fb(enlaces["fb"]))
    if enlaces.get("ig"):
        usuario_ig = _extraer_username_ig(enlaces["ig"])
        if usuario_ig.lower() not in [h.lower() for h in handles]:
            handles.append(usuario_ig)
    menciones = [f"@{h}" for h in handles]
    if menciones:
        lineas.insert(2, " ".join(menciones))
    return "\n".join(lineas)


# ---------------------------------------------------------------- imágenes


def _descargar_imagen(url: str) -> Image.Image | None:
    """Descarga una imagen desde URL; None si falla."""
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except Exception as exc:
        logger.warning("No se pudo descargar la foto %s: %s", url, exc)
        return None


def _recortar_cuadrado(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Recorta al cuadrado centrado y redimensiona."""
    w, h = img.size
    if w != h:
        lado = min(w, h)
        img = img.crop(((w - lado) // 2, (h - lado) // 2,
                        (w + lado) // 2, (h + lado) // 2))
    return img.resize(size, Image.Resampling.LANCZOS)


def _esquinas_redondeadas(img: Image.Image, radio: int = 56) -> Image.Image:
    """Aplica máscara de esquinas redondeadas (estilo squircle moderno)."""
    mascara = Image.new("L", img.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle(
        (0, 0, img.size[0] - 1, img.size[1] - 1), radius=radio, fill=255
    )
    salida = img.copy()
    salida.putalpha(mascara)
    return salida


def _fuente(tamano: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Carga Archivo Black (fallback a la fuente por defecto)."""
    try:
        return ImageFont.truetype(str(FUENTE_PATH), tamano)
    except Exception:
        return ImageFont.load_default()


def _centrar_texto(draw: ImageDraw.ImageDraw, texto: str, fuente, y: int,
                   lienzo_ancho: int, color, sombra: str = "#00000090") -> int:
    """Dibuja texto centrado con sombra sutil; devuelve la altura usada."""
    caja = draw.textbbox((0, 0), texto, font=fuente)
    ancho = caja[2] - caja[0]
    alto = caja[3] - caja[1]
    x = (lienzo_ancho - ancho) // 2
    draw.text((x + 3, y + 3), texto, font=fuente, fill=sombra)
    draw.text((x, y), texto, font=fuente, fill=color)
    return alto


def _fondo_gradiente(size: tuple[int, int]) -> Image.Image:
    """Degradado diagonal violeta→negro (identidad FG, vibrante en feed)."""
    tope = Image.new("RGB", size, VIOLETA)
    base = Image.new("RGB", size, BG)
    grad = Image.linear_gradient("L").rotate(135, expand=True).resize(size)
    return Image.composite(tope, base, grad).convert("RGBA")


def _brillo_radial(size: tuple[int, int], centro: tuple[int, int],
                   radio: int, color: tuple[int, int, int], alpha: int,
                   desenfoque: int) -> Image.Image:
    """Halo suave (neón) para hacer resaltar la foto sobre el fondo."""
    capa = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(capa).ellipse(
        (centro[0] - radio, centro[1] - radio,
         centro[0] + radio, centro[1] + radio),
        fill=(*color, alpha),
    )
    return capa.filter(ImageFilter.GaussianBlur(desenfoque))


def _estrella(draw: ImageDraw.ImageDraw, x: float, y: float, r: int,
              color) -> None:
    """Estrella de 4 puntas (destello decorativo)."""
    k = 0.22 * r
    draw.polygon(
        [(x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k),
         (x, y + r), (x - k, y + k), (x - r, y), (x - k, y - k)],
        fill=color,
    )


def _ecualizador(lienzo: Image.Image) -> None:
    """Barras tipo ecualizador al pie (señal musical, muy tenues)."""
    capa = Image.new("RGBA", LIENZO, (0, 0, 0, 0))
    draw = ImageDraw.Draw(capa)
    alturas = [46, 92, 60, 130, 84, 160, 70, 118, 52, 142,
               88, 58, 126, 74, 156, 64, 108, 48, 134, 80]
    ancho_barra, hueco = 18, 14
    total = len(alturas) * (ancho_barra + hueco) - hueco
    x = (LIENZO[0] - total) // 2
    for i, h in enumerate(alturas):
        alpha = 34 if i % 2 else 52
        draw.rounded_rectangle(
            [x, 1078 - h, x + ancho_barra, 1078],
            radius=8, fill=(*ACENTO_CLARO, alpha),
        )
        x += ancho_barra + hueco
    lienzo.alpha_composite(capa)


def _generos_cortos(generos: str, maximo: int = 3) -> str:
    """Primeros géneros separados por ' · ' para la línea bajo el nombre."""
    partes = [
        g.strip()
        for g in (generos or "").split(",")
        if g.strip() and g.strip().lower() != "[pendiente]"
    ]
    return " · ".join(partes[:maximo])


# ----------------------------------------------------- variantes de tarjeta

NUM_VARIANTES = 4


def _variante_de(slug: str) -> int:
    """Variante estable por artista (sha256 del slug): el mismo slug regenera
    siempre la misma tarjeta — Facebook descarga la imagen desde la URL."""
    digesto = hashlib.sha256(slug.encode("utf-8")).hexdigest()
    return int(digesto, 16) % NUM_VARIANTES


def _fondo_variante(variante: int) -> Image.Image:
    """Fondo según variante: 0 neón diagonal · 1 bloque geométrico
    · 2 aura con ondas · 3 doppler en oscuro."""
    if variante == 1:
        lienzo = Image.new("RGBA", LIENZO, "#100024")
        ImageDraw.Draw(lienzo).polygon(
            [(0, 0), (1080, 0), (0, 1080)], fill=(*VIOLETA, 255)
        )
        lienzo.alpha_composite(
            _brillo_radial(LIENZO, (850, 850), 280, ACENTO_CLARO, 90, 120)
        )
    elif variante == 2:
        lienzo = Image.new("RGBA", LIENZO, "#15002e")
        lienzo.alpha_composite(
            _brillo_radial(LIENZO, (540, 480), 540, ACENTO_CLARO, 80, 180)
        )
        lienzo.alpha_composite(
            _brillo_radial(LIENZO, (540, 470), 300, ACENTO, 130, 130)
        )
        # Ondas concéntricas alrededor de la foto: la firma gráfica de esta
        # variante (aura de sonido expandiéndose desde el artista).
        ondas = ImageDraw.Draw(lienzo)
        cx_o, cy_o = 540, 455
        for i, (radio, alfa) in enumerate([(318, 95), (376, 65), (434, 42), (496, 22)]):
            ondas.ellipse(
                (cx_o - radio, cy_o - radio, cx_o + radio, cy_o + radio),
                outline=(*ACENTO_CLARO, alfa),
                width=4 if i == 0 else 3,
            )
    elif variante == 3:
        # Doble Doppler en oscuro plano: dos fuentes puntuales visibles
        # (arriba a la izquierda y abajo a la derecha) emiten frentes
        # comprimidos hacia la foto y estirados hacia su espalda; los
        # recorridos se cruzan sobre el artista. Sin difuminados: solo
        # puntos, arcos de doble paso y negro puro.
        lienzo = Image.new("RGBA", LIENZO, "#070512")
        ondas = ImageDraw.Draw(lienzo)

        def _emisor(cx_e: int, cy_e: int, hacia: int,
                    frentes_c: list[int], frentes_e: list[int]) -> None:
            """Fuente puntual: comprimidos hacia 'hacia', estiros detrás.

            Los arcos van en violeta profundo (ACENTO), no lavanda, para que
            el subtítulo del artista (lavanda claro) no se pierda entre ellos.
            """
            ondas.ellipse(
                (cx_e - 10, cy_e - 10, cx_e + 10, cy_e + 10),
                fill=(255, 255, 255, 235),
            )
            for i, radio in enumerate(frentes_c):
                caja = (cx_e - radio, cy_e - radio, cx_e + radio, cy_e + radio)
                base = 185 - i * 22
                ondas.arc(caja, start=hacia - 75, end=hacia + 75,
                          fill=(*ACENTO, max(30, base // 3)), width=8)
                ondas.arc(caja, start=hacia - 75, end=hacia + 75,
                          fill=(*ACENTO, base), width=4 if i == 0 else 3)
            for i, radio in enumerate(frentes_e):
                caja = (cx_e - radio, cy_e - radio, cx_e + radio, cy_e + radio)
                base = 145 - i * 40
                ondas.arc(caja, start=hacia + 125, end=hacia + 235,
                          fill=(*ACENTO, max(24, base // 3)), width=6)
                ondas.arc(caja, start=hacia + 125, end=hacia + 235,
                          fill=(*ACENTO, base), width=3)

        _emisor(150, 150, 40, [130, 165, 200, 235, 270], [105, 180])
        _emisor(930, 930, 228, [130, 165, 200, 235, 270], [105, 180])
    else:
        lienzo = _fondo_gradiente(LIENZO)
        lienzo.alpha_composite(
            _brillo_radial(LIENZO, (540, 445), 330, ACENTO, 150, 110)
        )
        lienzo.alpha_composite(
            _brillo_radial(LIENZO, (760, 300), 170, ACENTO_CLARO, 70, 90)
        )
        lienzo.alpha_composite(
            _brillo_radial(LIENZO, (280, 640), 150, ACENTO_CLARO, 55, 90)
        )
        _ecualizador(lienzo)
    return lienzo


_DESTELLOS = {
    0: [(180, 200, 16, 200), (905, 175, 12, 170), (875, 700, 18, 150),
        (165, 640, 11, 170), (985, 430, 10, 140)],
    1: [(950, 120, 14, 190), (120, 930, 12, 170), (985, 690, 10, 150),
        (70, 420, 11, 160)],
    2: [(215, 470, 15, 190), (865, 470, 15, 190), (540, 145, 13, 180),
        (540, 795, 11, 150)],
    3: [(1000, 95, 11, 150), (70, 720, 9, 120)],
}


def _destellos(draw: ImageDraw.ImageDraw, variante: int) -> None:
    for sx, sy, sr, sa in _DESTELLOS.get(variante, _DESTELLOS[0]):
        _estrella(draw, sx, sy, sr, (*ACENTO_CLARO, sa))


def _poner_foto(lienzo: Image.Image, draw: ImageDraw.ImageDraw,
                foto: Image.Image, fy: int, tam: int,
                marco_doble: bool = True) -> None:
    """Foto cuadrada con esquinas redondeadas, centrada, con marco(s)."""
    fx = (LIENZO[0] - tam) // 2
    escala = tam / 560
    sq = _recortar_cuadrado(foto, (tam, tam))
    lista = _esquinas_redondeadas(sq, radio=int(56 * escala))
    lienzo.paste(lista, (fx, fy), lista)
    if marco_doble:
        draw.rounded_rectangle(
            (fx - 14, fy - 14, fx + tam + 14, fy + tam + 14),
            radius=int(70 * escala),
            outline=(255, 255, 255, 255), width=12,
        )
        draw.rounded_rectangle(
            (fx - 30, fy - 30, fx + tam + 30, fy + tam + 30),
            radius=int(84 * escala),
            outline=(*ACENTO_CLARO, 220), width=4,
        )
    else:
        draw.rounded_rectangle(
            (fx - 12, fy - 12, fx + tam + 12, fy + tam + 12),
            radius=int(66 * escala),
            outline=(255, 255, 255, 255), width=10,
        )


def _badge(draw: ImageDraw.ImageDraw, by_top: int = 62,
           invertido: bool = False) -> None:
    """Píldora 'NUEVO ARTISTA VERIFICADO'; en v2 va en blanco con texto FG."""
    texto = "NUEVO ARTISTA VERIFICADO"
    fuente = _fuente(30)
    caja = draw.textbbox((0, 0), texto, font=fuente)
    bw = caja[2] - caja[0]
    bx = (LIENZO[0] - bw) // 2
    by_bottom = by_top + 66
    if invertido:
        draw.rounded_rectangle(
            [bx - 36, by_top, bx + bw + 36, by_bottom], radius=33,
            fill=(255, 255, 255, 255), outline=(*ACENTO, 255), width=3,
        )
        color = (*ACENTO, 255)
    else:
        draw.rounded_rectangle(
            [bx - 36, by_top, bx + bw + 36, by_bottom], radius=33,
            fill=ACENTO, outline=(255, 255, 255, 255), width=3,
        )
        color = (255, 255, 255, 255)
    by_texto = by_top + (by_bottom - by_top - (caja[3] - caja[1])) // 2 - caja[1]
    draw.text((bx, by_texto), texto, font=fuente, fill=color)


def _nombre_sublinea(draw: ImageDraw.ImageDraw, artista: Artist,
                     y_nombre: int, tam_max: int = 104) -> None:
    """Nombre gigante ajustado al ancho + línea ciudad · géneros."""
    nombre = artista.nombre.upper()
    maximo = LIENZO[0] - 100
    tam = tam_max
    while tam > 44:
        caja = draw.textbbox((0, 0), nombre, font=_fuente(tam))
        if caja[2] - caja[0] <= maximo:
            break
        tam -= 4
    alto = _centrar_texto(draw, nombre, _fuente(tam), y_nombre, LIENZO[0], TEXTO)
    sublinea = " · ".join(
        p for p in (_dato_real(artista.ciudad), _generos_cortos(artista.generos)) if p
    )
    if sublinea:
        _centrar_texto(draw, sublinea, _fuente(32),
                       y_nombre + alto + 26, LIENZO[0], (*ACENTO_CLARO, 235))


# Composición por variante: foto SIEMPRE igual (fy, tam, y_nombre comunes);
# cambia marco, posición del badge y tamaño máximo del nombre.
_LAYOUTS = {
    0: dict(fy=170, tam=570, doble=True, badge_y=62, inv=False, y_nom=775, tmax=100),
    1: dict(fy=170, tam=570, doble=True, badge_y=62, inv=True, y_nom=775, tmax=100),
    2: dict(fy=170, tam=570, doble=False, badge_y=62, inv=True, y_nom=775, tmax=100),
    3: dict(fy=170, tam=570, doble=False, badge_y=62, inv=False, y_nom=775, tmax=100),
}


def _mono_imagen() -> Image.Image | None:
    """Monograma FG real (asset blanco transparente extraído del logo)."""
    if "img" not in _MONO_CACHE and RUTA_MONOGRAMA.exists():
        _MONO_CACHE["img"] = Image.open(RUTA_MONOGRAMA).convert("RGBA")
    return _MONO_CACHE.get("img")


def _mono_ancho(alto: int) -> int:
    mono = _mono_imagen()
    if mono is None:
        return 0
    return int(mono.size[0] * alto / mono.size[1])


def _pegar_monograma(lienzo: Image.Image, alto: int, x: int, y_eje: int,
                     tinto: tuple[int, int, int] | None = None) -> None:
    """Pega el monograma FG centrado en 'y_eje'; tinto opcional (RGB)."""
    mono = _mono_imagen()
    if mono is None:
        return
    w = _mono_ancho(alto)
    recorte = mono.resize((w, alto), Image.LANCZOS)
    if tinto:
        lav = Image.new("RGBA", recorte.size, (*tinto, 255))
        lav.putalpha(recorte.getchannel("A"))
        recorte = lav
    lienzo.alpha_composite(recorte, (int(x), int(y_eje - alto / 2)))


def _barra_marca(lienzo: Image.Image, draw: ImageDraw.ImageDraw,
                 variante: int) -> None:
    """Firma de marca al pie; la composición cambia por variante.

    v0: monograma a la izquierda + nombre, dominio a la derecha.
    v1: una sola línea centrada 'FG · FRONTERA GRANDE · dominio'.
    v2: dominio a la izquierda, nombre y monograma a la derecha.
    v3: cápsula centrada con el monograma + nombre + dominio.

    El monograma es el asset real del logo; los anchos siempre se miden.
    """
    dominio = WEB_URL.replace("https://", "").replace("http://", "").rstrip("/")
    f_dom = _fuente(24)
    dw = draw.textlength(dominio, font=f_dom)
    y_eje = 1022

    if variante == 1:
        texto = f"FRONTERA GRANDE   ·   {dominio}"
        f_marca = _fuente(28)
        tw = draw.textlength(texto, font=f_marca)
        fg_w = _mono_ancho(58)
        x = (LIENZO[0] - (fg_w + 24 + tw)) // 2
        _pegar_monograma(lienzo, 58, x, y_eje)
        draw.text((x + fg_w + 24, y_eje), texto, font=f_marca,
                  fill=(255, 255, 255, 255), anchor="lm")
    elif variante == 2:
        draw.text((56, y_eje), dominio, font=f_dom,
                  fill=(*ACENTO_CLARO, 230), anchor="lm")
        f_marca = _fuente(34)
        texto = "FRONTERA GRANDE"
        tw = draw.textlength(texto, font=f_marca)
        fg_w = _mono_ancho(58)
        mx = LIENZO[0] - 56 - fg_w
        _pegar_monograma(lienzo, 58, mx, y_eje - 2)
        draw.text((mx - 24 - tw, y_eje), texto, font=f_marca,
                  fill=(255, 255, 255, 255), anchor="lm")
    elif variante == 3:
        texto = f"FRONTERA GRANDE   ·   {dominio}"
        f_marca = _fuente(26)
        tw = draw.textlength(texto, font=f_marca)
        fg_w = _mono_ancho(54)
        alto_p = 72
        ancho_p = int(fg_w + 20 + tw + 68)
        x0, y0 = (LIENZO[0] - ancho_p) // 2, 988
        draw.rounded_rectangle(
            [x0, y0, x0 + ancho_p, y0 + alto_p],
            radius=alto_p // 2,
            fill=(10, 7, 24, 150),
            outline=(*ACENTO_CLARO, 120),
            width=2,
        )
        _pegar_monograma(lienzo, 54, x0 + 34, y0 + alto_p / 2)
        draw.text((x0 + 34 + fg_w + 20, y0 + alto_p / 2), texto,
                  font=f_marca, fill=(255, 255, 255, 245), anchor="lm")
    else:
        mw = _mono_ancho(64)
        _pegar_monograma(lienzo, 64, 56, 1016)
        f_marca = _fuente(34)
        draw.text((56 + mw + 24, 1006), "FRONTERA GRANDE",
                  font=f_marca, fill=(255, 255, 255, 255))
        draw.text((LIENZO[0] - dw - 56, 1014), dominio,
                  font=f_dom, fill=(*ACENTO_CLARO, 230))


def generar_imagen_promo(artista: Artist, variante: int | None = None) -> Path | None:
    """Genera la tarjeta promocional 1080×1080 del artista.

    Sistema de variantes para evitar monotonía en el feed: misma identidad
    (tipografía, badge, barra de marca) con cuatro composiciones de fondo,
    layout y firma inferior. La variante se elige por hash del slug si no
    se fuerza. Devuelve la ruta del PNG o None si no hay foto descargable.
    """
    if not artista.imagen_perfil:
        return None
    foto = _descargar_imagen(artista.imagen_perfil)
    if foto is None:
        return None

    v = _variante_de(artista.slug) if variante is None else variante % NUM_VARIANTES
    cfg = _LAYOUTS[v]

    lienzo = _fondo_variante(v)
    draw = ImageDraw.Draw(lienzo)
    _destellos(draw, v)

    _poner_foto(lienzo, draw, foto, cfg["fy"], cfg["tam"], cfg["doble"])
    _badge(draw, cfg["badge_y"], cfg["inv"])
    _nombre_sublinea(draw, artista, cfg["y_nom"], cfg["tmax"])
    _barra_marca(lienzo, draw, v)

    PROMOS_DIR.mkdir(parents=True, exist_ok=True)
    ruta = PROMOS_DIR / f"{artista.slug}.png"
    lienzo.convert("RGB").save(ruta, "PNG", optimize=True)
    # Instagram exige JPEG para contenedores de imagen: se guarda gemelo.
    ruta_jpg = PROMOS_DIR / f"{artista.slug}.jpg"
    lienzo.convert("RGB").save(ruta_jpg, "JPEG", quality=90, optimize=True)
    return ruta


def imagen_promo_url(slug: str) -> str | None:
    """URL pública de la tarjeta promocional (la API debe ser accesible)."""
    if not API_PUBLIC_URL:
        return None
    return f"{API_PUBLIC_URL}/api/promos/{slug}.png"


# ---------------------------------------------------------------- publicación


def publicar_en_fb(mensaje: str, imagen_url: str | None = None) -> dict:
    """Publica en la página FG: foto con caption si hay imagen, texto si no.

    Returns:
        dict con 'ok', 'post_id' o 'error'.
    """
    if not promo_configurado():
        return {"ok": False, "error": "FG_PAGE_ID o FG_PAGE_TOKEN no configurados"}
    try:
        if imagen_url:
            r = requests.post(
                f"{GRAF_API}/{FG_PAGE_ID}/photos",
                data={
                    "access_token": FG_PAGE_TOKEN,
                    "url": imagen_url,
                    "caption": mensaje,
                    "published": "true" if PROMO_AUTO_PUBLISH else "false",
                },
                timeout=60,
            )
        else:
            r = requests.post(
                f"{GRAF_API}/{FG_PAGE_ID}/feed",
                data={
                    "access_token": FG_PAGE_TOKEN,
                    "message": mensaje,
                    "published": "true" if PROMO_AUTO_PUBLISH else "false",
                },
                timeout=30,
            )
        r.raise_for_status()
        resp = r.json()
        if "id" in resp:
            return {"ok": True, "post_id": resp["id"]}
        if "error" in resp:
            return {"ok": False, "error": resp["error"].get("message", "Error de Meta")}
        return {"ok": False, "error": "Respuesta inesperada de Meta"}
    except requests.RequestException as exc:
        return {"ok": False, "error": f"Error de red: {exc}"}


_IG_FG_CACHE: dict[str, str | None] = {}


def _ig_de_fg() -> str | None:
    """ID de la cuenta de Instagram de la página FG (None si no hay).

    Se consulta una sola vez por proceso y se cachea: la vinculación no
    cambia durante la vida del servicio.
    """
    if not promo_configurado():
        return None
    if "id" in _IG_FG_CACHE:
        return _IG_FG_CACHE["id"]
    ig_id = None
    try:
        r = requests.get(
            f"{GRAF_API}/{FG_PAGE_ID}",
            params={
                "access_token": FG_PAGE_TOKEN,
                "fields": "instagram_business_account",
            },
            timeout=15,
        )
        r.raise_for_status()
        ig_id = (r.json().get("instagram_business_account") or {}).get("id")
        if not ig_id:
            logger.warning("La página FG no tiene Instagram business vinculado")
    except requests.RequestException as exc:
        logger.warning("No se pudo leer el IG de la página FG: %s", exc)
    _IG_FG_CACHE["id"] = ig_id
    return ig_id


def _construir_mensaje_ig(artista: Artist, enlaces: dict[str, str]) -> str:
    """Caption para Instagram: mención clicable al handle del artista.

    En IG los @handles se convierten en enlaces que además notifican a la
    banda (a diferencia de los captions de FB vía API). Sin placeholders.
    """
    partes_nombre = artista.nombre.strip()
    handle = ""
    if enlaces.get("ig"):
        handle = _extraer_username_ig(enlaces["ig"])
    titulo = (
        f"{partes_nombre} (@{handle})" if handle else partes_nombre
    )
    ficha = " · ".join(
        p for p in (
            _dato_real(getattr(artista, "segmento", None)),
            _dato_real(getattr(artista, "ciudad", None)),
            _dato_real(artista.generos),
        ) if p
    )
    lineas = [
        f"🎵 {titulo} se suma a la escena musical de la frontera grande de Tamaulipas 🎸",
    ]
    if ficha:
        lineas.append(ficha)
    lineas.append("🔗 Escúchalo y sígelo: link en bio")
    hashtags = ["#FronteraGrande", "#MusicaIndependiente", "#Tamaulipas",
                "#EscenaLocal"]
    ciudad = _dato_real(getattr(artista, "ciudad", None))
    if ciudad:
        hashtags.append(f"#{ciudad.replace(' ', '')}")
    lineas.append(" ".join(hashtags))
    return "\n".join(lineas)


def publicar_en_ig(mensaje: str, imagen_url: str) -> dict:
    """Publica la tarjeta en el Instagram de la página FG.

    Flujo de contenedores: `POST /{ig}/media` → poll de `status_code` →
    `POST /{ig}/media_publish`. La API de IG no tiene borradores: publicar
    es inmediato. Returns dict con 'ok', 'post_id' o 'error'.
    """
    ig_id = _ig_de_fg()
    if not ig_id:
        return {"ok": False, "error": "Página FG sin Instagram vinculado"}
    try:
        r = requests.post(
            f"{GRAF_API}/{ig_id}/media",
            data={
                "access_token": FG_PAGE_TOKEN,
                "image_url": imagen_url,
                "caption": mensaje,
            },
            timeout=60,
        )
        r.raise_for_status()
        resp = r.json()
        creation_id = resp.get("id")
        if not creation_id:
            error = (resp.get("error") or {}).get("message", "sin creation_id")
            return {"ok": False, "error": f"Error de Meta: {error}"}

        publicado = False
        for _ in range(10):
            time.sleep(2)
            e = requests.get(
                f"{GRAF_API}/{creation_id}",
                params={"access_token": FG_PAGE_TOKEN,
                        "fields": "status_code"},
                timeout=15,
            )
            estado = e.json().get("status_code")
            if estado == "FINISHED":
                publicado = True
                break
            if estado == "ERROR":
                return {"ok": False, "error": "El contenedor de IG falló"}
        if not publicado:
            return {"ok": False, "error": "Contenedor de IG sin procesar (timeout)"}

        p = requests.post(
            f"{GRAF_API}/{ig_id}/media_publish",
            data={"access_token": FG_PAGE_TOKEN, "creation_id": creation_id},
            timeout=30,
        )
        p.raise_for_status()
        resp_p = p.json()
        post_id = resp_p.get("id")
        if not post_id:
            error = (resp_p.get("error") or {}).get("message", "sin id")
            return {"ok": False, "error": f"Error de Meta: {error}"}
        return {"ok": True, "post_id": post_id}
    except requests.RequestException as exc:
        return {"ok": False, "error": f"Error de red: {exc}"}


def publicar_bienvenida(artista: Artist) -> dict:
    """Genera la tarjeta promocional y publica el post de bienvenida.

    Publica en la página de Facebook y, si PROMO_IG está activo y la
    página tiene Instagram vinculado, también en Instagram con caption
    propio. No lanza excepciones: registra cada resultado en `promo_posts`
    y devuelve un dict con 'ok'. Un fallo de promo nunca rompe la
    verificación.
    """
    if not promo_configurado():
        logger.info("Promo desactivado: FG_PAGE_ID/FG_PAGE_TOKEN ausentes")
        return {"ok": False, "error": "Promo no configurado"}

    enlaces = _obtener_enlaces_artista(artista)
    mensaje = _construir_mensaje(artista, enlaces)

    imagen_url = None
    imagen_url_jpg = None
    try:
        ruta = generar_imagen_promo(artista)
        if ruta and API_PUBLIC_URL:
            imagen_url = imagen_promo_url(artista.slug)
            imagen_url_jpg = f"{API_PUBLIC_URL}/api/promos/{artista.slug}.jpg"
    except Exception as exc:
        logger.warning("Tarjeta no generada para %s: %s", artista.nombre, exc)

    resultado = publicar_en_fb(mensaje, imagen_url)

    try:
        from db.database import SessionLocal

        session = SessionLocal()
        try:
            promo = PromoPost(
                artist_id=artista.id,
                plataforma="fb",
                post_id=resultado.get("post_id", ""),
                mensaje=mensaje,
                estado="publicado" if resultado.get("ok") else "error",
                error_detalle=resultado.get("error", ""),
            )
            session.add(promo)
            session.commit()
        finally:
            session.close()
    except Exception as exc:
        logger.exception("Error guardando promo_post: %s", exc)

    if resultado.get("ok"):
        logger.info("Post de bienvenida publicado para %s (post_id=%s)",
                    artista.nombre, resultado["post_id"])
    else:
        logger.error("Fallo publicando bienvenida para %s: %s",
                     artista.nombre, resultado.get("error"))

    resultado_ig: dict | None = None
    if PROMO_IG:
        mensaje_ig = _construir_mensaje_ig(artista, enlaces)
        if imagen_url_jpg:
            resultado_ig = publicar_en_ig(mensaje_ig, imagen_url_jpg)
        else:
            resultado_ig = {"ok": False,
                            "error": "Sin URL pública para la tarjeta"}
        try:
            from db.database import SessionLocal

            session = SessionLocal()
            try:
                promo = PromoPost(
                    artist_id=artista.id,
                    plataforma="ig",
                    post_id=resultado_ig.get("post_id", ""),
                    mensaje=mensaje_ig,
                    estado="publicado" if resultado_ig.get("ok") else "error",
                    error_detalle=resultado_ig.get("error", ""),
                )
                session.add(promo)
                session.commit()
            finally:
                session.close()
        except Exception as exc:
            logger.exception("Error guardando promo_post IG: %s", exc)
        if resultado_ig.get("ok"):
            logger.info("Bienvenida publicada en IG para %s (post_id=%s)",
                        artista.nombre, resultado_ig["post_id"])
        else:
            logger.error("Fallo publicando bienvenida en IG para %s: %s",
                         artista.nombre, resultado_ig.get("error"))

    resultado["ig"] = resultado_ig
    return resultado


def obtener_promos_artista(artist_id: int) -> list[PromoPost]:
    """Obtiene el historial de posts promocionales de un artista."""
    from db.database import SessionLocal

    session = SessionLocal()
    try:
        return (
            session.query(PromoPost)
            .filter(PromoPost.artist_id == artist_id)
            .order_by(PromoPost.fecha.desc())
            .all()
        )
    finally:
        session.close()