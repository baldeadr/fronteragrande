# Arquitectura Integrada - Frontera Grande

> Diagrama Mermaid de la arquitectura completa: frontend, backend, base de datos, scrapers, APIs externas, jobs y despliegue.

```mermaid
flowchart TD
    %% ========== USUARIO ==========
    U[Usuario / Artista] -->|Navega| WEB
    U -->|Registra proyecto| WEB
    U -->|Conecta Meta/TikTok| WEB

    %% ========== FRONTEND (Next.js) ==========
    subgraph FE[Frontend - Next.js 16 (web/)]
        direction TB
        WEB[App Router + React 19] --> DIR[Directorio /artistas]
        WEB --> DET[Perfil /artistas/[slug]]
        WEB --> STA[Stats /stats]
        WEB --> ADM[Admin /admin]
        WEB --> ONB[Onboarding /ayuda-artistas]
        WEB --> PWA[PWA instalable + Push]
    end

    %% ========== BACKEND (FastAPI) ==========
    subgraph BE[Backend - FastAPI (backend/)]
        direction TB
        API[main.py :8000] --> RT[Routers /api/*]
        RT --> DEP[Dependencies / Depends]
        DEP --> SV[lib/servicios.py]
        DEP --> PL[lib/plataformas.py]
        DEP --> RP[lib/repository.py]
        DEP --> HP[lib/helpers.py]
        SV --> RP
        PL --> RP
        RP --> DB[(Base de Datos)]
    end

    %% ========== BASE DE DATOS ==========
    subgraph DB[Base de Datos - SQLAlchemy]
        direction TB
        DB --> ART[artists]
        DB --> LNK[artist_links]
        DB --> EVT[events]
        DB --> FED[feed_items]
        DB --> CHK[activity_checks]
        DB --> SPT[spotify_listener_snapshots]
        DB --> SET[settings]
        DB --> PUSH[push_subscriptions]
        DB --> PROM[promo_posts]
        DB --> ALT[alta_registros]
    end

    %% ========== SCRAPERS / ADAPTERS ==========
    subgraph SC[Scrapers & Adapters (scraper/)]
        direction TB
        CORE[core.py - regla actividad] --> ADAP[adapters/]
        ADAP --> HTTP[http.py]
        ADAP --> YT[youtube.py]
        ADAP --> TT[tiktok.py]
        ADAP --> IG[instagram.py]
        ADAP --> FB[facebook.py]
        ADAP --> SP[spotify.py]
        ADAP --> BC[bandcamp.py]
        ADAP --> SC2[soundcloud.py]
        ADAP --> IMG[imagenes.py]
        ADAP --> OEM[oembed.py]
        ADAP --> BT[beatport.py]
        ADAP --> MC[mixcloud.py]
        ERR[errors.py - ScraperError]
    end

    %% ========== APIs EXTERNAS ==========
    subgraph EXT[APIs Externas]
        direction TB
        META[Meta Graph API\nFB Pages + IG Business] -->|OAuth + tokens| BE
        TIKTOK[TikTok Business API\nCreator OAuth PKCE] -->|OAuth + tokens| BE
        YTAPI[YouTube Data API v3] -->|API Key| BE
        SPOTIFY[Spotify Web API\nMCP + OAuth] -->|Client Credentials| BE
        BCWEB[Bandcamp HTML] -->|Scraping| BE
        SCWEB[SoundCloud API v2] -->|Client ID| BE
        BTWEB[Beatport __NEXT_DATA__] -->|Scraping| BE
        MCWEB[Mixcloud REST] -->|API Pública| BE
    end

    %% ========== JOBS / SYNC SCRIPTS ==========
    subgraph JOBS[Jobs & Sync (scripts/ + GitHub Actions)]
        direction TB
        SYNC_META[scripts/sync_feed_igfb.py\n+ sync_eventos_meta.py] -->|Cada 6h| META
        SYNC_TT[scripts/sync_feed_tiktok.py] -->|Cada 6h| TIKTOK
        SYNC_YT[scripts/sync_youtube_stats.py] -->|Semanal| YTAPI
        SYNC_RLS[scripts/sync_lanzamientos.py] -->|Cada 6h| SPOTIFY & BCWEB & SCWEB & BTWEB & MCWEB
        SYNC_PLAY[scripts/generar_playlist_semanal.py] -->|Lunes| SPOTIFY
        SNAPSHOT[scripts/escena_local_snapshot.py] -->|Snapshot| DB
        RECALC[scripts/recalcular_actividad.py] -->|Trigger| DB
        PROP_BIO[scripts/proponer_bios.py] -->|Bajo demanda| ADAP
        IMPORT_CUR[scripts/importar_curado3.py] -->|Bootstrap| DB
        EXPORT_CSV[scripts/exportar_csv.py] -->|Backup| CSV[(data/escena_local.csv)]
        CARR[scripts/generar_carruseles.py] -->|Marketing| IMG_OUT[carrucel/]
    end

    %% ========== DESPLIEGUE ==========
    subgraph DEPLOY[Despliegue - Produccion]
        direction TB
        GH[GitHub main] -->|Push| VERCEL[Vercel --> fronteragrande.mx]
        GH -->|Push| RENDER[Render --> fronteragrande-api.onrender.com]
        RENDER --> NEON[(Neon PostgreSQL)]
        VERCEL -->|HTTPS| API
        RENDER -->|HTTPS| DB
    end

    %% ========== FLUJOS CLAVE ==========
    %% Onboarding artista
    ONB -.-->|POST /api/artists| API
    API -.-->|Crea artista + snapshot YT| DB

    %% Verificación Meta/TikTok
    WEB -.-->|OAuth callback| API
    API -.-->|Guarda tokens| DB
    API -.-->|Dispara sync| SYNC_META
    API -.-->|Publica promo| PROM

    %% Feed automático
    SYNC_META -.-->|Posts + eventos| DB
    SYNC_TT -.-->|Videos| DB
    SYNC_RLS -.-->|Lanzamientos| DB

    %% Ranking & Ligas
    SV -->|ranking_global / ranking_ligas| API
    HP -->|calcular_indice_universal + clasificar_por_indice| SV

    %% Activity check
    RECALC -.-->|Actualiza estado_activo| DB

    %% Push notifications
    PWA -.-->|Registra suscripción| API
    API -.-->|Guarda en push_subscriptions| DB
    SYNC_META -.-->|Nuevo post verificado| PUSH
    ADM -.-->|Broadcast| PUSH

    %% Estilos
    classDef fe fill:#1e293b,color:#fff,stroke:#38bdf8
    classDef be fill:#0f172a,color:#fff,stroke:#22d3ee
    classDef db fill:#166534,color:#fff,stroke:#4ade80
    classDef sc fill:#7c2d12,color:#fff,stroke:#fb923c
    classDef ext fill:#4c1d95,color:#fff,stroke:#a855f7
    classDef job fill:#92400e,color:#fff,stroke:#fbbf24
    classDef dep fill:#1f2937,color:#fff,stroke:#6b7280

    class WEB,DIR,DET,STA,ADM,ONB,PWA fe
    class API,RT,DEP,SV,PL,RP,HP be
    class DB,ART,LNK,EVT,FED,CHK,SPT,SET,PUSH,PROM,ALT db
    class CORE,ADAP,HTTP,YT,TT,IG,FB,SP,BC,SC2,IMG,OEM,BT,MC,ERR sc
    class META,TIKTOK,YTAPI,SPOTIFY,BCWEB,SCWEB,BTWEB,MCWEB ext
    class SYNC_META,SYNC_TT,SYNC_YT,SYNC_RLS,SYNC_PLAY,SNAPSHOT,RECALC,PROP_BIO,IMPORT_CUR,EXPORT_CSV,CARR job
    class GH,VERCEL,RENDER,NEON dep
```

---

## Descripción por Capas

### 1. Frontend (Next.js 16, App Router)
- **Páginas**: Directorio (`/artistas`), Perfil (`/artistas/[slug]`), Stats (`/stats`), Admin (`/admin`), Acerca de, Onboarding.
- **Componentes clave**: `InsigniaNivel`, `RankingFiltrable` (ranking por grupos Escena/Ligas), `Directorio` (filtros: Liga, Categoría, Ciudad, Géneros, Estado), `ContenidoPerfil` (pestañas Todo/Posts/Video/Música/Eventos), `EstadoBadge`, `Avatar`, `ConsumoAnalisis`.
- **PWA**: `manifest.ts`, `sw.js` (cache shell + estáticos), iconos en `public/icons/`, Web Push (VAPID) con suscripciones en `push_subscriptions`.
- **API Client**: `web/lib/api.ts` (typed fetch wrappers).

### 2. Backend (FastAPI, arquitectura por capas)
| Capa | Archivo | Responsabilidad |
|------|---------|-----------------|
| Routers | `backend/main.py` | Endpoints REST, validación, cache (`MemoryCache` TTL 5 min), auth admin (`X-Admin-Token`), invalidación de caché (`POST /api/admin/cache-invalidate`), CORS |
| Servicios | `lib/servicios.py` | Read-models (`artistas_df`, `feed_df`), rankings (`ranking_global`, `ranking_ligas`), métricas, edición, onboarding |
| Plataformas | `lib/plataformas.py` | Registro `PREVIEWS` (OCP) -> previews YouTube/TikTok/IG/FB/Spotify/SC/Mixcloud; detección plataforma; helper URLs |
| Repositorio | `lib/repository.py` | **Todo** el SQL: `ArtistRepository`, `EventRepository`, `FeedRepository`, `LinkRepository`, `ChecksRepository` |
| Helpers | `lib/helpers.py` | `calcular_indice_universal`, `clasificar_por_indice`, normalización URLs, géneros, slug, `es_bio_clara` |

### 3. Base de Datos (SQLAlchemy + SQLite / PostgreSQL)
- **SQLite** por defecto (`instance/local_scene.db`).
- **PostgreSQL** en producción vía `DATABASE_URL` (Neon) - driver `psycopg`, normalización URL en `db/database.py`.
- **Migraciones ligeras**: `ALTER TABLE ADD COLUMN IF NOT EXISTS` en `db/database.py` (columna `nivel`, `tt_user_id`, `tt_refresh_token`, etc.).
- **Modelos**: `Artist`, `ArtistLink`, `Event`, `FeedItem`, `ActivityCheck`, `SpotifyListenerSnapshot`, `Setting`, `PushSubscription`, `PromoPost`, `AltaRegistro`.

### 4. Scrapers & Adapters (Open/Closed Principle)
- `lib/plataformas.py` registra `PREVIEWS` -> añadir fuente = nuevo adapter + entrada en registro (sin tocar `main.py`).
- **Adapters funcionales sin API key**: HTTP, YouTube (oEmbed + Data API), TikTok (oEmbed público), Instagram/FB (oEmbed posts), Bandcamp, SoundCloud, Beatport, Mixcloud.
- **Con credenciales**: Spotify (MCP + OAuth), Meta Graph API (OAuth pages), TikTok Business (PKCE).
- **Jerarquías centralizadas** en `scraper/jerarquias.py` (foto de perfil y enlace puente).
- Excepciones unificadas: `scraper/errors.py` -> `ScraperError`.

### 5. APIs Externas & Sync Automático
| Fuente | Qué sincroniza | Frecuencia | Auth |
|--------|----------------|------------|------|
| **Meta (FB/IG)** | Posts, eventos, seguidores, foto perfil, bio | Cada 6h (GH Actions) | OAuth Page Token |
| **TikTok** | Videos, seguidores, foto | Cada 6h | Creator OAuth PKCE |
| **YouTube** | Suscriptores, vistas | Semanal | API Key |
| **Spotify** | Oyentes mensuales (si Extended Quota), lanzamientos | Cada 6h | Client Credentials + OAuth playlist |
| **Bandcamp / SC / Beatport / Mixcloud** | Lanzamientos (historial completo, sin ventana temporal) | Cada 6h | HTML / API pública |
| **Promo IG @fronteragrande** | Post bienvenida al verificar artista | Evento | `instagram_content_publish` (App Review) |

### 6. Jobs & Scripts (scripts/ + GitHub Actions Workflows)
- `sync-feed-igfb.yml` / `sync-tiktok.yml` / `sync-lanzamientos.yml` / `sync-eventos-meta.yml` / `sync-youtube.yml` / `sync-playlist.yml`
- `scripts/seed_db.py` (insert-if-missing por `slug`; `--reescribir` = upsert)
- `scripts/exportar_csv.py` (BD -> CSV, backup + sync con architecting-a-band)
- `scripts/recalcular_actividad.py` (regla ≤6m activo / 6-18m en_duda / >18m inactivo)
- `scripts/proponer_bios.py` + `data/bios_pendientes.md` (curación manual)
- `scripts/generar_carruseles.py` (marketing IG)
- `scripts/spotify_mcp_server.py` + `scripts/escena_local_snapshot.py` (serie temporal)

### 7. Despliegue
- **Repo**: `github.com/baldeadr/fronteragrande` (rama `main`)
- **API**: Render (blueprint `render.yaml`), Python 3.11, `requirements-prod.txt`, PostgreSQL Neon, variables de entorno en dashboard.
- **Web**: Vercel (`vercel.json` + `framework: nextjs`, root `web/`), build `npm run build`, `next.config.ts` con `allowedDevOrigins`.
- **CI**: GitHub Actions (lint, build, tests, sync workflows).
- **Dominio**: `fronteragrande.mx` (Cloudflare -> Vercel), DNS + TLS automático.

---

## Flujos Críticos

1. **Alta de artista** -> `POST /api/artists` (validaciones, rate-limit, onboarding YT + SC/Mixcloud seguidores + oyentes Spotify) -> `ArtistRepository.crear` -> `FeedRepository` (primer video YT) -> BD.
2. **Verificación Meta** -> OAuth callback -> guarda `fb_page_token`/`ig_user_id` -> `verificado = true` -> dispara `sync_feed_igfb` + promo IG.
3. **Verificación TikTok** -> PKCE callback -> guarda `tt_user_id`/`tt_refresh_token` -> `verificado = true` -> dispara `sync_feed_tiktok`.
3. **Feed automático** -> GH Action cada 6h -> adapters -> `FeedRepository.crear_si_nuevo` (anti-dup por URL) -> `recalcular_actividad` actualiza `estado_activo`.
4. **Ranking** -> `lib/servicios.ranking_por_ligas` (4 ligas + universal) -> posiciones `rank_liga`/`rank_universal` derivadas del **índice universal** (`calcular_indice_universal`, techos fijos, sin re-normalización por liga). El desglose A/C (`indice_alcance`/`indices_audiencia_consumo`) es solo informativo. El ranking y `nivel`/`catalogado` se calculan del **mismo** `df` en cada request (la API cachea la respuesta completa 5 min, no el ranking por separado); los syncs llaman `POST /api/admin/cache-invalidate` (vía `scripts/invalidar_cache_api.sh`) para renovar la caché.
5. **Ligas** -> `calcular_indice_universal` (techos fijos: IG/FB/TT/YT 50M, Spotify oyentes 20M —bajado de 50M el 2026-09-14: el oyente mensual es consumo intencional—, etc.) + `clasificar_por_indice` (umbrales fijos: **≥60 Ligas Mayores**, **≥50 Emergente**) + **Leyenda** (manual con fuente en `notas`).
6. **Push** -> PWA registra suscripción -> `lib/notificaciones` envía VAPID -> admin broadcast / nuevo verificado / nuevo post Meta.

---

## Convenciones Clave (AGENTS.md)
- **BD = fuente de verdad** -> `exportar_csv.py` regenera CSV semilla.
- **No inventar datos**: seguidores, vistas, fechas, logros -> BD o fuente documentada.
- **`[PENDIENTE]`** = falta definir; **`[PROPUESTA]`** = propuesta IA para confirmar.
- **Idioma**: español en código, UI, docs, commits.
- **Tests**: `.venv/bin/pytest` (BD temporal aislada, 195 tests).
- **Verificación pre-deploy**: `pytest` + `curl /api/health` + `npm run lint && npm run build`.