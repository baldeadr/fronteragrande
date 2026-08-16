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
puede enviar avisos generales desde `/admin`; las altas de artistas y los
posts nuevos de Meta generan avisos automáticos.
