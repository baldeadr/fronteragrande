# Sincronización de TikTok — plan y estado

Estado del plan TikTok acordado con el artista (2026-08-16). La **única vía
automática** para obtener seguidores (`followers_tt`, ya alimentan ranking y
stats) y videos recientes (feed, fuente `tt`) es la **TikTok Business API**
(OAuth del creador). No hay API pública sin aprobación, el perfil bloquea
bots (reto JS) y el oEmbed solo sirve para previsualizar un post individual.

## Cómo funciona (implementado)

- `backend/feed_tiktok.py`: OAuth del creador (`/api/feed/tiktok/login` →
  `callback` → `desconectar`) con **PKCE** (`code_challenge` S256; el verifier
  viaja en `state` para no guardar estado) + `user/info/` (nombre, avatar,
  seguidores) + `video/list/` (videos). Guarda solo `tt_user_id` (open_id) y
  `tt_refresh_token` (se rota en cada uso; el access token dura 24 h). Los
  tokens nunca se exponen en la API.
- `scripts/sync_feed_tiktok.py`: por cada artista conectado rota el refresh
  token, actualiza `followers_tt` y registra los videos en `feed_items`
  (fuente `tt`, sin duplicar por URL). Si `video.list` no está aprobado,
  registra solo seguidores.
- **Límite del modo desarrollo/sandbox (2026-08-16):** con solo `user.info.basic`
  TikTok **deniega** `follower_count` (`scope_not_authorized`, igual que el
  límite 2026 de Spotify). Al añadir los scopes `user.info.stats` (seguidores)
  y `video.list` (videos) y reautorizar, **ambos funcionan en sandbox**. Para
  usuarios reales en producción se requiere la **aprobación** de la app.
- Web: botón "Conectar TikTok" en el perfil (paralelo al de Meta); la cuenta
  conectada también **reclama/verifica** el perfil (`estado_registro` →
  `confirmado`).
- `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` en `.env` (ver `.env.example`).
  Sin ellas la conexión queda desactivada (login devuelve 503).

## Fases

| Fase | Estado | Detalle |
|------|--------|---------|
| A. Inventario | ✔ Hecho | Perfiles registrados abajo; columnas `tt_user_id`/`tt_refresh_token` en `artists` (migración ligera en `db/database.py`). |
| B. App + aprobación | `[PENDIENTE]` artista | App creada en TikTok for Developers (modo sandbox). Pendiente: **aprobación manual** del scope `video.list` para producción (video demo + explicación). |
| C. Implementación | ✔ Hecho | `backend/feed_tiktok.py` (PKCE) + `scripts/sync_feed_tiktok.py` + botón "Conectar TikTok" + tests. |
| D. Operación | ✔ Hecho | `.github/workflows/sync-tiktok.yml` cada 6 h (paralelo a `sync-meta.yml`); requiere los secrets `TIKTOK_CLIENT_KEY`/`TIKTOK_CLIENT_SECRET`. |

### Fase B — pasos para el artista

1. Ir a [developer.tiktok.com](https://developer.tiktok.com) → crear cuenta de
   desarrollador → **Create App** (tipo *Business* o *General* según lo que
   ofrezca el dashboard).
2. Añadir el scope **`user.info.basic`** (estándar) y **`video.list`**.
   `video.list` requiere solicitud/verificación; añadirlo a `TIKTOK_SCOPES`
   en producción solo cuando TikTok lo apruebe.
3. Configurar la redirección de OAuth a
   `https://fronteragrande-api.onrender.com/api/feed/tiktok/callback`.
4. Poner `TIKTOK_CLIENT_KEY` y `TIKTOK_CLIENT_SECRET` en el `.env` de Render.

### Respaldo si rechazan `video.list`

Quedamos con seguidores (`user.info.basic`, sin aprobación especial) y los
TikTok cross-posteados a FB/IG/YT que ya llegan por el sync de Meta. El
módulo ya tolera el error de `video.list` (registra el problema y continúa).

## Inventario de perfiles TikTok de la escena (2026-08-16)

| Proyecto | Perfil | ¿Administra? |
|----------|--------|--------------|
| Apex Ultra | https://www.tiktok.com/@apexultramusic | ✔ Sí (sandbox, 2026-08-16) |
| Cada Martes | https://www.tiktok.com/@cadamartesmx | `[PENDIENTE]` |
| Comando Burrito | https://www.tiktok.com/@comandoburrito | `[PENDIENTE]` |
| Eliwix y las Cerezas Podridas | https://www.tiktok.com/@cerezaspodridas | `[PENDIENTE]` |
| Isquemia | https://www.tiktok.com/@isquemiabanda | `[PENDIENTE]` |
| Oxte | https://www.tiktok.com/@oxte.band | `[PENDIENTE]` |
| Vaale | https://www.tiktok.com/@vaalemusic | `[PENDIENTE]` |

La columna "¿Administra?" se completa cuando el artista conecta su cuenta
desde el perfil (proceso de verificación).

## Notas de la puesta en marcha (2026-08-16)

- **PKCE obligatorio:** el login debe enviar `code_challenge`/`code_challenge_method=S256`
  y el callback el `code_verifier` (el verifier va empaquetado en `state`).
- **Redirect URI solo HTTPS** (`http://127.0.0.1` es rechazado): se usó un
  túnel cloudflared (`https://<tunel>.trycloudflare.com/api/feed/tiktok/callback`).
  El túnel pide **verificar la URL prefix** con un archivo de firma servido
  desde la API (`backend/main.py` → `GET /tiktokZRAuUrtos3HEHHPy6apDTOQcgqkpwyZC.txt`).
  El túnel es temporal: para producción se verificará la URL estable de Render.
- **Términos/Privacidad:** TikTok exige ToS URL y Privacy Policy URL reales
  (mínimos `[PENDIENTE]` servidos desde la API: `/terminos` y `/privacidad`).
- **Sandbox:** app sin aprobar funciona solo en modo sandbox con
  **sandbox users** (agregar la cuenta que autoriza); la app pide envío a
  revisión (explicación + video demo) solo para ir a producción.