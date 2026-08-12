# Despliegue en línea (free tier) — Frontera Grande

Guía para llevar el sitio a internet **gratis o casi gratis**, con el dominio
final (`fronteragrande.mx`) pendiente. Para la prueba con artistas se usa el
dominio gratuito de cada plataforma y el dominio se apunta después.

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
- `vercel.json` — indica a Vercel que la app Next.js está en `web/`.
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

1. Entra a [neon.tech](https://neon.tech) → "Create a project" (gratis).
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

## 4. Cargar los datos semilla en Neon

Desde tu máquina (el venv ya tiene `psycopg` en `requirements.txt`):

```bash
.venv/bin/pip install -r requirements.txt   # la primera vez, incluye psycopg
DATABASE_URL="POSTGRESQL_URL_DE_NEON" .venv/bin/python scripts/seed_db.py
```

Esto crea las tablas y carga los 28 artistas + 11 eventos. Verifica:

```bash
DATABASE_URL="POSTGRESQL_URL_DE_NEON" .venv/bin/python \
  -c "from lib.repository import ArtistRepository; from db.database import SessionLocal; s=SessionLocal(); print(len(ArtistRepository(s).todos()))"
```

## 5. Vercel (web Next.js)

1. Entra a [vercel.com](https://vercel.com) → **Add New → Project**.
2. Importa el repo de GitHub. Vercel ya sabe (por `vercel.json`) que la app
   está en `web/`.
3. En **Environment Variables** define:
   - `NEXT_PUBLIC_API_URL` = `https://fronteragrande-api.onrender.com`
   - `NEXT_PUBLIC_SITE_URL` = tu dominio de Vercel (o `https://fronteragrande.mx`
     cuando exista). El sitemap/robots/metadatos lo usan.
4. **Deploy**. Al terminar, la web queda en `https://fronteragrande.vercel.app`.

## 6. (Opcional) Conectar Meta (login y verificación de artistas)

El OAuth de Meta exige **HTTPS** y una URL de callback fija. En producción:

- `META_REDIRECT_URI` = `https://fronteragrande-api.onrender.com/api/feed/igfb/callback`
  (Registrar esa URI en la app de Meta: developers.facebook.com → Valid OAuth
  Redirect URIs).
- `WEB_URL` = `https://fronteragrande.vercel.app` (adónde regresa el flujo).
- Para artistas reales habría que solicitar la **revisión de la app**
  (Business Verification); en modo desarrollo solo funciona con el admin.

Para la prueba con unos pocos artistas, puedes saltarte este paso.

## 7. Mantener viva la API (opcional pero recomendado)

1. Crea una cuenta gratis en [UptimeRobot](https://uptimerobot.com/).
2. Nuevo monitor HTTP(S) → URL de la API → intervalo **14 minutos**.
3. Listo: mientras UptimeRobot pinguee, Render no se duerme.

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