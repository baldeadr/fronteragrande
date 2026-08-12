# Scraping: adaptadores y jerarquías de plataformas

El scraping del proyecto no es un solo motor: hay **adaptadores por fuente**
(`scraper/adapters/`) y **jerarquías de plataforma** para decidir qué usar
cuando hay varias opciones disponibles. Las jerarquías están centralizadas en
`scraper/jerarquias.py` (fuente única de verdad); este documento las explica.

---

## 1. Jerarquía de foto de perfil

**Módulo:** `scraper/adapters/imagenes.py` · **Constante:** `PRIORIDAD_FOTO_DE_PERFIL`
**Script:** `scripts/actualizar_imagenes.py` (recorre artistas, guarda
`imagen_perfil`, `imagen_origen`, `imagen_actualizada`).

Se prueba cada plataforma en orden hasta obtener una URL de imagen; si ninguna
funciona, la web muestra el **fallback a inicial** del nombre (`web/components/Avatar.tsx`).

| # | Plataforma | Método | Observaciones |
|---|------------|--------|---------------|
| 1 | Spotify | página *embed* del artista | prefiere la foto `ab676161…`; si el artista no tiene foto, usa su cabecera `ab67616d0000b273…` (recorte grande). Host: `image-cdn-ak.spotifycdn.com`. |
| 2 | Bandcamp | `og:image` | funciona sin API key. |
| 3 | SoundCloud | `og:image` | funciona sin API key. |
| 4 | YouTube | `og:image` | funciona sin API key (og:image del canal). |
| 5 | Instagram | `og:image` | **suele bloquear bots** (400/429); se omite si falla. |
| 6 | Facebook | `og:image` | **suele bloquear bots**; se omite si falla. |
| 7 | TikTok | `og:image` | **suele bloquear bots**; se omite si falla. |
| 8 | X | `og:image` | se intenta como última opción. |

Fuente única en código:

```python
# scraper/jerarquias.py
PRIORIDAD_FOTO_DE_PERFIL = ["spotify", "bandcamp", "soundcloud", "yt", "ig", "fb", "tt", "x"]
```

---

## 2. Jerarquía del enlace "puente"

**Módulo:** `lib/helpers.py` · **Función:** `artista_link_principal()`
**Constante:** `PRIORIDAD_LINK_PUENTE`

La tarjeta de un artista muestra **un solo enlace principal** ("el puente" a
sus redes). Se elige el primer enlace **no de búsqueda** (`es_busqueda=False`)
según este orden:

| # | Plataforma |
|---|------------|
| 1 | YouTube |
| 2 | Spotify |
| 3 | Bandcamp |
| 4 | SoundCloud |
| 5 | Instagram |
| 6 | TikTok |
| 7 | web |

Fuente única en código:

```python
# scraper/jerarquias.py
PRIORIDAD_LINK_PUENTE = ["yt", "spotify", "bandcamp", "soundcloud", "ig", "tt", "web"]
```

---

## 3. Adaptadores de actividad y feed (complementarios)

Estos **no compiten entre sí**: cada uno alimenta una parte distinta del feed
y de la detección de actividad. No hay jerarquía entre ellos.

| Adaptador | Función | Requisitos |
|-----------|---------|------------|
| `scraper/adapters/http.py` | salud de URLs (200/4xx) para chequear actividad | ninguno |
| `scraper/adapters/youtube.py` | últimos videos del canal vía RSS → `feed_items` | ninguno (sin API key) |
| `scraper/adapters/tiktok.py` | metadatos de un video/post vía **oEmbed** público (título, autor, miniatura) | ninguno (sin API key) |
| `scraper/adapters/instagram.py` | oEmbed de un post/reel de IG público (html del embed) | ninguno (sin API key) |
| `scraper/adapters/facebook.py` | oEmbed de un post de FB público (html del embed) | ninguno (sin API key) |
| `scraper/adapters/spotify.py` | datos de Spotify | credenciales en `.env` (opcional) |
| `scraper/adapters/oembed.py` | llamada oEmbed compartida (con caché) para TikTok/IG/FB | ninguno |

Todos los adaptadores lanzan excepciones de la familia `scraper/errors.py`
(`ScraperError` y subclases por fuente) para que quienes los llaman no se
acoplen a excepciones concretas ni de red.

### Previews del feed estilo YouTube

El feed previsualiza el contenido de cada plataforma así (ver el registro
`PREVIEWS` en `lib/plataformas.py`):

| Plataforma | Preview | Detalle |
|------------|---------|---------|
| YouTube | miniatura + botón de play | embed oficial + link a YouTube |
| TikTok | miniatura + botón de play (o embed) | miniatura/título vía **oEmbed** (sin API key) |
| Instagram | iframe embebible | `/p/{código}/embed/captioned/` (carga en el navegador, sin token) |
| Facebook | iframe embebible | `/plugins/post.php` (carga en el navegador, sin token) |

**Importante:** Instagram, Facebook y TikTok **bloquean bots**, así que no se
puede listar automáticamente los posts recientes de un perfil ajeno (IG pide
token OAuth, FB bloquea, TikTok pone captcha). Por eso la ingesta de contenido
de un proyecto **la hace el propio artista**: al conectar su página de
Facebook/Instagram (OAuth) el contenido se sincroniza automáticamente; los
proyectos que no conectan quedan como registros de investigación sin contenido
sincronizado (no hay ingesta manual).

El feed **solo enlaza**: guarda la URL original y muestra el embed/miniatura,
y el botón **"Abrir en {plataforma}"** lleva al contenido en su red de origen
(la app es un puente, no almacena el contenido).

### Sincronización automática con Meta Graph API (Fase 3)

Para artistas que **administran su página** de FB/IG, la conexión OAuth con
Meta permite automatizar la ingesta (sin copiar contenido, solo enlaces):

- **Credenciales** en `.env`: `META_APP_ID`, `META_APP_SECRET` y
  `META_REDIRECT_URI` (deben registrarse en developers.facebook.com con los
  permisos `pages_show_list`, `pages_read_engagement`, `instagram_basic`).
- **Flujo:** `GET /api/feed/igfb/login?slug={slug}` → diálogo de Facebook →
  `GET /api/feed/igfb/callback` canjea el código y guarda el **token de
  página** (larga duración, no expira salvo revocación) más el id de la
  cuenta IG de negocio. Al conectar, el perfil queda **verificado**:
  `estado_registro` pasa a `confirmado (artista, YYYY-MM-DD)`. La app valida
  que la cuenta autorizada administre la página **registrada** del artista
  (compara con su URL de Facebook); si administra otra página, falla. Los
  tokens **nunca** se exponen en la API.
- **Sync:** `scripts/sync_feed_igfb.py` trae los últimos posts de la página FB
  (`/{page}/posts`) y los media de la cuenta IG (`/{ig-user}/media`) y crea
  `FeedItem` sin duplicar por URL; al final recalcula actividad.
- **UI:** en el perfil, sección "Reclama tu perfil" (botón de conexión) o
  "Perfil verificado" (estado conectado). Solo se muestra si la app está
  configurada.

Si Meta no está configurado, la app funciona solo con los registros de
investigación (sin contenido sincronizado): no existe vía manual de ingesta.

## 4. El feed como señal de actividad

El **feed del perfil** no es solo un escaparate: es la **bitácora de señales
de actividad** del proyecto. Su propósito es responder *"¿el proyecto sigue
activo?"*. Cada elemento del feed es evidencia de actividad.

**Qué cuenta como actualización** (fuente de verdad):

| Señal | Plataformas | Cómo se registra |
|-------|-------------|------------------|
| Video nuevo | YouTube, Instagram, TikTok | adaptador RSS de YT (onboarding) / sync Meta Graph API |
| Post nuevo | Instagram, Facebook, TikTok | sync Meta Graph API (artista conectado) |
| Lanzamiento | Spotify, Bandcamp, SoundCloud, Apple | campo `ultimo_lanzamiento` del artista |
| Evento | escena | CSV de eventos |

**No cuenta** como señal: solo "presencia" del perfil o reacciones a contenido
ajeno.

**Regla de actividad (6 / 18 meses):** se toma la **señal más reciente** de
todas las disponibles (lanzamiento, evento o elemento del feed):

| Estado | Última señal |
|--------|--------------|
| `activo` | ≤ 6 meses (o método `presencia_continua` / `lanzamiento_próximo`) |
| `en_duda` | entre 6 y 18 meses, o sin señal conocida |
| `inactivo` | > 18 meses, o pausa confirmada (`artista (EN PAUSA)`) |

Implementada en `scraper/core.py` (`REGLA_ACTIVIDAD`); **no depende de
jerarquías de plataformas**. `scripts/recalcular_actividad.py` recorre todos
los artistas y actualiza `estado_activo` (BD **y** CSV semilla, para mantener
una sola verdad).

---

## Cómo cambiar una jerarquía

1. Editar **solo** `scraper/jerarquias.py` (es la fuente única; `imagenes.py`
   y `lib/helpers.py` la importan).
2. Si cambia la de fotos de perfil, re-correr `scripts/actualizar_imagenes.py`.
3. Actualizar las tablas de este documento para mantener la documentación sincronizada.
