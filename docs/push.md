# Web Push

La PWA puede enviar avisos a dispositivos que acepten las notificaciones.
En iPhone se requiere iOS 16.4 o posterior y añadir primero la PWA a la
pantalla de inicio.

## Configuración

1. Generar las llaves con `.venv/bin/python scripts/generar_vapid.py`.
2. Configurar `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` y `VAPID_SUBJECT` en
   Render, y copiar la clave pública como `NEXT_PUBLIC_VAPID_PUBLIC_KEY` en
   Vercel.
3. Configurar las mismas variables VAPID en GitHub Actions si el workflow de
   sincronización de Meta debe notificar nuevos posts.

La web registra suscripciones en `POST /api/push/subscribe`. El panel admin
puede enviar avisos generales desde `/admin`; los posts nuevos de Meta generan
avisos automáticos; las altas de artistas **solo** generan avisos automáticos
cuando el proyecto se verifica mediante OAuth (Meta o TikTok).

## Diagnóstico

Si al activar notificaciones el navegador muestra "Registration failed - push
service error", "Load failed" o un error de CORS, revisar:

1. Que `NEXT_PUBLIC_VAPID_PUBLIC_KEY` en Vercel sea **exactamente igual** a
   `VAPID_PUBLIC_KEY` en Render (mismos caracteres, sin comillas ni espacios).
2. Que ambas variables correspondan al mismo par generado por
   `scripts/generar_vapid.py` (la pública y la privada deben emparejar).
3. Que la URL de la PWA sea HTTPS (los navegadores rechazan push en HTTP).
4. Que `CORS_ORIGINS` en Render incluya el dominio desde el que se sirve la
   web. Si se cambia de dominio (p. ej. de `*.vercel.app` a `fronteragrande.mx`),
   hay que agregar el nuevo dominio; de lo contrario el navegador bloquea el
   `POST /api/push/subscribe`. Verificar con:
   ```bash
   curl -I -H "Origin: https://fronteragrande.mx" \
     https://fronteragrande-api.onrender.com/api/push/vapid-config
   ```
   Debe devolver `access-control-allow-origin: https://fronteragrande.mx`.

El endpoint `GET /api/push/vapid-config` indica si la API tiene la clave pública
configurada y si es válida criptográficamente. No expone la clave privada.

## Mejoras técnicas del registro

- `/sw.js` se sirve con `Content-Type: application/javascript; charset=utf-8` y
  `Cache-Control: public, max-age=0, must-revalidate`.
- El service worker se registra en `layout.tsx` de forma simple y confiable.
- La decodificación de la clave VAPID y el manejo de errores vive en
  `web/lib/push.ts`, compartido por los componentes de notificaciones.
