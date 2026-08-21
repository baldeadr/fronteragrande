"""Envío de notificaciones Web Push (PWA) con VAPID.

Sin credenciales VAPID en el entorno, el envío se omite en silencio: el resto
de la aplicación funciona igual (suscripciones, alta de artistas, admin).
Las suscripciones viven en `push_subscriptions` y se administran vía
`backend/push.py`. Generar el par de llaves con `scripts/generar_vapid.py`.
"""

import logging
import json
import os

from pywebpush import WebPushException, webpush

from lib.repository import PushSubscriptionRepository

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:hola@fronteragrande.mx")

NOTIFICACION_PREDETERMINADA = {
    "title": "Frontera Grande",
    "body": "",
    "url": "/",
    "icon": "/icons/icon-192.png",
    "badge": "/icons/icon-192.png",
}


class SubscriptionGoneError(Exception):
    """La suscripción ya no existe en el servicio push (410/404)."""

    def __init__(self, endpoint: str):
        super().__init__(f"Suscripción ya no válida: {endpoint}")
        self.endpoint = endpoint


def configurado() -> bool:
    return bool(VAPID_PRIVATE_KEY and VAPID_SUBJECT)


def _payload(titulo: str, cuerpo: str = "", url: str = "/") -> dict:
    return {
        **NOTIFICACION_PREDETERMINADA,
        "title": titulo,
        "body": cuerpo,
        "url": url,
    }


def enviar(subscription, titulo: str, cuerpo: str = "", url: str = "/") -> bool:
    """Envía una notificación a una suscripción. True si se entregó.

    Levanta `SubscriptionGoneError` si el servicio responde 410/404 para que
    el caller pueda purgar la suscripción.
    """
    if not configurado():
        return False
    info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.keys_p256dh,
            "auth": subscription.keys_auth,
        },
    }
    try:
        webpush(
            subscription_info=info,
            data=json.dumps(_payload(titulo, cuerpo, url)),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_SUBJECT},
            ttl=86400,
            timeout=10,
        )
        return True
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        logger.warning("Push falló (%s) para %s", status, subscription.endpoint)
        if status in (410, 404):
            raise SubscriptionGoneError(subscription.endpoint)
        return False
    except Exception as exc:  # noqa: BLE001 — el aviso nunca debe romper el flujo
        logger.warning("Push falló inesperado para %s: %s", subscription.endpoint, exc)
        return False


def notificar_todos(
    repo: PushSubscriptionRepository,
    titulo: str,
    cuerpo: str = "",
    url: str = "/",
) -> int:
    """Envía a todos los suscriptores y purga los dados de baja.

    Devuelve cuántas notificaciones se entregaron. No hace commit: el caller
    (router o script) decide cuándo persistir.
    """
    if not configurado():
        return 0
    enviadas = 0
    for sub in repo.todos():
        try:
            if enviar(sub, titulo, cuerpo, url):
                enviadas += 1
        except SubscriptionGoneError:
            repo.eliminar(sub.endpoint)
    return enviadas


def notificar_verificacion_artista(session, nombre_artista: str) -> None:
    """Envía notificación push cuando un artista verifica su proyecto.

    Respeta el toggle `notificar_auto_verificacion` de SettingsRepository.
    No rompe el flujo si falla el envío.
    """
    try:
        from lib.repository import PushSubscriptionRepository, SettingsRepository

        if not SettingsRepository(session).obtener_bool("notificar_auto_verificacion"):
            return
        enviadas = notificar_todos(
            PushSubscriptionRepository(session),
            f"{nombre_artista} se verificó",
            "Un nuevo artista se conectó en Frontera Grande.",
            "/",
        )
        session.commit()
        if enviadas:
            logger.info("Aviso de verificación enviado a %s suscriptores", enviadas)
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo notificar verificación: %s", exc)
