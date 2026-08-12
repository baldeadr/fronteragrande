# Conectar Facebook/Instagram a la escena local (Meta Graph API)

Guía paso a paso para activar la **sincronización automática** de posts de
Facebook e Instagram de los artistas que **administran su página**. El
resultado es un feed que **solo enlaza** (la app es un puente: muestra el
post y el botón "Abrir en {red}" lleva al origen).

> Si este paso no se hace, la app sigue funcionando con los registros de
> investigación (sin contenido sincronizado de FB/IG). La sincronización es
> la forma de que el **propio artista** mantenga su perfil y su contenido.

---

## 1. Requisitos

- Una cuenta de **Facebook** que administre la página del artista (FB e IG
  de negocio vinculadas).
- Acceso a [developers.facebook.com](https://developers.facebook.com).
- `META_APP_ID`, `META_APP_SECRET` y `META_REDIRECT_URI` en el `.env` del
  proyecto (ver `.env.example`).

## 2. Crear la app

1. Entra a [developers.facebook.com](https://developers.facebook.com) →
   **Mis aplicaciones** → **Crear aplicación**.
2. Tipo de app: **Negocio**.
3. Rellena nombre y correo de contacto → **Crear**.

## 3. Añadir los productos

En **Agregar productos** (panel izquierdo de la app):

- **Facebook Login for Business** (o "Acceso de Facebook").
- **Instagram** → "Instagram API with Instagram Login" (Instagram para
  empresas). Si pide "convertir a Instagram de negocio", vincúlalo a la
  página FB del artista.

## 4. Configurar OAuth (URL de redirección)

En **Facebook Login for Business** → **Configuración** (o "Use cases"):

1. Define el "Tipo de app": si la app será **pública** (producción), elige
   **Público**. En desarrollo, **El modo de desarrollo** basta.
2. En **Valid OAuth Redirect URIs** (URL válidas de redirección de OAuth)
   añade exactamente el valor de `META_REDIRECT_URI` del `.env`:
   - **Desarrollo (HTTPS obligatorio):** Meta ya **no acepta `http://`**.
     Usa un túnel HTTPS que apunte al callback local:
     - `cloudflared tunnel --url http://127.0.0.1:8000` → devuelve
       `https://xxxx.trycloudflare.com`; el callback queda
       `https://xxxx.trycloudflare.com/api/feed/igfb/callback`
       (instalar: binario en
       `https://github.com/cloudflare/cloudflared/releases`).
     - La URL del túnel es **temporal**: al cambiar, actualizar también
       `META_REDIRECT_URI` del `.env` y reiniciar la API.
   - Producción: `https://tudominio.com/api/feed/igfb/callback`
3. Guarda.

> El callback redirige a la web usando `WEB_URL` del `.env`
> (por defecto `http://127.0.0.1:3000`). Si abres la web desde otro host
> (p. ej. el teléfono por LAN), ajusta `WEB_URL` para que el regreso caiga en
> la misma web que estás usando.

## 5. Permisos

La app solicita estos permisos (ya configurados en
`backend/feed_meta.py`, `SCOPES`):

| Permiso | Para qué |
|---------|----------|
| `pages_show_list` | listar las páginas que administra el usuario |
| `pages_read_engagement` | leer los posts de la página |
| `instagram_basic` | leer media y metadatos de la cuenta IG de negocio |

- **Modo desarrollo:** como **admin de la app**, puedes autorizar sin pasar
  revisión.
- **Producción:** para usarla con cualquier usuario necesitas solicitar la
  **revisión de la app** (Business Verification) para estos permisos.

## 6. Configurar `.env`

```env
META_APP_ID=1234567890123456
META_APP_SECRET=abcdef1234567890abcdef1234567890
META_REDIRECT_URI=https://xxxx.trycloudflare.com/api/feed/igfb/callback
WEB_URL=http://127.0.0.1:3000
```

Reinicia la API después de cambiar el `.env`:
`./scripts/dev.sh` (o reinicia `uvicorn`).

## 7. Conectar el artista (reclamar y verificar el perfil)

1. Abre el perfil del artista en la web → sección **"¿Eres {artista}? Reclama
   tu perfil"** → **Conectar y verificar**.
2. Facebook abre el diálogo de autorización → acepta con la cuenta que
   **administra la página del artista**.
3. La app valida que la cuenta autorizada administre la **página registrada**
   del artista (compara con su URL de Facebook). Si administra otra página,
   la conexión falla y no vincula nada.
4. Al conectar, se guarda el token de la página (larga duración) y el id de
   la cuenta IG; `estado_registro` pasa a `confirmado (artista, fecha)` y el
   perfil muestra el badge público **"Verificado"**.

> En el flujo de autorización, Meta exige que el **usuario** que autoriza sea
> admin de la página que se va a conectar. Solo la página **registrada** del
> artista se vincula (no la primera administrada). Un perfil que no se
> conecta queda como registro de investigación, sin contenido sincronizado.

## 8. Sincronización automática

- **A mano:** `.venv/bin/python scripts/sync_feed_igfb.py` — trae los últimos
  10 posts de FB y media de IG de cada artista conectado, los registra en el
  feed sin duplicar (por URL) y recalcula `estado_activo`.
- **Cron** (script listo, `scripts/sync_igfb.sh`), p. ej. cada 6 horas:

  ```bash
  crontab -e
  ```
  ```
  0 */6 * * * /ruta/al/proyecto/scripts/sync_igfb.sh >> /tmp/sync_igfb.log 2>&1
  ```

## 9. Notas y solución de problemas

- **Tokens de página de larga duración:** no expiran mientras el usuario no
  revoque la app. Si un artista ve la cuenta desconectada, vuelve a conectar.
- **`{"detail":"Meta no configurado..."}` (503):** faltan `META_APP_ID` o
  `META_APP_SECRET` en `.env`, o la API no se reinició.
- **Callback devuelve "error":** revisa que la URI de redirección coincida
  exactamente, que el usuario sea admin de la página, y los logs de la API
  (`/tmp/api.log`).
- **"El usuario no administra ninguna página":** la cuenta autorizada no es
  admin de ninguna página FB.
- **Seguridad:** los tokens se guardan solo en la BD y **nunca** se exponen
  por la API (`/api/artists/{slug}` solo reporta el estado de conexión).
