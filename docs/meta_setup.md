# Conectar Facebook/Instagram a la escena local (Meta Graph API)

Guía paso a paso para activar la **sincronización automática** de posts de
Facebook e Instagram de los artistas que **administran su página**. El
resultado es un feed que **solo enlaza** (la app es un puente: muestra el
post y el botón "Abrir en {red}" lleva al origen).

> Si este paso no se hace, la app sigue funcionando con los registros de
> investigación (sin contenido sincronizado de FB/IG). La sincronización es
> la forma de que el **propio artista** mantenga su perfil y su contenido.

> **Estado actual (agosto 2026):** la app de Meta está configurada en
> producción, el OAuth ya fue probado, **Apex Ultra quedó verificado** y sus
> publicaciones de Facebook ya aparecen en el perfil. GitHub Actions ejecuta
> la sincronización cada 6 horas. Falta conectar al resto de artistas.
> **2026-08-29:** la app entró en **validación/registro** de Meta
> (Business Verification); mientras Meta procesa ese estado, el **Facebook
> Login queda temporalmente deshabilitado** para toda la app (ver § 10).

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

| Permiso | Para qué | Estado |
|---------|----------|--------|
| `pages_show_list` | listar las páginas que administra el usuario | verificado |
| `pages_read_engagement` | leer los posts de la página | verificado |
| `instagram_basic` | leer media y metadatos de la cuenta IG de negocio | verificado |
| `pages_events` | leer eventos de la página (ingesta opcional) | **opcional — solo tras aprobación**: pedirlo sin aprobación bloquea a usuarios no-admin con `Invalid Scope: pages_events`. Por eso el login normal no lo pide; se usa `con_eventos=1` (`SCOPES_EVENTOS` en `backend/feed_meta.py`) solo tras App Review. |

- **Modo desarrollo:** como **admin de la app**, puedes autorizar sin pasar
  revisión (por eso Apex Ultra sí conectó con `pages_events`).
- **Producción:** para usarla con cualquier usuario necesitas solicitar la
  **revisión de la app** (Business Verification) para estos permisos.
  Hasta entonces, **no pedir `pages_events` en el login por defecto**.

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
- **`Invalid Scope: pages_events`:** la app pidió `pages_events` sin tener
  aprobación de Meta. **No es un error de mayúsculas**: es que el permiso
  aún no está aprobado para usuarios externos. Solución: el login normal
  (`/api/feed/igfb/login?slug=X`) ya no lo pide; si necesitas eventos,
  usa `?con_eventos=1` solo tras App Review, o deja los eventos por CRUD
  del admin (`POST /api/admin/events`).
- **Seguridad:** los tokens se guardan solo en la BD y **nunca** se exponen
  por la API (`/api/artists/{slug}` solo reporta el estado de conexión).

## 10. Validación de la app y error "Feature Unavailable"

Cuando la app de Meta entra en **validación/registro** (Business
Verification / App Review en curso), Meta **desactiva temporalmente el
Facebook Login** para toda la app mientras "actualiza las configuraciones
adicionales de la app". En ese lapso, cualquier intento de conexión muestra:

> **Feature Unavailable**
> Facebook Login is currently unavailable for this app, since we are
> updating additional details for this app. Please try again later.

**Qué significa:**

- Es un **bloqueo temporal impuesto por Meta**, no un problema del proyecto,
  de la cuenta, ni del código.
- Afecta a **todos** los usuarios mientras la app está en ese estado
  intermedio (aunque el usuario tenga rol de admin/test).
- **Plazos orientativos** (tiempo no oficial garantizado de Meta):
  - Revisión de permisos (App Review): **3–7 días** (a veces hasta 2 semanas).
  - Verificación de negocio (Business Verification): la más larga,
    **1–3 semanas o más**, según la documentación enviada (puede pedir
    comprobantes). El estado "updating additional details" suele resolverse
    en **unos pocos días**.

**Qué hacer:**

- **Esperar** a que Meta complete el proceso; cuando la app quede aprobada
  y en modo público/activo, el login se desbloquea para todos.
- Si en **+2 semanas** sigue igual, revisar el estado en el dashboard de la
  app (posible documento pendiente de la verificación de negocio).
- **No reintentar en bucle**: no hay acción de código posible; es un proceso
  de Meta.
- Para pruebas locales aprovecha el **modo desarrollo** (solo admins/test de
  la app) una vez desbloqueado.

### Roles de app y cuenta de prueba

Para probar el login en modo desarrollo hace falta que la cuenta secundaria
tenga un rol de app que permita "probar todos los permisos, funciones y
productos". En Meta (en español) estos roles **sirven para pruebas**:

- **Administrador** / **Desarrollador**: además de probar, pueden modificar
  configuración de la app.
- **Evaluador** (en inglés "Tester"): puede probar todos los permisos,
  funciones y productos — el rol mínimo recomendado para una cuenta de
  prueba secundaria.

> El "Evaluador" de la lista de roles **sí** es válido para login en
> desarrollo (es el antiguo "Tester"). No es el rol de "App Review
> reviewer". Si una cuenta con rol **Evaluador** recibe el error
> "Feature Unavailable" y la app está en validación, es **por el bloqueo
> temporal de § 10**, no por el rol.
