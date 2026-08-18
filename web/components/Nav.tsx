"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { BotonAtras, useBarrasOcultas } from "@/components/NavegacionMovil";

const enlaces = [
  { href: "/", texto: "Actividad" },
  { href: "/artistas", texto: "Directorio" },
  { href: "/eventos", texto: "Eventos" },
  { href: "/stats", texto: "Stats" },
  { href: "/acerca-de", texto: "Acerca de" },
];

export default function Nav() {
  const [abierto, setAbierto] = useState(false);
  const oculto = useBarrasOcultas();
  const pathname = usePathname();

  return (
    <header className={`relative sticky top-0 z-40 border-b border-line bg-bg/90 backdrop-blur transition-transform duration-200 ${oculto ? "-translate-y-full" : "translate-y-0"}`}>
      <BotonAtras />
      <nav className={`mx-auto flex max-w-6xl items-center justify-between px-4 py-3 ${pathname !== "/" ? "pl-14 md:pl-4" : ""}`}>
        <Link href="/" className="flex items-center gap-2 font-bold tracking-tight transition duration-150 active:scale-[0.98]">
          <Image
            src="/icon.svg"
            alt=""
            width={32}
            height={32}
            className="rounded-lg"
            aria-hidden
          />
          <span className="font-brand text-lg">Frontera Grande</span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {enlaces.map((e) => (
            <Link
              key={e.href}
              href={e.href}
              className="rounded-lg px-3 py-2 text-sm text-muted transition duration-150 hover:bg-surface-2 hover:text-text active:scale-95 active:bg-accent-soft"
            >
              {e.texto}
            </Link>
          ))}
        </div>

        <button
          className="grid h-9 w-9 place-items-center rounded-lg border border-line text-lg transition duration-150 active:scale-90 active:bg-accent-soft md:hidden"
          onClick={() => setAbierto((v) => !v)}
          aria-label="Menú"
        >
          {abierto ? "✕" : "☰"}
        </button>
      </nav>

      {abierto && (
        <div className="border-t border-line px-4 py-2 md:hidden">
          {enlaces.map((e) => (
            <Link
              key={e.href}
              href={e.href}
              onClick={() => setAbierto(false)}
              className="block rounded-lg px-3 py-2.5 text-muted transition duration-150 hover:bg-surface-2 hover:text-text active:scale-[0.98] active:bg-accent-soft"
            >
              {e.texto}
            </Link>
          ))}
        </div>
      )}
    </header>
  );
}
