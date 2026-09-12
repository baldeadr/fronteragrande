"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { BotonAtras, useBarrasOcultas } from "@/components/NavegacionMovil";
import IconoVerificado from "@/components/IconoVerificado";
import { buscarArtistas } from "@/lib/api";
import type { ArtistCard } from "@/lib/types";

const enlaces = [
  { href: "/", texto: "Actividad" },
  { href: "/artistas", texto: "Directorio" },
  { href: "/eventos", texto: "Eventos" },
  { href: "/stats", texto: "Stats" },
  { href: "/acerca-de", texto: "Acerca de" },
  { href: "/ayuda-artistas", texto: "Ayuda" },
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

function ResultadoArtista({ artista, alIr }: { artista: ArtistCard; alIr: () => void }) {
  const inicial = artista.nombre ? artista.nombre[0].toUpperCase() : "♪";
  return (
    <li>
      <button
        type="button"
        onClick={alIr}
        className="flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-surface-2"
      >
        {artista.imagen_perfil ? (
          <Image
            src={artista.imagen_perfil}
            alt={`Foto de ${artista.nombre}`}
            width={36}
            height={36}
            className="h-9 w-9 shrink-0 rounded-full object-cover"
            unoptimized
          />
        ) : (
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-accent-soft text-sm font-bold text-accent">
            {inicial}
          </span>
        )}
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-1 truncate text-sm font-medium">
            {artista.nombre}
            {artista.verificado && (
              <IconoVerificado className="h-3.5 w-3.5 shrink-0 text-accent" />
            )}
          </span>
          <span className="block truncate text-xs text-muted">
            {artista.segmento}
            {artista.ciudad ? ` · ${artista.ciudad}` : ""}
          </span>
        </span>
        <span
          className="h-2 w-2 shrink-0 rounded-full"
          style={{ backgroundColor: artista.color_estado }}
          title={`Estado de actividad: ${artista.estado_activo}`}
        />
      </button>
    </li>
  );
}

export default function Nav() {
  const [abierto, setAbierto] = useState(false);
  const [buscando, setBuscando] = useState(false);
  const [q, setQ] = useState("");
  const [resultados, setResultados] = useState<ArtistCard[]>([]);
  const [dropdownAbierto, setDropdownAbierto] = useState(false);
  const contenedorRef = useRef<HTMLDivElement | null>(null);
  const oculto = useBarrasOcultas();
  const pathname = usePathname();
  const router = useRouter();
  const esPerfilArtista = pathname.startsWith("/artistas/");

  useEffect(() => {
    if (dropdownAbierto) {
      function cerrar(e: MouseEvent) {
        if (!contenedorRef.current?.contains(e.target as Node)) {
          setDropdownAbierto(false);
        }
      }
      document.addEventListener("mousedown", cerrar);
      return () => document.removeEventListener("mousedown", cerrar);
    }
  }, [dropdownAbierto]);

  useEffect(() => {
    const texto = q.trim();
    if (!texto || !esPerfilArtista) return;
    const temporizador = window.setTimeout(async () => {
      try {
        const r = await buscarArtistas(texto);
        setResultados(r.slice(0, 8));
        setDropdownAbierto(true);
      } catch {
        setResultados([]);
      }
    }, 250);
    return () => {
      window.clearTimeout(temporizador);
      setResultados([]);
      setDropdownAbierto(false);
    };
  }, [q, esPerfilArtista]);

  function irAlPerfil(slug: string) {
    setQ("");
    setResultados([]);
    setDropdownAbierto(false);
    setBuscando(false);
    router.push(`/artistas/${slug}`);
  }

  function buscar(e: React.FormEvent) {
    e.preventDefault();
    const texto = q.trim();
    if (!texto) return;
    if (resultados.length > 0) {
      irAlPerfil(resultados[0].slug);
      return;
    }
    setBuscando(false);
    router.push(`/artistas?q=${encodeURIComponent(texto)}`);
  }

  const desplegable =
    q.trim() && esPerfilArtista && dropdownAbierto && resultados.length > 0 && (
      <ul className="absolute inset-x-0 top-full z-50 mt-1 max-h-80 overflow-auto rounded-xl border border-line bg-surface p-1 shadow-lg">
        {resultados.map((a) => (
          <ResultadoArtista
            key={a.slug}
            artista={a}
            alIr={() => irAlPerfil(a.slug)}
          />
        ))}
      </ul>
    );

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
          <div ref={contenedorRef} className="relative hidden min-w-0 md:block">
            <form
              onSubmit={buscar}
              role="search"
              className="hidden md:block"
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
            {desplegable}
          </div>
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
        <div ref={contenedorRef} className="relative border-t border-line px-4 py-2 md:hidden">
          <form onSubmit={buscar} role="search">
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
          {desplegable}
        </div>
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