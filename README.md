# Frontera Grande

Base de datos interactiva de los **proyectos musicales de la frontera grande de Tamaulipas** (abierta a crecer a otras regiones y disciplinas artísticas). Registra bandas, DJs, solistas, colectivos, covers y tributos, sus ciudades, enlaces de redes, dónde escucharlos/verlos, y monitorea si están **activos** a partir de su huella en internet.

> Es la versión **aplicación web** de la base de datos de [ESCENA_LOCAL.md](https://github.com/anomalyco/architecting-a-band) del proyecto **architecting-a-band**. Los datos semilla (`data/*.csv`) se mantienen en sincronía con ese proyecto. Para el **alcance y los límites** (qué es y qué no es), ver [docs/vision.md](docs/vision.md). Para costos, audiencia y monetización, ver [docs/finanzas.md](docs/finanzas.md).

## ¿Para qué sirve?

- **Base de datos y feed público de la escena**: los proyectos en un solo lugar, con previews de su contenido y enlaces directos a sus redes (el *puente*).
- **Descubrimiento**: quién está activo, qué publica, dónde escucharlo/verlo.
- **Stats de la escena**: segmentos, ciudades, estado de actividad, huella digital (seguidores por red).
- **Medir y posicionar el proyecto propio frente a la competencia** (ver `app/stats` y el análisis en `COMPETENCIA_LOCAL.md`).
- **Detectar si un proyecto sigue activo** mediante scraping (regla de actividad documentada).
- Diseñado **mobile-first** y con SEO básico (metadatos, sitemap) pensando en monetización futura.

## Estado

- **Pivote a web pública:** ✔ API REST (FastAPI) sobre la capa de datos existente · ✔ frontend Next.js responsive (móvil + desktop) · ✔ feed con miniaturas y previews (YouTube, TikTok, IG, FB) · ✔ directorio con filtros (categoría/ciudad/actividad con etiqueta y opción "Todas", géneros en chips multi-selección y leyenda de actividad) · ✔ eventos · ✔ **panel de stats interactivo** (gráficas SVG caseras: actividad temporal, ranking desglosable por red, ecosistema de redes, ciudades apiladas, dona por categoría) · ✔ **página Acerca de** (historia, qué es/no es, actividad y regla del ranking) · ✔ **identidad Frontera Grande** · ✔ sitemap/robots · ✔ **registro voluntario de artistas** (botón "Suma tu proyecto": crea el perfil; el artista lo **verifica** conectando su página de Facebook/Instagram vía OAuth, y entonces sus posts se sincronizan automáticamente; badge "Verificado" público) · ✔ **ingesta manual eliminada** (el contenido solo llega por el propio artista) · ✔ 29 proyectos + 11 eventos (27 de `architecting-a-band` + 2 registrados desde la web).
- **Despliegue:** ✔ **EN LÍNEA (agosto 2026)** — API en Render
  (`https://fronteragrande-api.onrender.com`, `{"estado":"ok"}`) + web en Vercel
  (`https://fronteragrande.vercel.app`) + PostgreSQL en Neon (29 artistas,
  11 eventos, 20 con foto, 64 videos de YouTube). Deploy automático desde
  GitHub (`baldeadr/fronteragrande`).
- **Meta (verificado):** ✔ app configurada en producción, Apex Ultra verificado y
  publicaciones de Facebook sincronizadas; workflow automático cada 6 horas;
  ✔ **panel de administración en la web** (`/admin`, editar/eliminar con token;
  pendiente el disparador del scraper); monitor UptimeRobot para mantener la API
  despierta; auth y permisos para el registro de
  artistas (por ahora es público en modo desarrollo); y **dominio**
  (decisión tomada: `fronteragrande.mx`; metadatos/sitemap/robots ya usan
  `https://fronteragrande.mx`; falta registrar/comprar y apuntar).

Desplegado **gratis** con Vercel (web) + Render (API) + Neon (PostgreSQL);
paso a paso y arquitectura: [docs/despliegue.md](docs/despliegue.md).
El **dominio** quedó decidido como **`fronteragrande.mx`** (metadatos, sitemap
y robots ya lo usan por defecto).

## Stack

| Capa | Tecnología | Nota |
|---|---|---|
| Web (pública) | **Next.js** (App Router + Tailwind) | mobile-first, SEO, metadatos |
| API | **FastAPI** | capas `lib/servicios.py` (read-models) + `lib/repository.py` (SQL) sobre `db/` |
| Datos | **SQLAlchemy 2.x** | el cambio a PostgreSQL es transparente (`DATABASE_URL`) |
| BD | **SQLite** (local) → **PostgreSQL** (producción) | PostGIS cuando exista el mapa |
| Scraping | `requests` + adaptadores por fuente | `scraper/adapters/` |

## Cómo correrla

```bash
# 1. entorno virtual + dependencias (Python)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. base de datos (crea instance/local_scene.db y la carga)
.venv/bin/python scripts/seed_db.py

# 3. todo a la vez (API :8000 + web :3000)
./scripts/dev.sh
# … o en dos terminales:
#   .venv/bin/uvicorn backend.main:app --reload --port 8000
#   cd web && npm run dev
```

La web se abre en `http://127.0.0.1:3000` y la API en `http://127.0.0.1:8000/docs`.

> **Dev (Next 16):** no corras `npm run build` mientras el `npm run dev` está
> activo (pisa `.next/` y la página deja de hidratar). El origen del navegador
> debe estar declarado en `web/next.config.ts` → `allowedDevOrigins`
> (`127.0.0.1`/`localhost`), o el dev bloquea el JS del cliente.

**Node.js es necesario** para la web (`node` y `npm`; instalar con conda: `conda install -c conda-forge nodejs`).

Para PostgreSQL (producción): crear la base, configurar `DATABASE_URL` en `.env` y volver a correr el seed.

### Tests (red de seguridad)

```bash
.venv/bin/pytest        # suite completa, usa una BD temporal aislada (no toca instance/)
```

Dependencias de test: `pytest` y `httpx` (ver `requirements-dev.txt`). La suite vive en `tests/` y cubre la API (artistas, perfil, feed, eventos, ranking, actividad) y previews/plataformas.

## Estructura

```
├── backend/
│   ├── main.py              # API REST: artistas, perfil, feed, eventos, stats (solo routing)
│   ├── dependencies.py      # Sesión + repositorios vía Depends
│   └── feed_meta.py         # OAuth + sync con la Graph API de Meta
├── web/                     # Frontend Next.js (público, responsive)
│   └── app/
│       ├── page.tsx         # Actividad de la escena (feed) + resumen de proyectos
│       ├── artistas/        # Directorio con filtros + perfil [slug]
│       ├── feed/            # Redirige a la portada (la portada es el feed)
│       ├── eventos/         # Eventos de la escena
│       ├── stats/           # Panel interactivo de indicadores (gráficas SVG propias)
│       ├── acerca-de/       # Página de la plataforma (historia, visión, ranking)
│       └── sitemap.ts       # SEO
├── db/
│   ├── models.py           # Esquema SQLAlchemy (artists, links, events, checks, feed_items)
│   ├── database.py         # Conexión (SQLite local / PostgreSQL) + migración ligera
│   └── seed.py             # Carga desde data/*.csv
├── lib/
│   ├── repository.py       # Toda la SQL en repositorios (Artist/Event/Feed/Link/Checks)
│   ├── servicios.py        # Read-models para la API (artistas_df, feed_df, ranking)
│   ├── plataformas.py      # Detección y previews por plataforma (registro OCP)
│   └── helpers.py          # Utilidades puras sin SQL (URLs, géneros, indice_alcance)
├── scraper/
│   ├── core.py             # Regla de actividad (lanzamiento/evento/feed)
│   ├── errors.py           # ScraperError (familia de excepciones de los adaptadores)
│   └── adapters/           # http.py (salud de URLs), spotify.py (API, requiere .env),
│                           # youtube.py (últimos videos vía RSS, sin API key),
│                           # oembed.py (oEmbed común con caché para IG/FB/TikTok),
│                           # imagenes.py (fotos de perfil desde las redes, sin API key)
├── data/
│   ├── escena_local.csv    # Bootstrap + export (regenerado desde la BD)
│   └── eventos.csv         # Bootstrap + export (regenerado desde la BD)
├── tests/                  # Suite pytest (BD temporal aislada)
└── scripts/
    ├── seed_db.py          # Cargar los CSV en una BD vacía (insert-if-missing)
    ├── exportar_csv.py     # Regenerar los CSV desde la BD (respaldo/sync)
    ├── actualizar_imagenes.py  # Fotos de perfil desde las redes (URLs, sin descargar)
    ├── actualizar_feed_youtube.py  # Últimos videos de YouTube por RSS (sin API key)
    ├── sync_feed_igfb.py   # Sync automático de posts FB/IG vía Meta Graph API
    ├── actualizar_oyentes_spotify.py # Captura puntual de oyentes públicos (16 perfiles)
    ├── sync_igfb.sh        # Wrapper para cron (sync Meta)
    ├── sync_local.sh       # Reconstruir la BD local desde producción (Neon)
    ├── recalcular_actividad.py  # Recalcula estado_activo (solo BD) con el feed como señal
    └── dev.sh              # Arranca API + web juntas
```

## API

`GET /api/artists` (con filtros `?segmento=&ciudad=&genero=&estado=&q=`) · `GET /api/artists/{slug}` · `GET /api/feed` · `GET /api/events` · `GET /api/stats` · `GET /api/genres` · `GET /api/health`. Documentación interactiva en `/docs`.

**Ranking de alcance:** cada artista expone `ranking: {indice, rank, total}` y `menciones`. El índice (0-100) es una **suma ponderada por plataforma** (`lib/helpers.py` → `indice_alcance`, pesos: IG 30 · FB 25 · Spotify 20 · YT 10 · TT 10 · Bandcamp 2.5 · SoundCloud 2.5): cada métrica de alcance se transforma con `log10(v+1)` y se normaliza 0-100 **entre todos los artistas** (sin la plataforma = 0, penaliza no tenerla). Las **menciones especiales** destacan al Nº 1 de cada género/ciudad/categoría con al menos 3 artistas. El ranking es global y estable aunque se filtre la lista.

## Modelo de datos

- **artists** — nombre, categoría de proyecto (Banda / Solista / DJ / Colectivo / Covers / Tributo; MC y Productor como Solista por ahora), ciudad, géneros, estado de registro, métricas por red (seguidores y reproducciones/vistas: `followers_*`, `vistas_yt`, `vistas_tt`, `reproducciones_spotify`, `reproducciones_bandcamp`, `reproducciones_soundcloud`), fechas de último lanzamiento/evento, estado de actividad, foto de perfil (`imagen_perfil` + `imagen_origen` + `imagen_actualizada`, obtenidas como URL desde las redes sin descargar). El campo interno sigue llamándose `segmento` (nombre de etiqueta de UI: **categoría**); `es_propio` (proyecto del propio universo) es un flag booleano derivado de la columna CSV del mismo nombre.
- **artist_links** — enlaces por plataforma (`ig`, `fb`, `yt`, `tt`, `spotify`, `bandcamp`, `soundcloud`, `apple`, `linktree`, `x`…); marca si es un enlace de búsqueda y no la página oficial.
- **events** — eventos de la escena: fecha, lugar, ciudad, cartel y qué demuestran.
- **activity_checks** — historial de chequeos del scraper (snapshots).
- **feed_items** — contenido reciente de los proyectos (videos, posts), sincronizado del artista conectado (Meta Graph API) o del feed de YouTube (onboarding).

## Regla de actividad

> **activo** = señal de actividad (lanzamiento, evento o feed) en los últimos **6 meses**. **en_duda** = señal entre **6 y 18 meses**, o sin señal conocida. **inactivo** = sin señal en más de **18 meses**, o pausa confirmada. Se usa siempre la señal más reciente disponible. Implementada en `scraper/core.py`; se recalcula con `scripts/recalcular_actividad.py` (actualiza la BD; el CSV se regenera con `scripts/exportar_csv.py`).

## Scraping

Adaptadores por fuente en `scraper/adapters/` y jerarquías de plataforma centralizadas en `scraper/jerarquias.py` (foto de perfil y enlace puente). Documentación detallada: [docs/scraping.md](docs/scraping.md). Para activar la sincronización FB/IG con la Graph API de Meta: [docs/meta_setup.md](docs/meta_setup.md).

### Spotify (MCP + snapshot) — clonado desde architecting-a-band

- **`scripts/spotify_mcp_server.py`** — servidor MCP local de Spotify configurado en `opencode.json` (tools en la conversación: qué suena, recientes, top, búsquedas y stats de artistas). Autorización única del artista: `python scripts/spotify_mcp_server.py --auth` (token en `scripts/.spotify_cache.json`, no versionado). Requiere `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET`/`SPOTIFY_REDIRECT_URI` en `.env` (ver `.env.example`).
- **`scripts/escena_local_snapshot.py`** — snapshot de los artistas con perfil de Spotify a `data/escena_local_stats.csv` (serie temporal: followers, popularity, géneros, top tracks). Modo dry-run sin credenciales: `--dry-run`.
- **Límite 2026 del API:** las apps en modo desarrollo **ya no reciben followers/popularity/géneros/top-tracks** (top-tracks devuelve 403); el snapshot registra **presencia** (quién tiene perfil) con 0/0. Para recuperar los números hace falta **Extended Quota** (revisión de la app en el dashboard de Spotify) — pendiente.

## Roadmap

1. ✔ MVP original en Streamlit (CRUD + lista + eventos + stats + scraper).
2. ✔ **Feed de contenido reciente:** últimos videos de los canales de YouTube (RSS, sin API key) unificados con eventos y lanzamientos. *Pendiente:* Bandcamp/SoundCloud y Spotify API.
3. ✔ **Pivote a web pública** (Next.js + FastAPI) con previews y puente a redes; mobile-first y SEO básico.
4. ✔ **Fotos de perfil** de los artistas extraídas como URL desde sus redes sin descargar imágenes (prioridad en `scraper/jerarquias.py`); fallback a inicial.
5. ✔→✘ **Ingesta asistida de posts** (botón "+ Añadir post"): se implementó como puente manual y luego **se eliminó** en el pivote a **registro voluntario** — el contenido del feed solo llega por el artista que conecta su página FB/IG (sync Meta), no por terceros.
6. ✔ **Registro voluntario de artistas desde la web** (`POST /api/artists` + onboarding: foto, últimos videos de YouTube y `estado_activo`) y **directorio pulido** (taxonomía de categoría, ciudades base única, filtros mejorados). El perfil se **verifica** conectando la página FB/IG (OAuth).
7. ✔ **Stats de redes + ranking de alcance + panel de stats interactivo:** `GET /api/stats` ampliado (`feed_serie`, `altas_por_mes`, `seguidores`/`reproducciones`, `cobertura`, `posts_90dias`, `por_ciudad`, `eventos_proximos`) y gráficas SVG caseras interactivas en `web/components/stats/` (sin dependencias de cliente).
8. ✔ **Identidad Frontera Grande + Acerca de:** renombrado en toda la web, `docs/vision.md` (fuente única de qué es/qué no es), página **Acerca de** con la regla de actividad y la fórmula del ranking (KaTeX); feed mejorado (foto real, fecha relativa, "Cargar más", H1 "Actividad de la escena").
9. ◐ **Sincronización automática con Meta Graph API** (artistas que administran su página): OAuth de producción activo y probado con Apex Ultra (perfil **verificado**); sus publicaciones de Facebook ya aparecen en el perfil. Workflow de GitHub Actions activo cada 6 horas. Pendiente conectar al resto de artistas.
10. `[PROPUESTA]` **Canales oficiales de comunicación:** crear página de Facebook y cuenta de Instagram de Frontera Grande para publicar artistas, eventos, lanzamientos, datos de la escena y reels con fuentes o autorización; enlazar al sitio, definir calendario editorial y medir el tráfico generado.
11. ✔ **Panel de administración en la web (CRUD con auth):** `/admin` protegido por `ADMIN_PASSWORD` (`X-Admin-Token`) con login en sesión, listado (`GET /api/admin/artists`), edición (`PUT /api/artists/{slug}`: datos, bio, notas, logros, estado y redes) y eliminación con confirmación. Pendiente el disparador del scraper.
12. **Mapa de artistas por origen** (PostGIS) para ver la geografía de la escena.
13. ✔ **Producción y monetización (en línea, agosto 2026):** web en Vercel (`fronteragrande.vercel.app`) + API en Render (`fronteragrande-api.onrender.com`) + PostgreSQL en Neon, deploy automático desde GitHub; Meta ya sincroniza publicaciones mediante GitHub Actions. [docs/despliegue.md](docs/despliegue.md) tiene la arquitectura y el checklist. Pendiente: UptimeRobot, conectar más artistas, el **dominio** (`fronteragrande.mx`, decisión tomada 2026-08) + AdSense/patrocinios (la estructura ya lo soporta).

Detalle con estado por etapa y dependencias: [docs/roadmap.md](docs/roadmap.md).

## Convenciones

- Todo en **español**.
- `[PENDIENTE]` = falta por definir; no inventar contenido.
- `[PROPUESTA]` = propuesta de la IA para que el artista confirme o ajuste.
- La **BD es la fuente de verdad operativa**; los CSV son **bootstrap + export**: se leen solo para crear una BD vacía (`scripts/seed_db.py`, insert-if-missing, no pisa filas existentes) y se regeneran con `scripts/exportar_csv.py` (respaldo y sync con `architecting-a-band`). `scripts/sync_local.sh` reconstruye la BD local desde producción.
- Instrucciones para asistentes de IA: ver [AGENTS.md](AGENTS.md).
