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
service error", revisar:

1. Que `NEXT_PUBLIC_VAPID_PUBLIC_KEY` en Vercel sea **exactamente igual** a
   `VAPID_PUBLIC_KEY` en Render (mismos caracteres, sin comillas ni espacios).
2. Que ambas variables correspondan al mismo par generado por
   `scripts/generar_vapid.py` (la pública y la privada deben emparejar).
3. Que la URL de la PWA sea HTTPS (los navegadores rechazan push en HTTP).

El endpoint `GET /api/push/vapid-config` indica si la API tiene la clave pública
configurada y si es válida criptográficamente. No expone la clave privada.

## Mejoras técnicas del registro

- El service worker se registra con `scope: "/"` y `updateViaCache: "none"` para
  evitar que el navegador use una versión obsoleta al suscribirse.
- `/sw.js` se sirve con `Content-Type: application/javascript; charset=utf-8` y
  `Cache-Control: public, max-age=0, must-revalidate`.
- Antes de suscribirse se desuscribe cualquier registro previo para evitar que
  una clave VAPID anterior bloquee el registro nuevo.
