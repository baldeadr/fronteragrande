"use client";

import { useEffect, useState } from "react";
import { desuscribirPush, suscribirPush } from "@/lib/api";

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY ?? "";

function clavePublicaBytes(clave: string): ArrayBuffer {
  const padding = "=".repeat((4 - (clave.length % 4)) % 4);
  const base64 = (clave + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) bytes[i] = raw.charCodeAt(i);
  return bytes.buffer as ArrayBuffer;
}

export default function Notificaciones() {
  const [cargando, setCargando] = useState(true);
  const [suscrita, setSuscrita] = useState(false);
  const [instalada, setInstalada] = useState(false);
  const [iosSinInstalar, setIosSinInstalar] = useState(false);
  const [soportada, setSoportada] = useState(false);
  const [permiso, setPermiso] = useState<NotificationPermission | "desconocido">(
    "desconocido",
  );
  const [error, setError] = useState("");

  useEffect(() => {
    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      Boolean((navigator as Navigator & { standalone?: boolean }).standalone);
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    const puede =
      Boolean(VAPID_PUBLIC_KEY) &&
      "serviceWorker" in navigator &&
      "PushManager" in window &&
      "Notification" in window;

    // Estas señales solo existen en el navegador y sincronizan el estado con
    // la capacidad real de la PWA después de hidratar.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setInstalada(standalone);
    setIosSinInstalar(ios && !standalone);
    setSoportada(puede);
    if (puede) setPermiso(Notification.permission);

    if (!puede) {
      setCargando(false);
      return;
    }

    navigator.serviceWorker.ready
      .then((registration) => registration.pushManager.getSubscription())
      .then((subscription) => setSuscrita(Boolean(subscription)))
      .catch(() => setError("No se pudo consultar el estado de notificaciones."))
      .finally(() => setCargando(false));
  }, []);

  async function activar() {
    setError("");
    setCargando(true);
    try {
      const nuevoPermiso = await Notification.requestPermission();
      setPermiso(nuevoPermiso);
      if (nuevoPermiso !== "granted") {
        setError("El permiso de notificaciones no fue concedido.");
        return;
      }
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: clavePublicaBytes(VAPID_PUBLIC_KEY),
      });
      await suscribirPush(subscription);
      setSuscrita(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron activar las notificaciones.");
    } finally {
      setCargando(false);
    }
  }

  async function desactivar() {
    setError("");
    setCargando(true);
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        const endpoint = subscription.endpoint;
        await subscription.unsubscribe();
        await desuscribirPush(endpoint);
      }
      setSuscrita(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron desactivar las notificaciones.");
    } finally {
      setCargando(false);
    }
  }

  if (iosSinInstalar) {
    return (
      <p className="mt-2 max-w-sm text-center">
        En iPhone, añade la app a tu pantalla de inicio para activar notificaciones.
      </p>
    );
  }

  if (!soportada) return null;

  return (
    <div className="mt-3 flex flex-col items-center gap-1">
      <div className="flex items-center gap-2">
        <span>Notificaciones</span>
        <button
          type="button"
          onClick={suscrita ? desactivar : activar}
          disabled={cargando || permiso === "denied"}
          className="rounded border border-line px-2 py-1 text-[11px] text-accent hover:border-accent disabled:cursor-not-allowed disabled:opacity-50"
        >
          {cargando ? "…" : suscrita ? "Desactivar" : "Activar"}
        </button>
      </div>
      {permiso === "denied" && <span>Permiso bloqueado en el navegador.</span>}
      {error && <span className="text-red-400">{error}</span>}
      {!instalada && !suscrita && (
        <span>En iPhone, primero usa “Añadir a pantalla de inicio”.</span>
      )}
    </div>
  );
}
