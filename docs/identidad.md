# Identidad visual — Logo de Frontera Grande

> **Documento de referencia** para el estilo y las decisiones del logo y de la
> marca. Cambios de identidad se deciden aquí antes de tocar los archivos.
> Los valores técnicos (rutas, coordenadas) viven en los SVG; aquí vive el
> **porqué** y el **cómo** reproducirlos sin romper el estilo.

## 1. Concepto

- **Marca:** Frontera Grande, base de datos interactiva de la escena de la
  frontera grande de Tamaulipas (ver `docs/vision.md`).
- El logo es un **cuadrado negro de bordes redondeados** que funciona como sello.
  Dentro conviven tres elementos, de arriba a abajo:
  1. Las **iniciales FG** (identificador).
  2. El **wordmark** "FRONTERA / GRANDE" en **dos renglones**.
  3. Una **línea morada** abstracta.
- La línea no representa un accidente geográfico concreto. Es una **silueta
  abstracta de la frontera / del valle**: casi recta, con una leve depresión
  central, en referencia al Valle de Río Grande y a la doble orilla (México y
  EE. UU.). Esta interpretación encaja con el nombre y con la región que
  documenta el proyecto, y no se ata a un cerro específico del sur del estado.
- La identidad es **sobria y escalable**: sirve igual para música hoy y para
  otras disciplinas artísticas mañana (la visión lo permite).

## 2. Paleta

| Uso | Valor | Dónde |
| --- | --- | --- |
| Fondo del logo | `#0b0b10` | `--bg` |
| Fondo suave / tarjetas | `#14141b` | `--surface` |
| Texto principal | `#ececf1` | `--text` |
| Texto secundario (wordmark) | `#b8b8c2` | — |
| **Acento (línea morada)** | `#9d4edd` | `--accent` |
| Fondo suave del acento | `#2a1a33` | `--accent-soft` |

La paleta del logo es la misma de la web (`web/app/globals.css`): no se inventan
colores ajenos al sistema de diseño.

## 3. Tipografía

| Elemento | Fuente | Peso | Notas |
| --- | --- | --- | --- |
| Iniciales `FG` | **Archivo Black** | 900 | La fuente es el símbolo; no se reemplaza por otra |
| Wordmark | **Arial / Helvetica** | 300 (light) | Sobrio, con `letter-spacing` generoso |
| Títulos de web | Archivo Black (vía Google Fonts) | — | Consistente con `FG` |

- Archivo Black debe estar instalada para **regenerar** los SVG/PNG (está en
  `~/.local/share/fonts/ArchivoBlack-Regular.ttf` en el entorno de trabajo).
- Los SVG publicados ya tienen el texto **convertido a trazados** (paths, vía
  `export-text-to-path` de Inkscape): se ven idénticos en cualquier navegador
  sin depender de la fuente. **No** volver a editarlos con `<text>` salvo para
  regenerarlos con la fuente instalada.

## 4. Composición del logo (`web/public/logo-frontera-grande.svg`)

- `viewBox="18 18 476 476"`: **recortado al ras**, sin margen transparente
  alrededor del cuadrado (el cuadrado empieza en 18 y termina en 494 dentro de
  un lienzo de 512, así que el viewBox recorta ese borde).
- Cuadrado: `rect x=18 y=18 width=476 height=476 rx=78`, relleno `#0b0b10`.
- `FG`: Archivo Black, `font-size=168`, `letter-spacing=6` (las iniciales
  separadas), `transform="translate(0 -64) scale(1 1.22)"` (altura natural, sin
  alargar — el alargado es **solo del favicon**).
- Wordmark en **dos renglones**: `FRONTERA` y `GRANDE`, Arial light,
  `font-size=32`, `letter-spacing=6`, color `#b8b8c2`.
- Línea morada: `#9d4edd`, `stroke-width=8`, leve valle central
  (`M130 422h104c11 0 14-8 24-8s13 8 24 8h104`).
- Aire: hay espacio respirado entre el `FG` y el wordmark (el `FG` termina
  alrededor de `y≈254` y `FRONTERA` inicia en `y≈311`).

### Jerarquía visual
`FG` domina en tamaño; el wordmark acompaña; la línea cierra. Nada se encima ni
se toca (verificado midiendo el render, no a ojo).

## 5. Variantes

| Archivo | Uso | Diferencias con el logo |
| --- | --- | --- |
| `web/public/logo-frontera-grande.svg` | Página Acerca de, uso general | El logo completo |
| `web/public/logo-frontera-grande.png` | Export raster (1024×1024) | Misma composición |
| `web/app/icon.svg` | **Favicon** e ícono de navegación | `FG` **alargado** (`scale(0.72 1.4)`), `letter-spacing=20`, sin wordmark, con **línea morada gruesa** (`stroke-width=34`) al pie |
| `web/app/favicon.ico` | Favicon legacy (16/32/48) | Raster del `icon.svg` |
| `web/public/banner-frontera-grande.svg` + `.png` | Banner para Facebook (1640×624) | Logo embebido + wordmark grande en dos renglones + eslogan "La escena fronteriza, en un solo lugar." |

## 6. Reglas (qué NO se cambia sin decisión)

- **No** mezclar el `FG` alargado del favicon con el `FG` del logo completo:
  el alargado es exclusivo del favicon (pequeño), donde las letras rectas no se
  distinguen. La **línea morada gruesa** del favicon es su propia variante
  (preview de la identidad a tamaño mínimo), distinta de la línea del logo.
- **No** volver a una sola línea para el wordmark: en el cuadrado quedaba
  pequeño o desbordado; los dos renglones lo dejan crecer sin romper la caja.
- **No** cambiar `--accent` (`#9d4edd`) sin actualizar globals.css, los SVG y
  este documento a la vez (una sola verdad).
- **No** regenerar PNG/SVG de memoria: rasterizar con Inkscape y verificar la
  composición midiendo el render (las iniciales, el wordmark y la línea no se
  deben tocar entre sí).
- **No** atar la línea morada a un accidente geográfico: es la frontera/valle
  abstracta (sección 1).
- Cambiar la tipografía de `FG` (Archivo Black) o el cuadrado redondeado
  cambia la identidad: requiere decisión explícita.

## 7. Cómo actualizar el logo

1. Editar el SVG de origen (no el PNG).
2. Rasterizar con Inkscape: `inkscape logo.svg --export-type=png --export-filename=salida.png --export-width=N --export-height=N`.
3. Verificar la composición (posición de bandas y separaciones) sobre el render.
4. Si cambia la composición, actualizar las variantes afectadas (favicon,
   banner) y este documento.
5. `npm run lint && npm run build` dentro de `web/` antes de commit.

> **Regeneración:** los SVG publicados llevan el texto convertido a paths
> (auto-contenidos). Para regenerarlos, editar el texto y rasterizar con
> Inkscape **con Archivo Black instalada**, y volver a convertir a paths con:
> `inkscape --actions="export-text-to-path;export-filename:salida.svg;export-plain-svg;export-do" origen.svg`.