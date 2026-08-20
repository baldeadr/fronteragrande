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
| 4 | Beatport | `og:image` | funciona sin API key. |
| 5 | Mixcloud | `og:image` | funciona sin API key. |
| 6 | YouTube | `og:image` | funciona sin API key (og:image del canal). |
| 7 | Instagram | `og:image` | **suele bloquear bots** (400/429); se omite si falla. |
| 8 | Facebook | `og:image` | **suele bloquear bots**; se omite si falla. |
| 9 | TikTok | `og:image` | **suele bloquear bots**; se omite si falla. |
| 10 | X | `og:image` | se intenta como última opción. |

Fuente única en código:

```python
# scraper/jerarquias.py
PRIORIDAD_FOTO_DE_PERFIL = [
    "spotify", "bandcamp", "soundcloud", "beatport", "mixcloud",
    "yt", "ig", "fb", "tt", "x",
]
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
| 5 | Beatport |
| 6 | Mixcloud |
| 7 | Instagram |
| 8 | TikTok |
| 9 | web |

Fuente única en código:

```python
# scraper/jerarquias.py
PRIORIDAD_LINK_PUENTE = [
    "yt", "spotify", "bandcamp", "soundcloud",
    "beatport", "mixcloud", "ig", "tt", "web",
]
```

---

## 3. Adaptadores de actividad y feed (complementarios)

Estos **no compiten entre sí**: cada uno alimenta una parte distinta del feed
y de la detección de actividad. No hay jerarquía entre ellos.

| Adaptador | Función | Requisitos |
|-----------|---------|------------|
| `scraper/adapters/http.py` | salud de URLs (200/4xx) para chequear actividad | ninguno |
| `scraper/adapters/youtube.py` | últimos videos del canal vía RSS → `feed_items` | ninguno (sin API key) |
| `scraper/adapters/youtube.py` | estadísticas públicas del canal → `followers_yt`/`vistas_yt` | `YOUTUBE_API_KEY` |
| `scraper/adapters/tiktok.py` | metadatos de un video/post vía **oEmbed** público (título, autor, miniatura) | ninguno (sin API key) |
| `scraper/adapters/instagram.py` | oEmbed de un post/reel de IG público (html del embed) | ninguno (sin API key) |
| `scraper/adapters/facebook.py` | oEmbed de un post de FB público (html del embed) | ninguno (sin API key) |
| `scraper/adapters/mixcloud.py` | oEmbed de un set de Mixcloud (título, autor, miniatura, widget) | ninguno (sin API key) |
| `scraper/adapters/spotify.py` | datos de Spotify vía Web API | credenciales en `.env` (opcional) |
| `scraper/adapters/spotify_public.py` | oyentes mensuales del perfil público | ninguno; captura HTML puntual |
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
| Mixcloud | miniatura de portada o widget embebible | vía **oEmbed** público (sin API key); Beatport sin preview (texto/portada) |

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

### Oyentes mensuales de Spotify

La captura de oyentes mensuales usa el perfil público de Spotify, no la Web API
ni Spotify for Artists. Solo se procesa un artista cuando tiene una URL oficial
de Spotify registrada (`artist_links.plataforma = spotify` y no es una URL de
búsqueda). La URL se consulta con `scraper/adapters/spotify_public.py`, que lee
los metadatos públicos `og:description` o el elemento visible de oyentes.

El script inicial es `scripts/actualizar_oyentes_spotify.py`. Guarda el valor
actual en el artista y una fila histórica en `spotify_listener_snapshots`, con
fecha, URL, fuente y estado. Los fallos no detienen el resto del lote.

La captura es puntual por ahora: no hay cron. El onboarding de un artista nuevo
intenta capturar el dato una vez después de registrar su URL de Spotify; si
Spotify bloquea o cambia el HTML, el registro del artista continúa.

El dato debe mostrarse como **capturado del perfil público de Spotify** con su
fecha, no como una métrica en vivo ni como una estadística privada de Spotify
for Artists. No se buscan ni se registran perfiles ambiguos sin validación.

### Lanzamientos y contenido nuevo en el feed (fase 2026-08)

El feed registra también el **contenido nuevo** (material propio, no
apariciones) de cada artista por plataforma, vía `scripts/sync_lanzamientos.py`
(cron cada 6 h, workflow `sync-lanzamientos.yml`):

| Plataforma | Vía de datos | Adaptador | Detalle |
|------------|--------------|-----------|---------|
| Spotify | API oficial (`/artists/{id}/albums`, client credentials) | `scraper/adapters/spotify.py` (`get_artist_releases`) | álbumes y sencillos propios; funciona en apps en modo dev |
| Bandcamp | cuadrícula `music-grid-item` del HTML | `scraper/adapters/bandcamp.py` (`ultimos_lanzamientos`) | fecha = año del título del lanzamiento (el artista lo escribe); sin año → sin fecha |
| SoundCloud | api-v2 pública con `client_id` extraído del bundle JS | `scraper/adapters/soundcloud.py` (`ultimas_pistas`) | fuente frágil (el bundle cambia); si falla, se omite |
| Beatport | `__NEXT_DATA__` de la página del artista | `scraper/adapters/beatport.py` (nuevo) | sin API pública; `queries → state.data.results` |
| Mixcloud | API REST pública `api.mixcloud.com/{user}/cloudcasts/` | `scraper/adapters/mixcloud.py` (`ultimos_sets`) | lista los sets (cloudcasts) subidos |

Reglas del sync unificado:

- Solo **material propio** del artista (Spotify usa `include_groups=album,single`).
- Anti-duplicados por URL: `FeedRepository.crear_si_nuevo` (un solo lugar).
- Ventana de actividad: solo entran items de los últimos `SPOTIFY_SYNC_MESES`
  meses (24 por defecto); el feed es bitácora, no discografía completa.
- Un fallo por artista/plataforma no detiene el lote (try/except aislado).
- Al final recalcula `estado_activo` (el contenido reciente ≤ 6 meses lo
  alimenta).

### Seguidores de Facebook/Instagram (Meta Graph API)

El sync de Meta (`scripts/sync_feed_igfb.py`) también actualiza los
**seguidores** de los artistas conectados: `followers_count` de la página FB
(`backend/feed_meta.py::pagina_seguidores`) y de la cuenta IG de negocio
(`ig_seguidores`). Los scopes actuales (`pages_read_engagement`,
`instagram_basic`) ya lo permiten. Solo escribe cuando la API devuelve un
valor (no inventa ceros) y marca `fecha_captura`.

### Fotos de perfil por API

`scripts/actualizar_imagenes.py` prioriza las **API oficiales** antes del
scraping: foto de la página FB (`/{page}/picture`) o de la cuenta IG
(`profile_picture_url`) para artistas conectados, y miniatura del canal vía
YouTube Data API si hay `YOUTUBE_API_KEY`. El avatar de TikTok se actualiza en
`scripts/sync_feed_tiktok.py` (donde ya se rota el token). Si ninguna API
responde, cae a la cadena de scraping `og:image` (jerarquía en
`scraper/jerarquias.py`).

### Eventos: CRUD en el admin e ingesta desde Meta (fase 2026-08)

El calendario de eventos tiene dos vías de alimentación:

- **Panel de administración:** alta, edición y baja desde `/admin` (pestaña
  "Eventos") vía `POST/PUT/DELETE /api/admin/events` (protegidos por
  `X-Admin-Token`). La lógica vive en `EventRepository` (`lib/repository.py`).
- **Ingesta automática desde Meta:** los artistas conectados que otorgaron el
  permiso `pages_events` publican sus toquines como eventos de página;
  `scripts/sync_eventos_meta.py` los registra en `events` (sin duplicar por
  fuente `Facebook (página del artista) · {evento_id}`, con el artista como
  promotor del cartel). El workflow `sync-eventos-meta.yml` lo corre cada 6 h.
  Los tokens conectados antes de añadir `pages_events` al scope necesitan
  **reconectar** Meta desde el perfil para concederlo (el sync los omite con
  un aviso, sin fallar).

**Eventos como señal de actividad:** `lib/servicios.recalcular_actividad`
actualiza `artista.ultimo_evento` con el evento más reciente en cuyo cartel
aparece el artista (solo avanza la fecha, nunca la regresa, para no pisar el
valor curado del CSV), y con eso aplica la regla de actividad. Lo llaman los
scripts de sync y los endpoints del admin tras cada cambio.

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
| Evento | escena | CRUD del admin / eventos de página Meta (`pages_events`) |

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
los artistas y actualiza `estado_activo` en la **BD** (fuente de verdad); el
CSV semilla se regenera aparte con `scripts/exportar_csv.py`.

---

## Cómo cambiar una jerarquía

1. Editar **solo** `scraper/jerarquias.py` (es la fuente única; `imagenes.py`
   y `lib/helpers.py` la importan).
2. Si cambia la de fotos de perfil, re-correr `scripts/actualizar_imagenes.py`.
3. Actualizar las tablas de este documento para mantener la documentación sincronizada.
