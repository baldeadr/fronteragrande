# AGENTS.md — Instrucciones para asistentes de IA

> **Este archivo es la puerta de entrada para cualquier LLM que trabaje en este proyecto.** Léelo completo antes de hacer cualquier cosa. Está escrito en Markdown plano para funcionar con cualquier herramienta (opencode, Claude Code, Cursor, etc.). Es el equivalente técnico de `architecting-a-band/AGENTS.md`, adaptado a este proyecto de aplicación web.

---

## 1. Qué es este proyecto

- Es una **aplicación web tipo base de datos** para registrar la **escena musical de la frontera grande de Tamaulipas** (bandas, DJs, solistas, colectivos, covers y tributos): ciudad, géneros, enlaces de redes, dónde escucharlos/verlos, y **actividad** detectada desde internet.
- La visión actual: **base de datos interactiva y feed públicos de artistas**, donde cada proyecto tiene **previews de su contenido** (miniaturas/videos) y **enlaces directos a sus redes** (el puente). Diseño **mobile-first** y con SEO básico, pensando en **monetización futura** (AdSense/patrocinios) como medio, no como fin.
- Para el **alcance y los límites** exactos (qué es y qué no es, y cómo crece), ver **docs/vision.md** (referencia única).
- Es la **versión ejecutable** de la base de datos documental [ESCENA_LOCAL.md](https://github.com/anomalyco/architecting-a-band) del proyecto **architecting-a-band** (universo artístico del artista). El objetivo es tener **stats de la escena y posicionar el proyecto propio frente a la competencia**.
- **Propietario:** ingeniero en mecatrónica con maestría en IA; **no escribe código**: es **arquitecto y director** de sistemas de IA. Él decide, el asistente propone y ejecuta lo técnico/documental.
- **Idioma de trabajo:** español.
- El proyecto debe ser **escalable**: si funciona a nivel local, crecer a nivel nacional/internacional (el modelo de datos ya lo permite; el mapa de artistas por origen es la siguiente etapa).

## 2. Rol del asistente de IA

- Eres **apoyo técnico**: implementas, corriges, documentas y verificas. No tomas decisiones creativas ni definitivas.
- **SÍ puedes:** modificar el código, la base de datos, añadir adaptadores de scraping, crear/actualizar documentación, proponer mejoras.
- **NO puedes:** inventar datos de artistas ni cifras sin fuente; tomar decisiones definitivas de producto; cambiar la arquitectura sin proponerlo primero.
- **Regla de oro:** si una petición contradice la arquitectura o las bases documentadas, señálalo y explica el porqué.

## 3. Cómo correr y verificar (comandos clave)

```bash
# instalar dependencias Python (primera vez)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# instalar Node (primera vez, sin sudo)
conda install -c conda-forge nodejs -y
cd web && npm install

# (re)construir la base de datos desde los CSV semilla (insert-if-missing;
# --reescribir pisa filas existentes)
.venv/bin/python scripts/seed_db.py
# regenerar los CSV desde la BD (respaldo/sync con architecting-a-band)
.venv/bin/python scripts/exportar_csv.py

# correr todo (API :8000 + web :3000)
./scripts/dev.sh

# tests del backend (red de seguridad; usa BD temporal aislada)
.venv/bin/pytest

# verificación de la web (build de producción + lint)
cd web && npm run lint && npm run build

# verificación de la API (debe devolver {"estado":"ok"})
curl -s http://127.0.0.1:8000/api/health
```

**Antes de dar una tarea por terminada, ejecutar siempre:**
0. `.venv/bin/pytest` (la suite debe quedar en verde; vivo en `tests/`).
1. `curl -s http://127.0.0.1:8000/api/health` y un muestreo de `/api/artists`, `/api/feed`, `/api/artists/{slug}`.
2. `npm run lint` y `npm run build` dentro de `web/`.

**Cuidado con el dev server de Next (lección aprendida 2026-08):** no correr
`npm run build` (producción) mientras el `npm run dev` está en marcha: el build
pisa el `.next/` del dev y este queda sirviendo bundles rotos (la página carga
pero no responde ningún control: filtros, chips, búsqueda). Además Next 16 exige
declarar el origen en `web/next.config.ts` → `allowedDevOrigins: ["127.0.0.1",
"localhost"]`; sin eso el dev **bloquea el JS del cliente** (cross-origin por
seguridad) y React no hidrata. Si algo no hidrata, revisar el log del dev
(`~/.next/dev/logs/next-development.log` o el stdout) buscando "Blocked
cross-origin".

## 4. Arquitectura

```
Next.js (web/)  →  FastAPI (backend/main.py)   →  lib/servicios.py (read-models, ranking)
                                                →  lib/plataformas.py (previews, OCP)
                                                →  lib/repository.py  (acceso a datos)
                                                →  db/ (SQLAlchemy)   →  SQLite/PostgreSQL
                                                →  scraper/ (monitoreo de actividad)
```

- **Capa de datos desacoplada:** la web (Next.js) nunca toca SQL; consume la **API REST** (`backend/main.py`). El backend está dividido en capas (SRP): los **routers** de `backend/main.py` solo rutean (sesiones/repos vía `Depends` de `backend/dependencies.py`); `lib/repository.py` concentra **toda** la SQL en repositorios (`ArtistRepository`, `EventRepository`, `FeedRepository`, `LinkRepository`, `ChecksRepository`); `lib/servicios.py` arma los **read-models** (`artistas_df`, `feed_df`, `metricas_artista`, `ranking_global`, `stats_escena`) y `lib/helpers.py` queda como utilidades puras sin SQL (URLs, géneros, `indice_alcance`). Los scripts reusan los repositorios en vez de SQL suelto. Todo es framework-agnóstico, sin Streamlit.
- **BD por defecto SQLite** (`instance/local_scene.db`); para crecimiento, `DATABASE_URL` de PostgreSQL en `.env` (ver `.env.example`).
- **Modelos:** `artists`, `artist_links`, `events`, `activity_checks` (snapshots del scraper), `feed_items` (contenido reciente del feed). `artists` incluye `bio` y foto de perfil como URL (`imagen_perfil`/`imagen_origen`/`imagen_actualizada`). La **categoría de proyecto** (campo interno `segmento`, etiqueta de UI "Categoría") tiene taxonomía **Banda / Solista / DJ / Colectivo / Covers / Tributo** (MC y Productor se registran como Solista por ahora); `es_propio` (proyecto del propio universo) es un flag booleano con columna semilla propia. `ciudad` es **ciudad base única** (si un artista opera en otra plaza, va en `notas`).
- **Scraper:** `scraper/core.py` implementa la regla de actividad; `scraper/adapters/` tiene un adaptador por fuente (`http.py` y `youtube.py` funcionales sin API key, `tiktok.py` vía oEmbed público sin API key, `instagram.py`/`facebook.py` oEmbed de posts públicos, `spotify.py` funcional si hay credenciales en `.env`) y `imagenes.py` (foto de perfil como URL sin API key; IG/FB/TikTok suelen bloquear). Los adaptadores lanzan excepciones de la familia `scraper/errors.py` (`ScraperError`) para que callers no acoplen a excepciones concretas; los oEmbeds IG/FB/TikTok comparten caché y lógica en `scraper/adapters/oembed.py`. La conversión de enlaces a previews y la detección de plataforma están centralizadas en `lib/plataformas.py` (registro `PREVIEWS`, patrón Open/Closed: añadir una fuente = añadir su adaptador y su entrada en el registro, sin tocar `backend/main.py`). Las **jerarquías de plataformas** (foto de perfil y enlace puente) están centralizadas en `scraper/jerarquias.py` y documentadas en `docs/scraping.md` — cambiar una jerarquía se hace solo ahí. La **sincronización automática de posts FB/IG** (artistas que administran su página) vive en `backend/feed_meta.py` (OAuth + Graph API, requiere `META_APP_ID`/`META_APP_SECRET` en `.env`) y `scripts/sync_feed_igfb.py`; los tokens de página nunca se exponen en la API.
- **Bios y géneros con fuente:** cadena de fuentes en `scraper/adapters/` (`bandcamp.py` → bio+tags, `soundcloud.py` → bio vía `__sc_hydration`, `youtube.py` → `youtube_about`); Spotify se omite porque no expone bio pública. `scripts/proponer_bios.py` recorre la cadena y **escribe directo** cuando la fuente está clara (`lib/helpers.es_bio_clara` y sin homónimos: ni advertidos en `notas` ni en `CONFLICTOS_CONOCIDOS`), con nota `Bio de <Plataforma> (YYYY-MM-DD)` en `notas`; lo ambiguo va al reporte `data/bios_pendientes.md` para curaduría. El CSV se regenera al final (BD = fuente de verdad). Fase 2 pendiente: `about`/`description` (FB) y `biography` (IG) vía Meta para artistas conectados.
- **Spotify (MCP + snapshot, clonado de architecting-a-band):** `scripts/spotify_mcp_server.py` expone tools MCP configuradas en `opencode.json` (en vivo: lo que suena, recientes, top, búsquedas, stats de artistas; autorización única `--auth`, token en `scripts/.spotify_cache.json`, no versionado) y `scripts/escena_local_snapshot.py` toma snapshots de la escena a `data/escena_local_stats.csv` (serie temporal, una fila por artista/fecha). Requieren `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET`/`SPOTIFY_REDIRECT_URI` en `.env`. **Límite 2026:** apps en modo desarrollo ya no reciben followers/popularity/géneros/top-tracks (top-tracks = 403); el snapshot registra solo **presencia** con 0/0 hasta solicitar **Extended Quota** en el dashboard. Dependencias: `mcp>=1.9,<2` y `spotipy` (la v2 de mcp cambia la API de FastMCP).
- **La BD es la fuente de verdad operativa.** `data/escena_local.csv` y `data/eventos.csv` son **bootstrap + export**: se leen solo para crear una BD vacía y se regeneran con `scripts/exportar_csv.py` (respaldo y sync con `architecting-a-band`). El seed hace **insert-if-missing por `slug`** (no pisa filas existentes: la BD tiene estado vivo como imágenes, verificación, actividad y métricas); `scripts/seed_db.py --reescribir` fuerza un upsert solo para reconstruir. `scripts/sync_local.sh` reconstruye la BD local descartable desde la de producción (Neon). `es_propio` se lee de la columna CSV homónima (devuelve `TRUE` solo para el proyecto propio).
- **Previews y feed como señal de actividad:** el feed y los perfiles muestran previews estilo YouTube (YouTube y TikTok con miniatura y play; Instagram, Facebook, Spotify y Mixcloud embebidos; ver `docs/scraping.md`). El **feed es la bitácora de actividad** del proyecto: un elemento reciente (≤ 6 meses) alimenta `estado_activo` vía `scripts/recalcular_actividad.py` (actualiza la BD; el CSV semilla se regenera con `scripts/exportar_csv.py`). Regla: activo ≤ 6 meses · en_duda 6–18 meses o sin señal · inactivo > 18 meses o pausa confirmada (`scraper/core.py`). **La ingesta es solo automática y la hace el propio artista:** al conectar su página FB/IG vía Meta Graph API (`scripts/sync_feed_igfb.py` + cron `scripts/sync_igfb.sh`; guía: `docs/meta_setup.md`), vía el feed de YouTube del onboarding (`lib/servicios.onboarding_artista`) o vía los **lanzamientos** (`scripts/sync_lanzamientos.py` + workflow `sync-lanzamientos.yml`: Spotify por API oficial, Bandcamp/SoundCloud/Beatport/Mixcloud por adaptadores; solo material propio y **sin ventana temporal** —entra todo el historial, tope `SYNC_LANZAMIENTOS_LIMIT` por plataforma—, anti-duplicados por URL en `FeedRepository.crear_si_nuevo`). No existe ingesta manual (el botón "+ Añadir post" y `POST /api/artists/{slug}/feed` se eliminaron: **no reintroducirlos**).
- **Ranking de alcance:** `lib/helpers.py` (`indice_alcance`) calcula un índice 0-100 por artista = suma ponderada por plataforma (pesos: IG 29 · FB 24 · Spotify 19 · YT 9 · TT 9 · Bandcamp 2.5 · SoundCloud 2.5 · Beatport 3 · Mixcloud 2); cada métrica de alcance se transforma con `log10(v+1)` y se normaliza 0-100 entre todos los artistas (sin la plataforma cuenta 0). La API expone `ranking: {indice, rank, total}` y `menciones` (Top 3 de la escena + Top 3 por género/ciudad/categoría, mínimo 3 participantes y puntaje real) en listado y detalle; `scripts/recalcular_actividad.py` no afecta el ranking. No inventar métricas: el ranking solo usa datos con fuente.

## 5. Convenciones del proyecto (crítico)

- **Idioma:** todo en español (código, mensajes de UI, documentación, commits).
- **`[PENDIENTE]`** = información que falta por definir; no inventar contenido donde aparece.
- **`[PROPUESTA]`** = propuesta del asistente para que el artista confirme o ajuste.
- **No inventar datos:** cifras de seguidores, reproducciones/vistas, fechas, lanzamientos y logros deben venir de la BD (sembrada desde los CSV semilla) o de investigación con fuente.
- **Una sola verdad:** la BD es la fuente de verdad operativa; si un dato cambia, actualizar las referencias cruzadas (BD, CSV exportado, documentación, código).
- **No escribir código con comentarios innecesarios:** seguir el estilo existente (docstrings de módulos/funciones en español, sin comentarios de relleno).
- **Bitácora (opcional, patrón del proyecto padre):** si se decide llevar historial de decisiones, seguir el formato de `architecting-a-band/BITACORA.md` (entradas en `bitacora/YYYY-MM.md`, no se reescriben).

## 6. Estado actual

- **Fase:** web pública **EN LÍNEA** (agosto 2026): API en Render `https://fronteragrande-api.onrender.com` + web en Vercel `https://fronteragrande.vercel.app` + PostgreSQL en Neon (ver [README.md](README.md) → Estado).
- **Decidido:** Next.js + FastAPI + SQLAlchemy + SQLite (→ PostgreSQL cuando escale). Sin mapa por ahora (siguiente etapa: PostGIS).
- **Web Push:** la PWA registra suscripciones VAPID en `push_subscriptions`; las altas de artistas y los posts nuevos de Meta disparan avisos, y el admin puede enviar broadcasts. En iPhone requiere instalar primero la PWA.
- **Hecho:** API REST · web mobile-first con directorio, perfiles, feed con previews de YouTube/IG/FB, eventos, **panel de stats interactivo** (gráficas SVG caseras en `web/components/stats/`: actividad temporal, ranking desglosable por red, ecosistema de redes, ciudades apiladas, dona por categoría; `GET /api/stats` ampliado con `feed_serie`, `altas_por_mes`, `seguidores`/`reproducciones`, `cobertura`, `posts_90dias`, `por_ciudad`, `eventos_proximos`), **identidad Frontera Grande** (renombrado; `docs/vision.md` es la fuente única de alcance y límites) y **página Acerca de** (historia, "cómo explorar la plataforma", regla de actividad y fórmula del ranking con KaTeX), fotos de perfil de los artistas desde sus redes (URLs), SEO básico (sitemap/robots/metadatos), **PWA instalable** (`app/manifest.ts` + `public/sw.js` con cache de la shell y de estáticos de Next, sin tocar la API externa; iconos en `web/public/icons/`), **registro voluntario de artistas + verificación por OAuth**: el botón "Suma tu proyecto" crea el perfil (`POST /api/artists`), y al conectar su página FB/IG (`backend/feed_meta.py`, valida que la cuenta autorizada administre la página registrada) el perfil queda **verificado** (badge público "Verificado", `estado_registro` → `confirmado (artista, fecha)`) y sus posts se sincronizan automáticamente; **ingesta manual eliminada** (`POST /api/artists/{slug}/feed`, `FormAgregarFeed` y `scripts/registrar_feed.py` ya no existen: **no reintroducirlos**), backend por **capas** (routers → `lib/servicios.py`/`lib/plataformas.py` → `lib/repository.py`), **suite de tests** (`.venv/bin/pytest`, red de seguridad en `tests/`), **directorio pulido**: taxonomía de categoría (Banda/Solista/DJ/Colectivo/Covers/Tributo, MC y Productor como Solista), ciudades normalizadas a base única con dropdown, filtros con etiqueta visible y opción "Todas", géneros en chips de selección múltiple y leyenda de actividad bajo los filtros. **Panel de administración** (`/admin`, protegido por `ADMIN_PASSWORD` vía `X-Admin-Token`): login en sesión, listado con `GET /api/admin/artists`, edición (`PUT /api/artists/{slug}`: nombre, ciudad, categoría, géneros, bio, notas, logros, estado de actividad y redes) y eliminación (`DELETE /api/artists/{slug}`) con confirmación; la lógica de edición vive en `lib/servicios.editar_artista` (solo aplica campos presentes, conserva enlaces de búsqueda). Valores huérfanos sin fuente marcados `[PENDIENTE]` en `notas` (ej. seguidores IG de isquemia/vaale). **Bios y géneros con fuente (Fase 1):** cadena Bandcamp→SoundCloud→YouTube en `scraper/adapters/` (sin API key) y `scripts/proponer_bios.py` que escribe directo lo claro con nota de fuente en `notas` y deja lo ambiguo en `data/bios_pendientes.md` (primera corrida 2026-08-16: 3 bios escritas; Distraught y Don Bravo quedaron pendientes por homónimos). **Bios y géneros con fuente (Fase 2):** para artistas conectados, bio desde Meta (`about`/`description` de FB y `biography` de IG vía `backend/feed_meta.py`) integrada en `scripts/sync_feed_igfb.py`. **Sincronización de TikTok (Business API):** `backend/feed_tiktok.py` (OAuth del creador con **PKCE**: login/callback/desconectar + `user.info.basic` + `video.list`; rota el refresh token y nunca expone tokens), `scripts/sync_feed_tiktok.py`, columnas `tt_user_id`/`tt_refresh_token` (migración ligera en `db/database.py`), botón "Conectar TikTok" en el perfil (`web/components/ConexionTikTok.tsx`) y `verificado` = `(fb_page_token or tt_refresh_token) and estado_registro`. **Cierre de datos automáticos (2026-08-19):** seguidores de **Facebook/Instagram** en el sync de Meta (`pagina_seguidores`/`ig_seguidores`, campo `followers_count`), **lanzamientos propios en el feed** (`scripts/sync_lanzamientos.py` + workflow `sync-lanzamientos.yml` cada 6 h: Spotify por API oficial `/artists/{id}/albums`, Bandcamp por cuadrícula HTML, SoundCloud por api-v2 con `client_id` del bundle, Beatport por `__NEXT_DATA__`, Mixcloud por API REST pública; todos con anti-duplicados por URL y **sin ventana temporal** —entra todo el historial de lanzamientos, tope `SYNC_LANZAMIENTOS_LIMIT` por plataforma—; el perfil organiza ese contenido en **pestañas** Todo/Posts/Video/Música/Eventos vía `web/components/ContenidoPerfil.tsx`), **fotos de perfil por API primero** (`scraper/adapters/imagenes.py`: Meta `picture`/`profile_picture_url`, YouTube Data API, avatar de TikTok en su sync) con fallback a scraping, y **métricas de YouTube visibles de nuevo** en el directorio (revertido lo ocultado en `be8d644`). **Eventos (fase 2026-08):** **CRUD de eventos en el panel de admin** (pestaña "Eventos": alta/edición/baja vía `POST/PUT/DELETE /api/admin/events`, lógica en `EventRepository`), **ingesta automática desde Meta** (permiso `pages_events` en el scope OAuth + `backend/feed_meta.py::pagina_eventos` + `scripts/sync_eventos_meta.py` + workflow `sync-eventos-meta.yml` cada 6 h; los toquines que el artista publica en su página FB se registran en `events` sin duplicar por fuente), **página pública de eventos pulida** (secciones "Próximos" y "Pasados", sin el aviso de "en construcción") y **eventos como señal de actividad** (`lib/servicios.recalcular_actividad` actualiza `ultimo_evento` desde la tabla `events` —solo avanza, no regresa— y aplica la regla; lo llaman los sync y los endpoints del admin tras cada cambio).
- **Pendiente:** conectar al resto de artistas que administran su página Meta (la app está configurada en producción; **Apex Ultra quedó verificado pero su token de Meta fue invalidado por Facebook** —cambio de contraseña/sesión—, hay que **reconectar** desde su perfil para que el sync de posts y seguidores vuelva a funcionar; la reconexión también concede el permiso `pages_events` nuevo para la ingesta de eventos), **verificar** que el secret `YOUTUBE_API_KEY` esté en GitHub Actions y que `sync-youtube.yml` corrió, crear el monitor **UptimeRobot**, disparador del **scraper** en el panel de admin (el CRUD ya está hecho), auth y **permisos** para el registro de artistas (el formulario hoy es público) y el **dominio** (decisión tomada: **`fronteragrande.mx`**, 2026-08; metadatos/sitemap/robots ya usan `https://fronteragrande.mx`; falta registro y apuntar). **Bios (cierre):** la Fase 2 ya escribe bio desde Meta (`about`/`description` de FB y `biography` de IG vía `backend/feed_meta.py`, integrado en `scripts/sync_feed_igfb.py` con guarda `es_bio_clara` y nota de fuente); falta curaduría de los pendientes de `data/bios_pendientes.md` desde el admin. **Sincronización de TikTok (backend, web y cron hechos):** `backend/feed_tiktok.py` (OAuth del creador con **PKCE**, scopes `user.info.basic` + `user.info.stats` + `video.list`), `scripts/sync_feed_tiktok.py`, `.github/workflows/sync-tiktok.yml` (cada 6 h, paralelo a Meta) y botón "Conectar TikTok" en el perfil (paralelo a Meta). App en TikTok for Developers (modo **sandbox**): Apex Ultra quedó conectado y verificado (2026-08-16) y su sync ya trae seguidores y videos al feed (en sandbox funcionan `user.info.stats` y `video.list`). Requiere los secrets `TIKTOK_CLIENT_KEY`/`TIKTOK_CLIENT_SECRET` en GitHub Actions. Falta: **aprobación** de la app (video demo + explicación) para producción y conectar al resto del inventario (`docs/tiktok.md`). **Beatport:** el adaptador está listo pero no hay artistas con enlace de Beatport en el inventario.
- **Despliegue (ACTIVO):** repo remoto `github.com/baldeadr/fronteragrande` (rama `main`), `render.yaml` (blueprint API), `vercel.json` (solo `framework: nextjs`; root dir `web` puesto en el dashboard de Vercel), `requirements-prod.txt` (deps mínimas de la API, sin matplotlib/wordcloud/mcp/spotipy), CORS configurable por env (`CORS_ORIGINS` en `backend/main.py`), driver PostgreSQL `psycopg` con normalización de URL en `db/database.py`, rutas del seed independientes del directorio (`db/seed.py`) y Meta OAuth configurado en Render. Re-ejecutar sobre Neon: `scripts/actualizar_imagenes.py` y `scripts/actualizar_feed_youtube.py` con `DATABASE_URL` de Neon. Guía: `docs/despliegue.md`.
- El artista **no escribe código**: las tareas se deben proponer y, si son técnicas, implementarse directamente con verificación.

## 7. Cómo actualizar la documentación

1. Al cambiar arquitectura o modelo de datos, actualizar **README.md** (índice y modelo), **docs/roadmap.md** (si afecta a una etapa del roadmap) y este archivo (si afecta a instrucciones de trabajo).
2. Mantener consistencia entre documentos y código.
3. Preferir editar archivos existentes; crear nuevos solo si aportan valor real.
4. Si una instrucción es ambigua o requiere una decisión de producto, **preguntar al artista antes de actuar**.
