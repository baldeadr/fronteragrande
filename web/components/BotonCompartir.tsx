"use client";

import { useEffect, useRef, useState } from "react";

function IconoCompartir({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <circle cx="18" cy="5" r="3" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="19" r="3" />
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
      <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
    </svg>
  );
}

function EsCompartible(): boolean {
  return typeof navigator !== "undefined" && typeof navigator.share === "function";
}

export default function BotonCompartir({
  nombre,
  slug,
}: {
  nombre: string;
  slug: string;
}) {
  const [copiado, setCopiado] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );

  const url = `${typeof window !== "undefined" ? window.location.origin : ""}/artistas/${slug}`;
  const texto = `Mira el perfil de ${nombre} en Frontera Grande`;

  async function compartir() {
    if (EsCompartible()) {
      try {
        await navigator.share({ title: `${nombre} — Frontera Grande`, text: texto, url });
        return;
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
      }
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopiado(true);
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => setCopiado(false), 2000);
    } catch {
      /* sin acción si el clipboard no está disponible */
    }
  }

  return (
    <button
      type="button"
      onClick={compartir}
      title={
        copiado
          ? "¡Enlace copiado!"
          : EsCompartible()
            ? "Compartir este perfil"
            : "Copiar enlace del perfil"
      }
      className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-line bg-surface px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:border-accent hover:text-text"
    >
      <IconoCompartir className="h-4 w-4" />
      {copiado ? "¡Copiado!" : "Compartir"}
    </button>
  );
}
