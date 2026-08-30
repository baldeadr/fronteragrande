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
| 7 | ✔ **Ranking de alcance** | Índice global 0-100 = 55% audiencia + 45% consumo, con señales `log10` normalizadas por métrica. YouTube divide su peso 30% suscriptores / 70% vistas; Spotify separa seguidores de oyentes/reproducciones. Muestra índices de audiencia, consumo y global (`lib/helpers.py`); menciones especiales para el Top 3 por género/ciudad/segmento. |
| 8 | ✔ Directorio pulido + registro desde la web | Taxonomía de categoría (Banda/Solista/DJ/Colectivo/Covers/Tributo; MC y Productor como Solista), ciudades base única con dropdown (Tamaulipas + Valle de Río Grande + "Otro"), filtros con etiqueta y "Todas", géneros en chips; `POST /api/artists` ("Suma tu proyecto") con validaciones (mínimo 1 red, máximo 6, rechazo de URLs duplicadas, rate-limit 5/IP/24h + cooldown 10min), onboarding (foto, últimos videos YT, `estado_activo`) y leyenda de que los proyectos sin verificar pueden ser eliminados. El artista **verifica** su perfil conectando la página FB/IG/TikTok; notificaciones push solo tras verificación. |
| 9 | ✔ Identidad **Frontera Grande** + Acerca de | Renombrado en toda la web; `docs/vision.md` (fuente única de qué es/qué no es); página **Acerca de** (historia, "cómo explorar", actividad y regla del ranking con fórmula en LaTeX); feed mejorado (foto real, fecha relativa, "Cargar más", H1 "Actividad de la escena"). |
| 10 | ✔ **Panel de stats interactivo** | `GET /api/stats` ampliado (`feed_serie`, `altas_por_mes`, `seguidores`/`reproducciones`, `cobertura`, `posts_90dias`, `por_ciudad`, `eventos_proximos`) + gráficas SVG caseras interactivas (actividad temporal, ranking desglosable por red, ecosistema de redes, ciudades apiladas con leyenda, dona por categoría) — sin dependencias de cliente. |
| 11 | ✔ **Panel de administración en la web (CRUD con auth)** | `/admin` protegido por `ADMIN_PASSWORD` (`X-Admin-Token`): login en sesión, listado con `GET /api/admin/artists`, edición (`PUT /api/artists/{slug}`: nombre, ciudad, categoría, géneros, bio, notas, logros, estado de actividad y redes) y eliminación (`DELETE /api/artists/{slug}`) con confirmación. Pendiente el disparador del scraper. |
| 12 | ✔ **Bios y géneros con fuente (Fase 1, cadena)** | Detectores sin API key en `scraper/adapters/` (`bandcamp.py` → bio+tags, `soundcloud.py` → bio vía `__sc_hydration`, `youtube.py` → `youtube_about`). `scripts/proponer_bios.py` recorre Bandcamp→SoundCloud→YouTube, **escribe directo** cuando la fuente está clara (`lib/helpers.es_bio_clara`, sin homónimos advertidos en `notas` ni en `CONFLICTOS_CONOCIDOS`) con nota `Bio de X (YYYY-MM-DD)` en `notas`, y reporta lo ambiguo en `data/bios_pendientes.md`. Primera corrida 2026-08-16: **3 bios escritas** (Futura Driver, Invitrox, Magito Rody); Distraught y Don Bravo quedaron pendientes por homónimos/conflicto. Spotify se omite (no expone bio pública). |
| 13 | ✔ **Ligas (catálogo de artistas destacados)** | Campo `nivel` (**Liga Mayor / En Ascenso / Leyenda de la Frontera**, ortogonal a Categoría) con **ranking de Ligas aparte** del de la escena local (`lib/servicios.ranking_ligas`); clasificador `lib/helpers.calcular_indice_universal` + `clasificar_por_indice` (techos fijos + umbrales **≥60 Ligas Mayores / ≥50 En Ascenso**, anti-trampa social ≤ consumo×3); catálogo inicial de 22 artistas de `curado3_enriquecido.csv` (5 Leyenda + 5 Liga Mayor, el resto sin nivel hasta tener métricas con fuente); filtro "Liga" en el directorio, insignia en tarjeta/perfil, gráfica "Ranking de Ligas" en `/stats`, sección en Acerca de y edición en el panel de admin. |

## Pendiente de datos externos (bloquea su activación)

| # | Etapa | Estado | Depende de |
|---|-------|--------|-----------|
| 11 | **Sincronización automática FB/IG (Meta)** | ◐ OAuth y primera sincronización de producción completados: Apex Ultra quedó **verificado** y sus publicaciones de Facebook ya aparecen en el perfil. Workflow de GitHub Actions activo cada 6 horas. Pendiente conectar al resto de artistas y confirmar el siguiente ciclo automático. | Artistas participantes |
| 12 | **Estadísticas públicas de YouTube** | ✔ `scripts/sync_youtube_stats.py` usa YouTube Data API v3 para actualizar `followers_yt`, `vistas_yt` y `fecha_captura`; workflow semanal en GitHub Actions. Las tarjetas muestran suscriptores cuando el dato es público. | `YOUTUBE_API_KEY` y validación de canales |
| 13 | Spotify: números del API | ✔ MCP (`scripts/spotify_mcp_server.py`) + snapshot (`scripts/escena_local_snapshot.py` → `data/escena_local_stats.csv`) clonados de architecting-a-band y probados. **Verificado 2026-08:** con las credenciales de desarrollo el API resuelve nombre/imagen/URI, pero **no entrega followers/popularity/géneros** (los campos ni siquiera aparecen) y `top-tracks` da **403**; el snapshot ya tolera esa respuesta (registra 0/0) y queda listo para re-ejecutarse sin cambios. **`[PENDIENTE]`** el API 2026 entrega esos números solo con **Extended Quota** (revisión de la app en el dashboard: developer.spotify.com/dashboard → app → solicitar quota). | **Extended Quota** de Spotify |

## Próximas etapas `[PROPUESTA]`

| # | Etapa | Notas |
|---|-------|-------|
| 14 | **Separación de cuentas y correo oficial** | `[PROPUESTA]` Crear correo `@fronteragrande.mx` (o subdominio) y migrar credenciales: Spotify (playlist + refresh token), Meta (apps de FB/IG + tokens de página), TikTok (app de developer), Render/Vercel/Neon (transferir a organización). Elimina dependencia de cuentas personales y permite escalar con equipo. Checklist técnico en `docs/migracion_cuentas.md`. |
| 15 | **Canales oficiales de comunicación** | `[PROPUESTA]` Crear página de Facebook y cuenta de Instagram de Frontera Grande. Publicar artistas registrados, eventos, lanzamientos, datos de la escena y reels con fuentes o autorización; enlazar siempre al sitio. Definir identidad, calendario editorial y métricas de tráfico. |
| 15b | **Publicación nativa en Instagram (API)** | ✔ **Implementado (2026-08-25):** publicación directa en IG @fronteragrande al verificar artista, con caption propio (mención clicable `@handle`, ficha, hashtags) y flujo contenedores `/media` → `/media_publish`. Controlado por `PROMO_IG=true` + `PROMO_AUTO_PUBLISH=true` en Render. Requiere permiso `instagram_content_publish` (App Review Meta) para producción; funciona en dev mode para admins. |
| 15c | Disparador de scraper en el panel de admin | ✔ CRUD hecho (`/admin`, editar/eliminar). Pendiente: botón que dispare el scraper de actividad por artista desde el panel. |
| 16 | Feeds de Bandcamp/SoundCloud y métricas públicas de Spotify | Captura puntual de oyentes mensuales desde perfiles públicos de Spotify; 16 URLs confirmadas y 11 artistas sin perfil. Pendiente ejecutar el lote inicial en producción. |
| 17 | Mapa de artistas por origen | PostGIS: la geografía de la escena (Reynosa/Matamoros/frontera). |
| 18 | **Producción y monetización** | ✔ **EN LÍNEA (agosto 2026):** web en Vercel (`fronteragrande.vercel.app`), API en Render (`fronteragrande-api.onrender.com`), BD en Neon. Deploy automático desde GitHub. Meta ya sincroniza publicaciones; pendiente: medir audiencia 90 días, evaluar patrocinio local, monitor UptimeRobot, conectar más artistas, alta en Google Search Console y AdSense (el dominio `fronteragrande.mx` ya está registrado y conectado a Vercel). Análisis financiero: `docs/finanzas.md`. |
| 19 | **Bios: Fase 2 y cierre** | ✔ **Hecho (2026-08-16):** `about`/`description` de FB y `biography` de IG para artistas **conectados a Meta** vía `backend/feed_meta.py`, integrado en el sync de 6h (`scripts/sync_feed_igfb.py`) con guarda `es_bio_clara` y nota de fuente. Pendiente: cerrar los pendientes de `data/bios_pendientes.md` (23) con curaduría desde el panel de admin. |
| 20 | **Sincronización de TikTok (Business API)** | ✔ **Hecho (backend, web y cron, 2026-08-16):** inventario (`docs/tiktok.md`), columnas `tt_user_id`/`tt_refresh_token`, `backend/feed_tiktok.py` (OAuth del creador con **PKCE**; scopes `user.info.basic`+`user.info.stats`+`video.list`), `scripts/sync_feed_tiktok.py`, botón "Conectar TikTok" en el perfil y `.github/workflows/sync-tiktok.yml` cada 6 h. **Probado con Apex Ultra en sandbox:** conectado, verificado, seguidores y videos al feed. **`[PENDIENTE]`** del artista: **aprobación** de la app (video demo + explicación) para producción y conectar al resto del inventario. |
| 21 | **Premios Frontera Grande 2027** | `[PROPUESTA]` Explorar un evento musical presencial con presentaciones en vivo y entregas de premios intercaladas. El formato inicial, categorías, nominaciones, votación y decisiones pendientes están documentados en [`docs/awards.md`](awards.md). |
| 22 | **Calendario cultural y editorial** | `[PROPUESTA]` Activar doodles animados por fecha y publicaciones coordinadas para celebraciones mexicanas, efemérides musicales y referencias regionales. Fechas, fuentes, formato y pendientes en [`docs/calendario-cultural.md`](calendario-cultural.md). |
| 23 | **App en tiendas (Android + iOS)** | `[PROPUESTA]` La web ya es **PWA instalable** (`web/app/manifest.ts` + `public/sw.js`, íconos en `public/icons/`); las tiendas solo agregan presencia/confianza. Decisión del artista: si se lanza app, **será en ambas plataformas**. Plan: **(1) Android vía TWA** — envolver la PWA con PWABuilder/Bubblewrap, verificar el dominio `fronteragrande.mx` con digital asset links (`/.well-known/assetlinks.json`) y publicar (cuenta de Google Play **$25 USD una sola vez**); **(2) iOS vía Capacitor** — wrapper nativo + pulir experiencia offline (Apple Developer **$99 USD/año**, revisión manual por envío). **Condición previa:** que el ingreso anual del sitio cubra el costo anual recurrente (~$130 USD: Apple $99 + dominio $30.70; ver `docs/finanzas.md`). |
| 24 | **Ecosistema de playlists temáticas** | `[PROPUESTA]` Expandir la playlist semanal a múltiples listas automáticas: por **género**, por **ciudad/lada**, **clásicos de la frontera**, **novedades/lanzamientos**, **artistas poco sonados**, por **categoría** y **eventos en vivo**. Detalle técnico y tabla de conceptos en `docs/playlist_semanal.md` (sección 6). Requiere Extended Quota de Spotify y parametrizar el generador. Cada playlist = ID manual + secreto + workflow dedicado. |

## En curso `[PROPUESTA]`

| # | Etapa | Estado |
|---|-------|--------|
| 18 | **Despliegue free tier (prueba con artistas)** | ✔ **Activo (2026-08):** API en Render `https://fronteragrande-api.onrender.com` (`{"estado":"ok"}`), web en Vercel `https://fronteragrande.vercel.app`, datos en Neon y Meta sincronizando en producción. Apex Ultra está verificado y muestra publicaciones de Facebook. Pendientes menores: crear monitor UptimeRobot y conectar más artistas (`docs/despliegue.md`). |
| 19 | **Playlist semanal → redes** | Template listo en `docs/publicaciones.md` (sección #R). Automatizar aviso semanal o curar manual cada lunes. Decidir tras 4 semanas de métricas. |

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
| 8 | Actualizar `/ayuda-artistas` con beneficios de verificación | ✔ Añadida la leyenda de que los proyectos sin verificar pueden ser eliminados. |
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
- Medir métricas 90 días. El dominio `fronteragrande.mx` ya está registrado y conectado.
- Patrocinios directos a locales de la zona (bares, escuelas, tiendas).

## Pendiente de producto

| Ítem | Estado |
|------|--------|
| **Dominio** | ✔ **`fronteragrande.mx`** registrado en Cloudflare por $30.70 USD por un año; conectado a Vercel y con vencimiento el 2027-08-20. Metadatos/sitemap/robots usan `https://fronteragrande.mx`. |
| **Permisos del registro** | El formulario sigue público pero ahora tiene rate-limit, validación de URLs duplicadas y advertencia de eliminación; auth más estricta (CAPTCHA/cuenta) queda pendiente de decisión. |
| **Sync de Meta** | Workflow de GitHub Actions activo cada 6 horas; primera sincronización confirmada con Apex Ultra. Pendiente conectar al resto de artistas. |
| **Finanzas** | Análisis inicial en `docs/finanzas.md`: audiencia de nicho, costos casi nulos en free tier, patrocinio local antes que APIs premium y AdSense como complemento. |

## Cómo se actualiza

- Los pasos los decide el **artista**; la IA propone e implementa lo técnico.
- Al completar una etapa, moverla a "Hecho" y actualizar `README.md`
  (sección Roadmap), `AGENTS.md` (Estado) y este documento — una sola verdad.
- Un elemento `[PENDIENTE]` no se marca hecho hasta que el dato real llegue
  y se verifique (regla: no inventar datos).
