# Despliegue en línea (free tier) — Frontera Grande

Guía para llevar el sitio a internet **gratis o casi gratis**, con el dominio
final (`fronteragrande.mx`) pendiente. Para la prueba con artistas se usa el
dominio gratuito de cada plataforma y el dominio se apunta después.

> **Estado: ✔ DESPLEGADO en línea (2026-08).** La web y la API están públicas
> bajo los dominios de prueba (ver tabla). El botón de **conexión con Meta
> (verificado)** queda pendiente de crear la app de Meta (sección 6).

Checklist de despliegue (✔ = hecho, ☐ = pendiente):

| Paso | Estado |
|---|---|
| 1. Repo en GitHub | ✔ `baldeadr/fronteragrande` |
| 2. Neon con datos semilla | ✔ 29 artistas, 11 eventos |
| 3. API en Render | ✔ `fronteragrande-api` (health `{"estado":"ok"}`) |
| 4. Fotos y feed de YouTube | ✔ 20 con foto · 64 videos |
| 5. Web en Vercel | ✔ `fronteragrande.vercel.app` |
| 6. Conexión Meta (verificado) | ☐ requiere app de Meta |
| 7. UptimeRobot (mantener API despierta) | ☐ pendiente de crear monitor |
| 8. Dominio `fronteragrande.mx` | ☐ sin registrar |

## Cómo están conectados los servicios

```mermaid
flowchart LR
    subgraph Navegador[Usuario — artista / visitante]
        U[Browser]
    end

    subgraph Vercel[Vercel · Web Next.js]
        W["fronteragrande.vercel.app"]
        W -.- Wenv["NEXT_PUBLIC_API_URL<br/>NEXT_PUBLIC_SITE_URL"]
    end

    subgraph Render[Render · API FastAPI]
        A["fronteragrande-api.onrender.com"]
        Ar["render.yaml + uvicorn<br/>backend.main:app"]
        Aenv["CORS_ORIGINS<br/>META_* · WEB_URL · DATABASE_URL"]
        A -.- Ar
    end

    subgraph Neon[Neon · PostgreSQL]
        DB[("neondb<br/>players · eventos · feed")]
    end

    subgraph GH[GitHub · baldeadr/fronteragrande]
        R["repo main<br/>(código fuente)"]
    end

    U -->|"HTTPS"| W
    W -->|"GET /api/* con NEXT_PUBLIC_API_URL"| A
    A -->|"SQLAlchemy + psycopg<br/>con DATABASE_URL"| DB

    R -.->|"deploy automático c/ push"| W
    R -.->|"Blueprint render.yaml"| A
```

```
Navegador ──HTTPS──> Vercel (web) ──GET /api/*──> Render (API) ──SQL──> Neon (PostgreSQL)
    ▲                                                            ▲
    └── celdas de Meta (OAuth, sección 6) ──hacia Render─────────┘
GitHub ─deploy automático─> Vercel + Render (leyendo render.yaml)
UptimeRobot ─ping 14 min─> Render (mantiene la API despierta)
```

Arquitectura en producción:

| Pieza | Plataforma | Costo | Dominio (prueba) |
|---|---|---|---|
| Web (Next.js) | **Vercel** | $0 | `https://fronteragrande.vercel.app` |
| API (FastAPI) | **Render** | $0* | `https://fronteragrande-api.onrender.com` |
| BD (PostgreSQL) | **Neon** | $0 (0.5 GB) | — |

*En Render free tier el servicio se duerme a los 15 min de inactividad; se
despierta solo (~50 s la primera carga). Un ping automático de
[UptimeRobot](https://uptimerobot.com/) (gratis) cada 14 min lo mantiene
activo.

Archivos de despliegue que ya están en el repo:

- `render.yaml` — blueprint con el servicio web de la API (Render lo lee al
  hacer "New → Blueprint").
- `vercel.json` — fija el framework (`nextjs`); el root dir `web/` se configura
  en el dashboard de Vercel (Project → Settings → Root Directory).
- `requirements-prod.txt` — dependencias mínimas de la API (sin las librerías
  de scripts locales).

## 1. Subir el repo a GitHub

El repo local ya está inicializado en la raíz (`git init` hecho, sin commit).
En github.com crea un repositorio **privado** (o público) llamado
`fronteragrande`, por ejemplo, y luego:

```bash
git add -A
git commit -m "Prepara despliegue: PaaS (Vercel + Render + Neon), CORS configurable, driver psycopg"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/fronteragrande.git
git push -u origin main
```

## 2. Neon (base de datos PostgreSQL)

1. Entra a [neon.com](https://neon.com) (antes neon.tech) → "Create a project" (gratis).
2. Elige región cercana (p. ej. `us-east`).
3. Copia la **connection string** de la rama principal (usa `postgresql://…`
   con password). Guárdala: es `DATABASE_URL`.

## 3. Render (API FastAPI)

1. Entra a [render.com](https://render.com) → **New → Blueprint**.
2. Conecta el repo de GitHub que acabas de subir.
3. Render detecta `render.yaml` y crea el servicio `fronteragrande-api`.
4. En el servicio, entra a **Environment** y define:
   - `DATABASE_URL` = la connection string de Neon.
   - `CORS_ORIGINS` = `https://fronteragrande.vercel.app` (el dominio que te
     asigne Vercel; **sin** `https://` duplicado, separado por comas si hay
     varios).
   - `META_REDIRECT_URI` y `WEB_URL` solo cuando quieras el login de Meta
     (ver paso 6). Si no, dejar vacío es válido.
5. Espera el deploy y anota la URL del servicio: `https://fronteragrande-api.onrender.com`.
6. Verifica: `curl https://fronteragrande-api.onrender.com/api/health` →
   `{"estado":"ok"}`.

> Si el build usa el entorno de la API, Render instala `requirements-prod.txt`
> (rápido). El `startCommand` corre `uvicorn backend.main:app`.
>
> **Estado actual:** el servicio está arriba con `CORS_ORIGINS` **vacío**
> (las páginas se renderizan en el servidor y no lo necesitan). Conviene
> definirlo a `https://fronteragrande.vercel.app` para que los fetch del
> navegador (formulario de alta, conexión Meta) funcionen.

## 4. Cargar los datos semilla en Neon

Desde tu máquina (el venv ya tiene `psycopg` en `requirements.txt`):

```bash
.venv/bin/pip install -r requirements.txt   # la primera vez, incluye psycopg
DATABASE_URL="POSTGRESQL_URL_DE_NEON" .venv/bin/python scripts/seed_db.py
```

Esto crea las tablas y carga los 29 artistas + 11 eventos. Después, **poblarlo
de contenido** (fotos de perfil y videos de YouTube) con los scripts de
scraping apuntando a Neon:

```bash
# Fotos de perfil desde las redes (URLs, sin descargar)
DATABASE_URL="…" .venv/bin/python scripts/actualizar_imagenes.py

# Últimos videos de YouTube (RSS, sin API key) → alimenta el feed
DATABASE_URL="…" .venv/bin/python scripts/actualizar_feed_youtube.py
```

> Re-ejecutar estos scripts refresca fotos/feed (las URLs de redes pueden
> caducar). `DATABASE_URL` se puede poner en `.env` y así no repetir el prefijo.

Verifica:
```bash
DATABASE_URL="POSTGRESQL_URL_DE_NEON" .venv/bin/python \
  -c "from lib.repository import ArtistRepository; from db.database import SessionLocal; s=SessionLocal(); print(len(ArtistRepository(s).todos()))"
```

## 5. Vercel (web Next.js)

1. Entra a [vercel.com](https://vercel.com) → **Add New → Project**.
2. Importa el repo de GitHub. Configura el **Root Directory** en `web/`
   (Project → Settings) antes del primer deploy.
3. En **Environment Variables** define:
   - `NEXT_PUBLIC_API_URL` = `https://fronteragrande-api.onrender.com`
   - `NEXT_PUBLIC_SITE_URL` = tu dominio de Vercel (o `https://fronteragrande.mx`
     cuando exista). El sitemap/robots/metadatos lo usan.
4. **Deploy**. Al terminar, la web queda en `https://fronteragrande.vercel.app`.

## 6. (Opcional) Conectar Meta (login y verificación de artistas)

El OAuth de Meta exige **HTTPS** y una URL de callback fija. En producción:

- `META_APP_ID` y `META_APP_SECRET` (las credenciales de la app de Meta) +
  `META_REDIRECT_URI` = `https://fronteragrande-api.onrender.com/api/feed/igfb/callback`
  (Registrar esa URI en la app de Meta: developers.facebook.com → Valid OAuth
  Redirect URIs).
- `WEB_URL` = `https://fronteragrande.vercel.app` (adónde regresa el flujo).
- Para artistas reales habría que solicitar la **revisión de la app**
  (Business Verification); en modo desarrollo solo funciona con el admin.

> Si `META_APP_ID`/`META_APP_SECRET` están **vacías**, la API responde
> `igfb.configurado: false` y el botón "Conectar con Meta" no aparece en el
> perfil del artista (exactamente el estado actual de producción).

Para la prueba con unos pocos artistas, puedes saltarte este paso.

## 7. Mantener viva la API (opcional pero recomendado)

1. Crea una cuenta gratis en [UptimeRobot](https://uptimerobot.com/).
2. Nuevo monitor HTTP(S) → URL de la API (`/api/health`) → intervalo **14 minutos**.
3. Listo: mientras UptimeRobot pinguee, Render no se duerme.

> **Pendiente:** con la misma cuenta de UptimeRobot se crea el monitor para
> `https://fronteragrande-api.onrender.com/api/health`.

## 8. Dominio `fronteragrande.mx` (después)

Cuando se registre, en Vercel **Settings → Domains** se apunta
`fronteragrande.mx`, se actualiza `NEXT_PUBLIC_SITE_URL` y el
`CORS_ORIGINS` de Render pasa a `https://fronteragrande.mx`.

---

## Verificación tras desplegar

```bash
curl -s https://fronteragrande-api.onrender.com/api/health        # {"estado":"ok"}
curl -s https://fronteragrande-api.onrender.com/api/artists        # lista JSON
curl -s https://fronteragrande-api.onrender.com/api/feed           # feed
curl -s https://fronteragrande.vercel.app                          # HTML de la portada
```