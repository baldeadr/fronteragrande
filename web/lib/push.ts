"use client";

/**
 * Utilidades compartidas para Web Push en la PWA.
 *
 * Incluye la decodificación de la clave pública VAPID y helpers para
 * interpretar los errores del navegador de forma útil para el usuario.
 */

export const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY ?? "";

/** Indica si el navegador puede suscribirse a notificaciones push. */
export function pushSoportado(): boolean {
  return (
    typeof window !== "undefined" &&
    Boolean(VAPID_PUBLIC_KEY) &&
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  );
}

/**
 * Convierte una clave VAPID pública en base64url (RFC 8292) a Uint8Array,
 * formato que esperan `PushManager.subscribe()` y `webpush`.
 */
export function urlBase64ToUint8Array(base64String: string): BufferSource {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i += 1) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/** Valida que la clave pública tenga el formato base64url y longitud razonable. */
export function vapidPublicKeyValida(): boolean {
  if (!VAPID_PUBLIC_KEY) return false;
  const limpia = VAPID_PUBLIC_KEY.trim();
  if (!/^[A-Za-z0-9_-]+$/.test(limpia)) return false;
  // Una clave P-256 sin comprimir ocupa 65 bytes → ~87 caracteres base64url.
  // Permitimos un rango amplio por si hay padding o formatos comprimidos.
  return limpia.length >= 80 && limpia.length <= 100;
}

function detalleError(error: unknown): string {
  if (error instanceof Error) {
    return `${error.name}: ${error.message}`;
  }
  return String(error);
}

/**
 * Traduce los errores comunes de `pushManager.subscribe()` a mensajes útiles.
 * Conserva el detalle técnico para facilitar el diagnóstico remoto.
 */
export function mensajeErrorPush(error: unknown): string {
  const detalle = detalleError(error);
  console.error("[Push] error completo:", error);

  if (error instanceof DOMException) {
    const nombre = error.name;
    const mensaje = error.message.toLowerCase();

    if (nombre === "NotAllowedError") {
      return "Permiso de notificaciones bloqueado en el navegador.";
    }
    if (nombre === "AbortError") {
      return `La solicitud fue cancelada (${detalle}). Intenta de nuevo.`;
    }
    if (nombre === "InvalidStateError") {
      return "El service worker aún no está listo. Recarga la página e intenta de nuevo.";
    }
    if (nombre === "SecurityError") {
      return "El navegador bloqueó la operación. Usa HTTPS o localhost.";
    }
    if (
      mensaje.includes("push service error") ||
      mensaje.includes("registration failed")
    ) {
      return "El servicio de notificaciones del navegador no pudo completar el registro. Revisa tu conexión y vuelve a intentar.";
    }
    if (mensaje.includes("insecure") || mensaje.includes("https")) {
      return "Las notificaciones requieren una conexión segura (HTTPS).";
    }
  }
  if (error instanceof Error) {
    const mensaje = error.message.toLowerCase();
    if (mensaje.includes("atob") || mensaje.includes("invalid")) {
      return "La clave pública de notificaciones no es válida.";
    }
    return error.message;
  }
  return `No se pudieron activar las notificaciones (${detalle}).`;
}

/** Devuelve el service worker registration listo para usar push. */
export async function obtenerRegistroPush(): Promise<ServiceWorkerRegistration> {
  if (!("serviceWorker" in navigator)) {
    throw new Error("Service Worker no soportado.");
  }
  return navigator.serviceWorker.ready;
}

/** Suscripción push con manejo explícito de estados. */
export async function suscribirNavegador(): Promise<PushSubscription> {
  if (!pushSoportado()) {
    throw new Error("Las notificaciones push no están soportadas en este navegador.");
  }
  if (!vapidPublicKeyValida()) {
    throw new Error("La clave pública de notificaciones no está configurada correctamente.");
  }
  const registration = await obtenerRegistroPush();
  return registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
  });
}
