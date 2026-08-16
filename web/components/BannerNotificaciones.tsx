"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { suscribirPush } from "@/lib/api";

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY ?? "";
const LS_KEY = "fg_push_banner";
const DIAS_RECORDARIO = 7;

function clavePublicaBytes(clave: string): ArrayBuffer {
  const padding = "=".repeat((4 - (clave.length % 4)) % 4);
  const base64 = (clave + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) bytes[i] = raw.charCodeAt(i);
  return bytes.buffer as ArrayBuffer;
}

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
    if (!VAPID_PUBLIC_KEY || !("serviceWorker" in navigator)) return;

    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      Boolean((navigator as Navigator & { standalone?: boolean }).standalone);
    const esIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIos(esIos);

    if (esIos && !standalone) return;

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
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: clavePublicaBytes(VAPID_PUBLIC_KEY),
      });
      await suscribirPush(subscription);
      localStorage.setItem(LS_KEY, String(Date.now()));
      setVisible(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo activar.");
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
