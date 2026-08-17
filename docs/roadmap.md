# Roadmap — Frontera Grande

Estado del proyecto y próximos pasos. Convenciones: ✔ hecho ·
`[PENDIENTE]` esperando datos/definición del artista · `[PROPUESTA]`
propuesta de la IA pendiente de confirmación.

## Fase actual

**Web pública en local (Next.js + FastAPI)**: directorio, perfiles, feed de
actividad interactivo, eventos, **panel de stats interactivo**, **registro
voluntario de artistas** (verificación por OAuth de Meta) y puente a redes,
con página **Acerca de**. **Desplegado en línea (agosto 2026)** con Vercel +
Render + Neon (ver estado completo en `docs/despliegue.md`). Queda pendiente
de **datos externos** (cron de Meta, Extended Quota de Spotify) que el artista
debe conseguir.

## Hecho

| # | Etapa | Detalle |
|---|-------|---------|
| 1 | ✔ MVP original (Streamlit) | CRUD + lista + eventos + stats + scraper. Superado por la web. |
| 2 | ✔ Feed de contenido reciente | Últimos videos de YouTube (RSS, sin API key) unificados con eventos y lanzamientos. |
| 3 | ✔ Pivote a web pública | Next.js + FastAPI, previews y puente a redes, mobile-first, SEO básico. |
| 4 | ✔ Fotos de perfil | URLs desde las redes sin descargar imágenes (`scraper/jerarquias.py`); fallback a inicial. |
| 5 | ✔→✘ Ingesta asistida de posts (eliminada) | Se implementó como puente manual (`POST /api/artists/{slug}/feed` + botón "+ Añadir post") y luego **se eliminó** en el pivote a **registro voluntario del artista**: el contenido del feed solo llega por el artista que conecta su página FB/IG (sync Meta) o el feed de YouTube del onboarding. No reintroducir. |
| 6 | ✔ Stats de redes | Seguidores FB/IG y reproducciones Spotify por plataforma (datos con fuente). |
| 7 | ✔ **Ranking de alcance** | Índice 0-100 = suma ponderada por plataforma (IG 29/FB 24/Spotify 19/YT 9/TT 9/BC 2.5/SC 2.5/Beatport 3/Mixcloud 2) de alcance `log10` normalizado entre todos los artistas (`lib/helpers.py`); menciones especiales para el Top 3 por género/ciudad/segmento. |
| 8 | ✔ Directorio pulido + registro desde la web | Taxonomía de categoría (Banda/Solista/DJ/Colectivo/Covers/Tributo; MC y Productor como Solista), ciudades base única con dropdown (Tamaulipas + Valle de Río Grande + "Otro"), filtros con etiqueta y "Todas", géneros en chips; `POST /api/artists` ("Suma tu proyecto") con onboarding (foto, ultimos videos YT, `estado_activo`). El artista **verifica** su perfil conectando la página FB/IG. |
| 9 | ✔ Identidad **Frontera Grande** + Acerca de | Renombrado en toda la web; `docs/vision.md` (fuente única de qué es/qué no es); página **Acerca de** (historia, "cómo explorar", actividad y regla del ranking con fórmula en LaTeX); feed mejorado (foto real, fecha relativa, "Cargar más", H1 "Actividad de la escena"). |
| 10 | ✔ **Panel de stats interactivo** | `GET /api/stats` ampliado (`feed_serie`, `altas_por_mes`, `seguidores`/`reproducciones`, `cobertura`, `posts_90dias`, `por_ciudad`, `eventos_proximos`) + gráficas SVG caseras interactivas (actividad temporal, ranking desglosable por red, ecosistema de redes, ciudades apiladas con leyenda, dona por categoría) — sin dependencias de cliente. |
| 11 | ✔ **Panel de administración en la web (CRUD con auth)** | `/admin` protegido por `ADMIN_PASSWORD` (`X-Admin-Token`): login en sesión, listado con `GET /api/admin/artists`, edición (`PUT /api/artists/{slug}`: nombre, ciudad, categoría, géneros, bio, notas, logros, estado de actividad y redes) y eliminación (`DELETE /api/artists/{slug}`) con confirmación. Pendiente el disparador del scraper. |
| 12 | ✔ **Bios y géneros con fuente (Fase 1, cadena)** | Detectores sin API key en `scraper/adapters/` (`bandcamp.py` → bio+tags, `soundcloud.py` → bio vía `__sc_hydration`, `youtube.py` → `youtube_about`). `scripts/proponer_bios.py` recorre Bandcamp→SoundCloud→YouTube, **escribe directo** cuando la fuente está clara (`lib/helpers.es_bio_clara`, sin homónimos advertidos en `notas` ni en `CONFLICTOS_CONOCIDOS`) con nota `Bio de X (YYYY-MM-DD)` en `notas`, y reporta lo ambiguo en `data/bios_pendientes.md`. Primera corrida 2026-08-16: **3 bios escritas** (Futura Driver, Invitrox, Magito Rody); Distraught y Don Bravo quedaron pendientes por homónimos/conflicto. Spotify se omite (no expone bio pública). |

## Pendiente de datos externos (bloquea su activación)

| # | Etapa | Estado | Depende de |
|---|-------|--------|-----------|
| 11 | **Sincronización automática FB/IG (Meta)** | ◐ OAuth y primera sincronización de producción completados: Apex Ultra quedó **verificado** y sus publicaciones de Facebook ya aparecen en el perfil. Workflow de GitHub Actions activo cada 6 horas. Pendiente conectar al resto de artistas y confirmar el siguiente ciclo automático. | Artistas participantes |
| 12 | YouTube `vistas_yt` | `[PENDIENTE]` no se extraen sin API key o ejecución de JS. | `YOUTUBE_API_KEY` opcional |
| 13 | Spotify: números del API | ✔ MCP (`scripts/spotify_mcp_server.py`) + snapshot (`scripts/escena_local_snapshot.py` → `data/escena_local_stats.csv`) clonados de architecting-a-band y probados. **Verificado 2026-08:** con las credenciales de desarrollo el API resuelve nombre/imagen/URI, pero **no entrega followers/popularity/géneros** (los campos ni siquiera aparecen) y `top-tracks` da **403**; el snapshot ya tolera esa respuesta (registra 0/0) y queda listo para re-ejecutarse sin cambios. **`[PENDIENTE]`** el API 2026 entrega esos números solo con **Extended Quota** (revisión de la app en el dashboard: developer.spotify.com/dashboard → app → solicitar quota). | **Extended Quota** de Spotify |

## Próximas etapas `[PROPUESTA]`

| # | Etapa | Notas |
|---|-------|-------|
| 14 | **Canales oficiales de comunicación** | `[PROPUESTA]` Crear página de Facebook y cuenta de Instagram de Frontera Grande. Publicar artistas registrados, eventos, lanzamientos, datos de la escena y reels con fuentes o autorización; enlazar siempre al sitio. Definir identidad, calendario editorial y métricas de tráfico. |
| 15 | Disparador de scraper en el panel de admin | ✔ CRUD hecho (`/admin`, editar/eliminar). Pendiente: botón que dispare el scraper de actividad por artista desde el panel. |
| 16 | Feeds de Bandcamp/SoundCloud y métricas públicas de Spotify | Captura puntual de oyentes mensuales desde perfiles públicos de Spotify; 16 URLs confirmadas y 11 artistas sin perfil. Pendiente ejecutar el lote inicial en producción. |
| 17 | Mapa de artistas por origen | PostGIS: la geografía de la escena (Reynosa/Matamoros/frontera). |
| 18 | **Producción y monetización** | ✔ **EN LÍNEA (agosto 2026):** web en Vercel (`fronteragrande.vercel.app`), API en Render (`fronteragrande-api.onrender.com`), BD en Neon. Deploy automático desde GitHub. Meta ya sincroniza publicaciones; pendiente: medir audiencia 90 días, evaluar patrocinio local, monitor UptimeRobot, conectar más artistas, **dominio** (`fronteragrande.mx`) y AdSense. Análisis financiero: `docs/finanzas.md`. |
| 19 | **Bios: Fase 2 y cierre** | ✔ **Hecho (2026-08-16):** `about`/`description` de FB y `biography` de IG para artistas **conectados a Meta** vía `backend/feed_meta.py`, integrado en el sync de 6h (`scripts/sync_feed_igfb.py`) con guarda `es_bio_clara` y nota de fuente. Pendiente: cerrar los pendientes de `data/bios_pendientes.md` (23) con curaduría desde el panel de admin. |
| 20 | **Sincronización de TikTok (Business API)** | ✔ **Hecho (backend, web y cron, 2026-08-16):** inventario (`docs/tiktok.md`), columnas `tt_user_id`/`tt_refresh_token`, `backend/feed_tiktok.py` (OAuth del creador con **PKCE**; scopes `user.info.basic`+`user.info.stats`+`video.list`), `scripts/sync_feed_tiktok.py`, botón "Conectar TikTok" en el perfil y `.github/workflows/sync-tiktok.yml` cada 6 h. **Probado con Apex Ultra en sandbox:** conectado, verificado, seguidores y videos al feed. **`[PENDIENTE]`** del artista: **aprobación** de la app (video demo + explicación) para producción y conectar al resto del inventario. |

## En curso `[PROPUESTA]`

| # | Etapa | Estado |
|---|-------|--------|
| 18 | **Despliegue free tier (prueba con artistas)** | ✔ **Activo (2026-08):** API en Render `https://fronteragrande-api.onrender.com` (`{"estado":"ok"}`), web en Vercel `https://fronteragrande.vercel.app`, datos en Neon y Meta sincronizando en producción. Apex Ultra está verificado y muestra publicaciones de Facebook. Pendientes menores: crear monitor UptimeRobot y conectar más artistas (`docs/despliegue.md`). |

## Campaña de lanzamiento `[PROPUESTA]`

Plan de lanzamiento orgánico definido el 2026-08-16. Detalle completo en
`bitacora/2026-08.md` (sesión del 16).

### Fase 0: Preparación (pendiente)

| # | Tarea | Estado |
|---|-------|--------|
| 1 | Botón "Compartir" en perfil de artista (WhatsApp, FB, copiar enlace) | `[PENDIENTE]` |
| 2 | Imagen OG dinámica por artista (links se ven profesionales en redes) | `[PENDIENTE]` |
| 3 | Badge "Recién registrado" (primeros 30 días) | `[PENDIENTE]` |
| 4 | Sección "Nuevos en la escena" en homepage | `[PENDIENTE]` |
| 5 | Script `generar_tarjeta.py` (Pillow, cuadrado + story, verificados + activos) | `[PENDIENTE]` |
| 6 | Completar perfiles de FB/IG (bio, portada) | `[PENDIENTE]` |
| 7 | Preparar contenido base (3-4 posts) | `[PENDIENTE]` |
| 8 | Actualizar `/ayuda-artistas` con beneficios de verificación | `[PENDIENTE]` |
| 9 | Crear cuenta de TikTok (cross-posting) | `[PENDIENTE]` |

### Fase 1: Sembrado (1-2 semanas)

- Compartir enlace en grupo de FB (~30 artistas) con post casual.
- Publicar posts base en IG/FB + primera "Artista de la Semana".
- Monitorear registros y tráfico. No follow-up agresivo.

### Fase 2: Lanzamiento suave

- $100 MXN boost en mejor post (sí hay señal del grupo FB).
- Compartir en círculo personal. Artistas compartiendo sus perfiles.

### Fase 3: Crecimiento continuo

- Posts regulares (2-3/semana). "Artista de la Semana" semanal.
- Medir métricas 90 días. Decisión de dominio (50+ visitas/semana → `fronteragrande.mx`).
- Patrocinios directos a locales de la zona (bares, escuelas, tiendas).

## Pendiente de producto

| Ítem | Estado |
|------|--------|
| **Dominio** | Decisión tomada: **`fronteragrande.mx`** (2026-08). Metadatos/sitemap/robots ya usan `https://fronteragrande.mx`. Pendiente: registrar/comprar el dominio y apuntarlo al despliegue. |
| **Permisos del registro** | El formulario hoy es público (modo desarrollo); requiere auth cuando se decida. |
| **Sync de Meta** | Workflow de GitHub Actions activo cada 6 horas; primera sincronización confirmada con Apex Ultra. Pendiente conectar al resto de artistas. |
| **Finanzas** | Análisis inicial en `docs/finanzas.md`: audiencia de nicho, costos casi nulos en free tier, patrocinio local antes que APIs premium y AdSense como complemento. |

## Cómo se actualiza

- Los pasos los decide el **artista**; la IA propone e implementa lo técnico.
- Al completar una etapa, moverla a "Hecho" y actualizar `README.md`
  (sección Roadmap), `AGENTS.md` (Estado) y este documento — una sola verdad.
- Un elemento `[PENDIENTE]` no se marca hecho hasta que el dato real llegue
  y se verifique (regla: no inventar datos).
