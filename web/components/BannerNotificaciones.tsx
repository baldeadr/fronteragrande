"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { suscribirPush } from "@/lib/api";
import {
  VAPID_PUBLIC_KEY,
  mensajeErrorPush,
  pushSoportado,
  suscribirNavegador,
} from "@/lib/push";

const LS_KEY = "fg_push_banner";
const DIAS_RECORDARIO = 7;

function puedeMostrar(): boolean {
  if (!VAPID_PUBLIC_KEY) return false;
  const visto = localStorage.getItem(LS_KEY);
  if (!visto) return true;
  const hace = Date.now() - Number(visto);
  return hace > DIAS_RECORDARIO * 24 * 60 * 60 * 1000;
}

export default function BannerNotificaciones() {
  const [visible, setVisible] = useState(false);
  const [ios, setIos] = useState(false);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect */
    if (typeof window === "undefined" || !pushSoportado()) {
      setCargando(false);
      return;
    }

    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      Boolean((navigator as Navigator & { standalone?: boolean }).standalone);
    const esIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
    setIos(esIos);

    if (esIos && !standalone) {
      setCargando(false);
      return;
    }

    navigator.serviceWorker.ready
      .then((reg) => reg.pushManager.getSubscription())
      .then((sub) => {
        if (sub) return;
        const permiso = Notification.permission;
        if (permiso === "denied" || permiso === "granted") return;
        if (puedeMostrar()) setTimeout(() => setVisible(true), 3000);
      })
      .catch(() => {})
      .finally(() => setCargando(false));
    /* eslint-enable react-hooks/set-state-in-effect */
  }, []);

  function recordarDespues() {
    localStorage.setItem(LS_KEY, String(Date.now()));
    setVisible(false);
  }

  async function activar() {
    setError("");
    setCargando(true);
    try {
      const nuevoPermiso = await Notification.requestPermission();
      if (nuevoPermiso !== "granted") {
        setError("Permiso no concedido.");
        setCargando(false);
        return;
      }
      const subscription = await suscribirNavegador();
      await suscribirPush(subscription);
      localStorage.setItem(LS_KEY, String(Date.now()));
      setVisible(false);
    } catch (e) {
      setError(mensajeErrorPush(e));
    } finally {
      setCargando(false);
    }
  }

  if (cargando || !visible) return null;

  return (
    <div className="fixed inset-x-0 bottom-24 z-50 flex justify-center px-4 md:bottom-8">
      <div className="flex max-w-lg flex-col items-center gap-3 rounded-2xl border border-line bg-surface p-4 shadow-lg shadow-black/40">
        <p className="text-center text-sm">
          {ios
            ? "Recibe avisos cuando haya artistas nuevos o contenido reciente."
            : "¿Quieres enterarte de artistas nuevos y contenido reciente?"}
        </p>
        {error && <p className="text-xs text-red-400">{error}</p>}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={activar}
            disabled={cargando}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-bg transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            Permitir
          </button>
          <button
            type="button"
            onClick={recordarDespues}
            className="rounded-lg border border-line px-4 py-2 text-sm text-muted transition-colors hover:border-accent hover:text-text"
          >
            Ahora no
          </button>
          <Link
            href="/notificaciones"
            className="text-xs text-accent underline underline-offset-2"
          >
            Saber más
          </Link>
        </div>
      </div>
    </div>
  );
}
