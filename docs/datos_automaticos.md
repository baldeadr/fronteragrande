# Datos que podemos obtener automáticamente

Estado al momento de escribir: agosto 2026. Esta tabla resume qué información extrae cada adaptador/plataforma conectada, cómo se obtiene y qué limitaciones tiene.

## 1. Datos de plataformas sociales y musicales

| Plataforma | Datos obtenidos automáticamente | Modo de obtención | Estado | Limitaciones |
|------------|----------------------------------|-------------------|--------|--------------|
| **Facebook / Instagram** | Publicaciones recientes (fecha, texto, enlace, multimedia); **seguidores** (`followers_count`); estado de actividad; biografía o descripción de la página; verificación de que el artista administra la página; **eventos de la página** (toquines que el artista publica, `pages_events`). | OAuth con Graph API de Meta; sincronización programada vía `scripts/sync_feed_igfb.py` y `scripts/sync_eventos_meta.py`. | Funcional en producción para artistas conectados. | Solo artistas que autorizaron y administren la página registrada; los tokens conectados antes de `pages_events` deben reconectar. |
| **TikTok** | Videos recientes (fecha, título, miniatura, enlace); seguidores; estadísticas de cuenta; **avatar** (se guarda como foto de perfil). | OAuth del creador con PKCE; sincronización programada vía `scripts/sync_feed_tiktok.py`. | Funcional en sandbox; Apex Ultra ya conectado. | La app aún no está aprobada para producción. Alcance limitado hasta aprobación. |
| **YouTube** | Videos recientes del canal; miniaturas; títulos; fechas; bio/descripción pública; actividad reciente; **suscriptores/vistas** vía Data API (`YOUTUBE_API_KEY`). | Adaptador `scraper/adapters/youtube.py` (RSS público sin API key + Data API v3 para stats). | Funcional. | El scraping RSS puede romperse ante cambios de UI; las stats requieren la clave configurada. |
| **Spotify** | Presencia del artista; búsquedas; reproducción actual; historial reciente; tops personales; **lanzamientos propios (álbumes/sencillos)** en el feed. | API oficial + MCP (`scripts/spotify_mcp_server.py`); `scripts/sync_lanzamientos.py` para el feed. | Funcional: `/artists/{id}/albums` responde en modo dev. | Apps en modo desarrollo reciben `0`, `None` o `403` en followers/popularity/géneros/top-tracks hasta obtener Extended Quota. |
| **Bandcamp** | Biografía pública; géneros/etiquetas; **lanzamientos recientes** (título, portada, URL, año). | Adaptador `scraper/adapters/bandcamp.py` (web scraping de la cuadrícula). | Funcional para bio/géneros y feed. | La fecha es el año del título del artista (la cuadrícula no expone fecha exacta). |
| **SoundCloud** | Biografía pública; **pistas recientes** (título, portada, URL, fecha). | Adaptador `scraper/adapters/soundcloud.py` (api-v2 con client_id del bundle JS). | Funcional para bio y feed. | Fuente frágil: el bundle JS cambia; si falla el client_id se omite la fuente. |
| **Beatport** | **Lanzamientos recientes** (título, portada, URL, fecha). | Adaptador `scraper/adapters/beatport.py` (JSON `__NEXT_DATA__`). | Funcional (sin artistas con enlace por ahora). | Sin API pública (la de socios es de pago); el HTML puede cambiar. |
| **Mixcloud** | **Sets (cloudcasts) recientes** (título, portada, URL, fecha). | Adaptador `scraper/adapters/mixcloud.py` (API REST pública `api.mixcloud.com`). | Funcional. | Solo usuario con cloudcasts públicos. |
| **Instagram / Facebook (públicos)** | Previews de posts públicos mediante oEmbed. | Adaptadores `scraper/adapters/instagram.py`, `facebook.py`, `oembed.py`. | Funcional para posts públicos. | Muchos posts privados o con login requerido no se resuelven. |
| **Imágenes de perfil** | URL de foto de perfil: **API primero** (Meta `picture`/`profile_picture_url`, YouTube Data API, TikTok avatar) y scraping `og:image` como respaldo. | `scraper/adapters/imagenes.py` + `scripts/actualizar_imagenes.py`. | Mejorado para artistas conectados. | Para no conectados sigue el scraping (IG/FB/TikTok suelen bloquear). |
| **HTTP genérico** | Detección básica de actividad en sitios web: última modificación, contenido disponible. | Adaptador `scraper/adapters/http.py`. | Funcional básico. | No extrae feeds estructurados. |

## 2. Datos derivados automáticamente

A partir de los datos anteriores, el sistema calcula sin intervención manual:

| Dato derivado | Descripción | Origen |
|---------------|-------------|--------|
| **Estado de actividad** | `activo`, `en_duda` o `inactivo` según la antigüedad de la señal más reciente (posts, videos, lanzamientos). | Regla en `scraper/core.py` usando feed e items recientes. |
| **Feed público** | Lista de publicaciones, videos y lanzamientos recientes de los artistas. | `lib/servicios.py` + repositorios. |
| **Previews** | Miniaturas y players embebidos de YouTube, TikTok, Instagram, Facebook, Spotify, Mixcloud. | `lib/plataformas.py` (registro `PREVIEWS`). |
| **Ranking de alcance** | Índice 0-100 ponderado por plataforma: IG, FB, Spotify, YT, TikTok, Bandcamp, SoundCloud, Beatport, Mixcloud. | `lib/helpers.py`. |
| **Estadísticas de la escena** | Actividad temporal, altas por mes, cobertura por ciudad/categoría, posts en 90 días, eventos próximos. | `GET /api/stats` + componentes SVG. |
| **Snapshots históricos** | Serie temporal de presencia de artistas en Spotify. | `scripts/escena_local_snapshot.py`. |

## 3. Datos que aún no se obtienen automáticamente

| Dato | Estado actual | Nota |
|------|---------------|------|
| **Métricas útiles de Spotify para todos los artistas** | Limitado | Requiere Extended Quota para followers/popularity/top-tracks. |
| **Eventos futuros** | Parcialmente manual | `data/eventos.csv`, **CRUD del panel admin** e ingesta automática de los eventos que los artistas conectados publican en su página de Facebook (`pages_events`). |
| **Artistas no conectados a Meta/TikTok** | Sin actividad social automática | Solo se muestran datos semilla + feed de YouTube/lanzamientos si aplica. |
| **Datos privados o restringidos por plataforma** | No accesibles | Respetamos los límites de cada API y el modo sandbox/producción. |

---

Última actualización: 2026-08-20.