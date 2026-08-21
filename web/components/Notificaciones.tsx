"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { desuscribirPush, suscribirPush } from "@/lib/api";
import {
  VAPID_PUBLIC_KEY,
  mensajeErrorPush,
  pushSoportado,
  suscribirNavegador,
} from "@/lib/push";

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
    /* eslint-disable react-hooks/set-state-in-effect */
    if (typeof window === "undefined") return;

    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      Boolean((navigator as Navigator & { standalone?: boolean }).standalone);
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    const puede = pushSoportado();

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
    /* eslint-enable react-hooks/set-state-in-effect */
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
      const subscription = await suscribirNavegador();
      await suscribirPush(subscription);
      setSuscrita(true);
    } catch (e) {
      setError(mensajeErrorPush(e));
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
      setError(mensajeErrorPush(e));
    } finally {
      setCargando(false);
    }
  }

  if (iosSinInstalar) {
    return (
      <p className="mt-2 max-w-sm text-center">
        En iPhone, añade la app a tu pantalla de inicio para activar notificaciones.{" "}
        <Link href="/notificaciones" className="text-accent underline underline-offset-2">
          Ver pasos
        </Link>
      </p>
    );
  }

  if (!soportada) {
    if (!VAPID_PUBLIC_KEY) return null;
    return (
      <p className="mt-2 max-w-sm text-center text-sm text-muted">
        Tu navegador no soporta notificaciones push.
      </p>
    );
  }

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
