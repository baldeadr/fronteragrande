"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { BotonAtras, useBarrasOcultas } from "@/components/NavegacionMovil";

const enlaces = [
  { href: "/", texto: "Actividad" },
  { href: "/artistas", texto: "Directorio" },
  { href: "/eventos", texto: "Eventos" },
  { href: "/stats", texto: "Stats" },
  { href: "/acerca-de", texto: "Acerca de" },
];

function IconoBuscar({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      aria-hidden="true"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

export default function Nav() {
  const [abierto, setAbierto] = useState(false);
  const [buscando, setBuscando] = useState(false);
  const [q, setQ] = useState("");
  const oculto = useBarrasOcultas();
  const pathname = usePathname();
  const router = useRouter();
  const esPerfilArtista = pathname.startsWith("/artistas/");

  function buscar(e: React.FormEvent) {
    e.preventDefault();
    const texto = q.trim();
    if (!texto) return;
    setBuscando(false);
    router.push(`/artistas?q=${encodeURIComponent(texto)}`);
  }

  return (
    <header className={`relative sticky top-0 z-40 border-b border-line bg-bg/90 backdrop-blur transition-transform duration-200 ${oculto ? "-translate-y-full" : "translate-y-0"}`}>
      <BotonAtras />
      <nav className={`mx-auto flex max-w-6xl items-center justify-between gap-2 px-4 py-3 ${pathname !== "/" ? "pl-14 md:pl-4" : ""}`}>
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

        {esPerfilArtista && (
        <form
          onSubmit={buscar}
          role="search"
          className="hidden min-w-0 md:block"
        >
          <div className="flex items-center gap-2 rounded-lg border border-line bg-surface px-2.5 py-1.5 transition-colors focus-within:border-accent">
            <IconoBuscar className="h-4 w-4 shrink-0 text-muted" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar artistas…"
              aria-label="Buscar artistas"
              className="w-40 bg-transparent text-sm outline-none placeholder:text-muted lg:w-48"
            />
          </div>
        </form>
      )}

        <div className="flex items-center gap-1">
          {esPerfilArtista && (
            <button
              className="grid h-9 w-9 place-items-center rounded-lg border border-line text-muted transition duration-150 active:scale-90 active:bg-accent-soft md:hidden"
              onClick={() => setBuscando((v) => !v)}
              aria-label="Buscar"
              aria-expanded={buscando}
            >
              <IconoBuscar className="h-4 w-4" />
            </button>
          )}
          <button
            className="grid h-9 w-9 place-items-center rounded-lg border border-line text-lg transition duration-150 active:scale-90 active:bg-accent-soft md:hidden"
            onClick={() => setAbierto((v) => !v)}
            aria-label="Menú"
          >
            {abierto ? "✕" : "☰"}
          </button>
        </div>
      </nav>

      {buscando && esPerfilArtista && (
        <form
          onSubmit={buscar}
          role="search"
          className="border-t border-line px-4 py-2 md:hidden"
        >
          <div className="flex items-center gap-2 rounded-lg border border-line bg-surface px-2.5 py-1.5 transition-colors focus-within:border-accent">
            <IconoBuscar className="h-4 w-4 shrink-0 text-muted" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar artistas…"
              aria-label="Buscar artistas"
              autoFocus
              className="w-full bg-transparent text-sm outline-none placeholder:text-muted"
            />
          </div>
        </form>
      )}

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
